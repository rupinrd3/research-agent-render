## Workflow Animation Reference

This note aligns the backend research workflow with the frontend animation system so engineers can see which runtime events do (or do not) trigger visible UI updates.

### 1. Expected Stage Flow (A)

| Stage | Backend event(s) | Responsible agent | UI expectation |
| --- | --- | --- | --- |
| Start | `session_start` | Orchestrator | Start node turns active once a session is created. |
| Think | `iteration_start`, `thought` | ReAct agent | Iteration badge increments, Think node pulses until reasoning completes. |
| Operate | `action`, long-running tool call | ReAct agent | Select/Run/Process happens here. The Think→Operate edge should animate during execution; Operate turns purple until the tool finishes. |
| Reflect | `tool_execution`, `observation`, optionally `finish_guard` | ReAct agent | Reflect lights up while results are processed, then decides whether to loop (→Think) or finish (→Evaluator). |
| Evaluate | `evaluator_start`, `evaluator_complete` | Evaluator agent | Evaluator node pulses for the duration of the quality check. |
| Final Report | `finish` (followed by `evaluator_complete`) | Orchestrator | Finish node completes only after evaluator success so durations are non-zero. |

Notes:
- A single iteration can contain multiple `action`→`tool_execution` pairs. Each pair should increment the Operate and Reflect counters once.
- Only `finish_guard` controls whether the loop continues after the auto-finish stage, so there are iterations where the backend jumps straight from `observation` to the next `iteration_start` without an explicit “iterate” event. The UI must still show a Reflect→Think loop for those transitions even though the backend never emits a separate trace.

### 2. Current Implementation Walkthrough (B)

1. **Iteration start** (`workflowStore.ts` lines 425‑517) resets Think/Operate/Reflect/Evaluator to `idle`, activates Think, and only marks the loop arc when `loopingFromEvaluate` is true (i.e., when `finish_guard` rejected).  
2. **Thought** (lines 519‑557) completes Think, activates Operate, and sets the Think→Operate edge active.  
3. **Action** (lines 560‑597) currently just records tool metadata; it no longer advances any edges or deactivates Reflect.  
4. **Tool execution** (lines 582‑640) waits for the tool to finish before completing Operate and activating Reflect. The Operate→Reflect edge only turns active at the end of the tool call, so users rarely see it because the next iteration resets it immediately.  
5. **Observation** (lines 643‑652) stores the observation text but does not visibly change the Reflect node.  
6. **Next iteration** is entered via another `iteration_start`. The reducer wipes the Reflect node before it ever gets a chance to resolve to “Iterate” unless a later `finish_guard` event arrives.  
7. **Loop arc** is only triggered when `finish_guard` returns `approved=false`, so earlier iterations show no visual arc even though the backend logically looped.  
8. **Evaluator & Finish** behave as expected because we emit dedicated `evaluator_start`/`_complete` events before marking Finish completed.

### 3. Comparison & Gaps (C & D)

1. **Operate→Reflect animation invisible:** the gradient edge only animates after `tool_execution` completes, so there is no visual feedback during the long-running tool call.  
   *Fix:* Toggle the Operate→Reflect edge to `active` as soon as `action` fires and keep it active until the matching `tool_execution` event completes.

2. **Reflect instantly resets:** the store resets Reflect to `idle` inside `iteration_start` without ever marking it as `completed`, so the node spends almost no time active (hence the white node and slow counter updates).  
   *Fix:* When we receive a new `iteration_start`, mark the previous Reflect state as `completed` (decision=`iterate`) before re-idling the node so the badge and arc update consistently.

3. **Loop arc only appears after finish guard:** because `loopingFromEvaluate` gates the Reflect→Think edge, users don’t see a dashed loop until the guard rejects.  
   *Fix:* Every iteration beyond the first should briefly activate the Reflect→Think edge so the dashed arc and “Looping” badge increment whenever the backend naturally continues the ReAct loop.

4. **Settings avatar doesn’t open the modal:** the circular avatar is rendered as a static `<div>` (`header.tsx` line 68), so clicking it does nothing.  
   *Fix:* Convert it into a button wired to the same `onSettingsClick` handler as the cog icon so both entry points work.

These issues explain the screenshots in `temp/1.png`‑`4.png`: Operate counts increase while Reflect stays white, the loop arc appears only at iteration 6, and the settings avatar is inert.

The following code changes implement the fixes described above.
