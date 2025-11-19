"""
Realtime Transport Manager

Provides WebSocket + Server-Sent Events broadcasting for live updates.
"""

import logging
import json
from typing import Dict, Set, Any, Optional, List
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
import asyncio

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages real-time connections and broadcasting.

    Features:
    - WebSocket connection pooling per session
    - SSE (Server-Sent Events) subscribers for resilient delivery
    - Broadcast to specific sessions or all connections
    - Automatic cleanup of disconnected clients
    - Message queueing for offline clients
    """

    MAX_OFFLINE_MESSAGES = 200
    SSE_QUEUE_SIZE = 256

    def __init__(self):
        """Initialize connection manager."""
        # Active connections: {session_id: set of WebSocket connections}
        self.active_connections: Dict[str, Set[WebSocket]] = {}

        # Message queues for sessions: {session_id: list of messages}
        self.message_queues: Dict[str, list] = {}

        # SSE subscribers: {session_id: list of asyncio.Queue instances}
        self.sse_subscribers: Dict[str, List[asyncio.Queue]] = {}

        logger.info("WebSocket ConnectionManager initialized")

    async def connect(self, websocket: WebSocket, session_id: str) -> None:
        """
        Accept a new WebSocket connection.

        Args:
            websocket: WebSocket connection
            session_id: Research session ID
        """
        await websocket.accept()

        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()

        self.active_connections[session_id].add(websocket)

        logger.debug(
            "WebSocket connected: session=%s, total_connections=%s",
            session_id,
            self.get_connection_count(session_id),
        )

        # Send queued messages if any
        if session_id in self.message_queues:
            for message in self.message_queues[session_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to send queued message: {e}")

            # Clear queue after sending
            del self.message_queues[session_id]

    def disconnect(self, websocket: WebSocket, session_id: str) -> None:
        """
        Remove a WebSocket connection.

        Args:
            websocket: WebSocket connection
            session_id: Research session ID
        """
        if session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket)

            # Remove session if no more connections
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]

        logger.debug(
            "WebSocket disconnected: session=%s, remaining=%s",
            session_id,
            self.get_connection_count(session_id),
        )

    async def broadcast_to_session(
        self, session_id: str, message: Dict[str, Any]
    ) -> None:
        """
        Broadcast message to all connections for a session.

        Args:
            session_id: Research session ID
            message: Message data to broadcast
        """
        delivered = False

        if session_id in self.active_connections:
            connections = self.active_connections[session_id].copy()
            dead_connections = []

            for connection in connections:
                try:
                    await connection.send_json(message)
                    delivered = True
                except Exception as e:
                    logger.error(f"Failed to send message to WebSocket: {e}")
                    dead_connections.append(connection)

            for connection in dead_connections:
                self.disconnect(connection, session_id)

        if await self._broadcast_to_sse_subscribers(session_id, message):
            delivered = True

        if not delivered:
            queue = self.message_queues.setdefault(session_id, [])
            queue.append(message)
            if len(queue) > self.MAX_OFFLINE_MESSAGES:
                queue.pop(0)
            logger.debug(f"Message queued for session {session_id}")

    async def broadcast_to_all(self, message: Dict[str, Any]) -> None:
        """
        Broadcast message to all active connections.

        Args:
            message: Message data to broadcast
        """
        for session_id in list(self.active_connections.keys()):
            await self.broadcast_to_session(session_id, message)

    def get_connection_count(self, session_id: str) -> int:
        """
        Get number of active connections for a session.

        Args:
            session_id: Research session ID

        Returns:
            Number of active connections
        """
        if session_id not in self.active_connections:
            return 0
        return len(self.active_connections[session_id])

    def get_total_connections(self) -> int:
        """
        Get total number of active connections across all sessions.

        Returns:
            Total connection count
        """
        return sum(
            len(connections)
            for connections in self.active_connections.values()
        )

    def get_active_sessions(self) -> list[str]:
        """
        Get list of sessions with active connections.

        Returns:
            List of session IDs
        """
        return list(self.active_connections.keys())

    def register_sse(self, session_id: str) -> asyncio.Queue:
        """
        Register an SSE subscriber for a session.
        """
        queue: asyncio.Queue = asyncio.Queue(maxsize=self.SSE_QUEUE_SIZE)
        subscribers = self.sse_subscribers.setdefault(session_id, [])
        subscribers.append(queue)

        # Flush queued messages if present
        if session_id in self.message_queues:
            for message in self.message_queues[session_id]:
                try:
                    queue.put_nowait(message)
                except asyncio.QueueFull:
                    break
            del self.message_queues[session_id]

        logger.debug(
            "SSE subscriber added: session=%s, total_sse=%s",
            session_id,
            len(subscribers),
        )

        return queue

    def unregister_sse(self, session_id: str, queue: asyncio.Queue) -> None:
        """
        Remove SSE subscriber from session.
        """
        subscribers = self.sse_subscribers.get(session_id)
        if not subscribers:
            return

        if queue in subscribers:
            subscribers.remove(queue)

        if not subscribers:
            self.sse_subscribers.pop(session_id, None)

        logger.debug(
            "SSE subscriber removed: session=%s, remaining=%s",
            session_id,
            len(self.sse_subscribers.get(session_id, [])),
        )

    async def _broadcast_to_sse_subscribers(
        self, session_id: str, message: Dict[str, Any]
    ) -> bool:
        """
        Broadcast to SSE subscribers; returns True if delivered.
        """
        subscribers = self.sse_subscribers.get(session_id)
        if not subscribers:
            return False

        delivered = False
        stale: List[asyncio.Queue] = []

        for queue in list(subscribers):
            try:
                queue.put_nowait(message)
                delivered = True
            except asyncio.QueueFull:
                logger.warning(
                    "SSE queue full for session %s; dropping oldest event",
                    session_id,
                )
                try:
                    queue.get_nowait()
                    queue.put_nowait(message)
                    delivered = True
                except Exception:
                    stale.append(queue)

        for queue in stale:
            subscribers.remove(queue)

        if not subscribers:
            self.sse_subscribers.pop(session_id, None)

        return delivered

    async def send_trace_event(
        self,
        session_id: str,
        event_type: str,
        data: Dict[str, Any],
    ) -> None:
        """
        Send a trace event to session.

        Args:
            session_id: Research session ID
            event_type: Event type (e.g., 'thought', 'action', 'observation')
            data: Event data
        """
        from datetime import datetime
        import uuid

        message = {
            "id": data.get("id") or str(uuid.uuid4()),
            "type": event_type,
            "session_id": session_id,
            "data": data,
            "message": data.get("message") or event_type,
            "timestamp": data.get("timestamp") or datetime.utcnow().isoformat(),
        }
        if "iteration" in data:
            message["iteration"] = data["iteration"]
        await self.broadcast_to_session(session_id, message)

    async def send_progress_update(
        self,
        session_id: str,
        status: str,
        progress: float,
        message: str = "",
    ) -> None:
        """
        Send a progress update.

        Args:
            session_id: Research session ID
            status: Status ('running', 'completed', 'failed')
            progress: Progress percentage (0-100)
            message: Optional progress message
        """
        from datetime import datetime
        import uuid

        update = {
            "id": str(uuid.uuid4()),
            "type": "progress_update",
            "session_id": session_id,
            "status": status,
            "progress": progress,
            "message": message or f"Status: {status}",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "status": status,
                "progress": progress,
                "message": message or f"Status: {status}",
            },
        }
        await self.broadcast_to_session(session_id, update)

    async def send_error(
        self,
        session_id: str,
        error_message: str,
        error_type: Optional[str] = None,
    ) -> None:
        """
        Send an error notification.

        Args:
            session_id: Research session ID
            error_message: Error message
            error_type: Optional error type
        """
        from datetime import datetime
        import uuid

        error_data = {
            "id": str(uuid.uuid4()),
            "type": "error",
            "session_id": session_id,
            "error_message": error_message,
            "error_type": error_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "error": error_message,
                "error_type": error_type,
            },
        }
        await self.broadcast_to_session(session_id, error_data)

    async def send_completion(
        self,
        session_id: str,
        result: Dict[str, Any],
    ) -> None:
        """
        Send completion notification.

        Args:
            session_id: Research session ID
            result: Research result data
        """
        from datetime import datetime
        import uuid

        completion = {
            "id": str(uuid.uuid4()),
            "type": "completion",
            "session_id": session_id,
            "result": result,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "session": result,
            },
        }
        await self.broadcast_to_session(session_id, completion)

    def cleanup_session(self, session_id: str) -> None:
        """
        Clean up all connections and queues for a session.

        Args:
            session_id: Research session ID
        """
        if session_id in self.active_connections:
            del self.active_connections[session_id]

        if session_id in self.message_queues:
            del self.message_queues[session_id]

        if session_id in self.sse_subscribers:
            del self.sse_subscribers[session_id]

        logger.info(f"Session cleaned up: {session_id}")


# Global connection manager instance
manager = ConnectionManager()


# Create FastAPI router for WebSocket
from fastapi import APIRouter

router = APIRouter(prefix="/ws", tags=["WebSocket"])


@router.websocket("/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time research updates.

    Args:
        websocket: WebSocket connection
        session_id: Research session ID
    """
    await manager.connect(websocket, session_id)

    try:
        # Keep connection alive and handle incoming messages
        while True:
            # Receive message (if any)
            try:
                data = await websocket.receive_text()
                logger.debug(f"Received WebSocket message: {data}")

                # Parse and handle message
                try:
                    message = json.loads(data)
                    message_type = message.get("type")

                    if message_type == "ping":
                        await websocket.send_json({"type": "pong"})

                    elif message_type == "subscribe":
                        # Already subscribed on connection
                        await websocket.send_json({
                            "type": "subscribed",
                            "session_id": session_id,
                        })

                    else:
                        logger.warning(f"Unknown message type: {message_type}")

                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON received: {data}")

            except WebSocketDisconnect:
                break

    except Exception as e:
        logger.error(f"WebSocket error: {e}")

    finally:
        manager.disconnect(websocket, session_id)


@router.get("/{session_id}/stream")
async def sse_endpoint(session_id: str):
    """
    Server-Sent Events endpoint for clients that cannot keep WebSockets alive.
    """
    queue = manager.register_sse(session_id)

    async def event_generator():
        try:
            # Send initial connect event
            yield f"event: connected\ndata: {json.dumps({'session_id': session_id})}\n\n"

            while True:
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=15)
                    yield f"data: {json.dumps(message)}\n\n"
                except asyncio.TimeoutError:
                    # Comment heartbeat keeps connection open without extra parsing
                    yield ": heartbeat\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            manager.unregister_sse(session_id, queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
