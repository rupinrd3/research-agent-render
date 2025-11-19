/**
 * Utility functions for the Agentic Research Lab frontend.
 * Includes className utilities, formatting helpers, and common functions.
 */

import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Combines multiple className values and merges Tailwind CSS classes intelligently.
 * Prevents conflicts between Tailwind classes (e.g., 'px-2 px-4' becomes 'px-4')
 *
 * @param inputs - Class values to combine
 * @returns Combined and merged className string
 *
 * @example
 * cn('px-2 py-1', 'px-4') // => 'px-4 py-1'
 * cn('text-red-500', condition && 'text-blue-500') // => conditional classes
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Formats a duration in seconds to a human-readable string
 *
 * @param seconds - Duration in seconds
 * @returns Formatted duration string
 *
 * @example
 * formatDuration(65) // => "1m 5s"
 * formatDuration(3665) // => "1h 1m 5s"
 */
export function formatDuration(seconds: number): string {
  if (seconds < 60) {
    return `${Math.round(seconds)}s`;
  } else if (seconds < 3600) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.round(seconds % 60);
    return secs > 0 ? `${mins}m ${secs}s` : `${mins}m`;
  } else {
    const hours = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = Math.round(seconds % 60);
    if (mins === 0 && secs === 0) return `${hours}h`;
    if (secs === 0) return `${hours}h ${mins}m`;
    return `${hours}h ${mins}m ${secs}s`;
  }
}

/**
 * Formats a timestamp relative to the current time
 *
 * @param timestamp - Date object or ISO string
 * @returns Relative time string
 *
 * @example
 * formatTimeAgo(new Date(Date.now() - 5000)) // => "5 seconds ago"
 * formatTimeAgo(new Date(Date.now() - 90000)) // => "2 minutes ago"
 */
export function formatTimeAgo(timestamp: Date | string): string {
  const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp;
  const seconds = Math.max(0, Math.floor((Date.now() - date.getTime()) / 1000));

  if (seconds < 5) return 'just now';
  if (seconds < 60) return `${seconds} seconds ago`;

  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return minutes === 1 ? '1 minute ago' : `${minutes} minutes ago`;

  const hours = Math.floor(minutes / 60);
  if (hours < 24) return hours === 1 ? '1 hour ago' : `${hours} hours ago`;

  const days = Math.floor(hours / 24);
  if (days < 30) return days === 1 ? '1 day ago' : `${days} days ago`;

  const months = Math.floor(days / 30);
  if (months < 12) return months === 1 ? '1 month ago' : `${months} months ago`;

  const years = Math.floor(months / 12);
  return years === 1 ? '1 year ago' : `${years} years ago`;
}

/**
 * Formats a cost in USD to a readable string
 *
 * @param cost - Cost in USD
 * @returns Formatted cost string
 *
 * @example
 * formatCost(0.002) // => "$0.002"
 * formatCost(1.5) // => "$1.50"
 */
export function formatCost(cost: number): string {
  if (cost < 0.001) {
    return `$${cost.toFixed(4)}`;
  } else if (cost < 1) {
    return `$${cost.toFixed(3)}`;
  } else {
    return `$${cost.toFixed(2)}`;
  }
}

/**
 * Truncates text to a maximum length and adds ellipsis
 *
 * @param text - Text to truncate
 * @param maxLength - Maximum length
 * @returns Truncated text
 *
 * @example
 * truncate("This is a long text", 10) // => "This is a..."
 */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
}

/**
 * Copies text to the clipboard
 *
 * @param text - Text to copy
 * @returns Promise that resolves when copy is complete
 *
 * @example
 * await copyToClipboard("Hello World")
 */
export async function copyToClipboard(text: string): Promise<void> {
  if (navigator.clipboard && window.isSecureContext) {
    await navigator.clipboard.writeText(text);
  } else {
    // Fallback for older browsers
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    try {
      document.execCommand('copy');
    } finally {
      textArea.remove();
    }
  }
}

/**
 * Downloads content as a file
 *
 * @param content - File content
 * @param filename - Name of the file
 * @param mimeType - MIME type of the file
 *
 * @example
 * downloadFile("Hello World", "hello.txt", "text/plain")
 */
export function downloadFile(
  content: string | Blob,
  filename: string,
  mimeType: string = 'text/plain'
): void {
  const blob = typeof content === 'string'
    ? new Blob([content], { type: mimeType })
    : content;

  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Formats a number with commas as thousand separators
 *
 * @param num - Number to format
 * @returns Formatted number string
 *
 * @example
 * formatNumber(1234567) // => "1,234,567"
 */
export function formatNumber(num: number): string {
  return num.toLocaleString('en-US');
}

/**
 * Generates a unique ID
 *
 * @returns Unique ID string
 *
 * @example
 * generateId() // => "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
 */
export function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Delays execution for a specified number of milliseconds
 *
 * @param ms - Milliseconds to delay
 * @returns Promise that resolves after the delay
 *
 * @example
 * await delay(1000) // Wait for 1 second
 */
export function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Safely parses JSON, returns default value on error
 *
 * @param json - JSON string to parse
 * @param defaultValue - Default value to return on error
 * @returns Parsed object or default value
 *
 * @example
 * safeJsonParse('{"key": "value"}', {}) // => {key: "value"}
 * safeJsonParse('invalid', {}) // => {}
 */
export function safeJsonParse<T>(json: string, defaultValue: T): T {
  try {
    return JSON.parse(json);
  } catch {
    return defaultValue;
  }
}

/**
 * Gets a score label based on the score value
 *
 * @param score - Score value (0-10)
 * @returns Score label
 *
 * @example
 * getScoreLabel(9.5) // => "Excellent"
 * getScoreLabel(5.0) // => "Fair"
 */
export function getScoreLabel(score: number): string {
  if (score >= 9) return 'Excellent';
  if (score >= 8) return 'Very Good';
  if (score >= 7) return 'Good';
  if (score >= 6) return 'Fair';
  if (score >= 5) return 'Average';
  return 'Poor';
}

/**
 * Gets a color class based on the score value
 *
 * @param score - Score value (0-10)
 * @returns Tailwind color class
 *
 * @example
 * getScoreColor(9.5) // => "text-green-400"
 * getScoreColor(5.0) // => "text-yellow-400"
 */
export function getScoreColor(score: number): string {
  if (score >= 8) return 'text-green-400';
  if (score >= 6) return 'text-blue-400';
  if (score >= 4) return 'text-yellow-400';
  return 'text-red-400';
}

/**
 * Calculates progress percentage
 *
 * @param current - Current value
 * @param total - Total value
 * @returns Progress percentage (0-100)
 *
 * @example
 * calculateProgress(3, 10) // => 30
 */
export function calculateProgress(current: number, total: number): number {
  if (total === 0) return 0;
  return Math.min(Math.round((current / total) * 100), 100);
}

/**
 * Debounces a function call
 *
 * @param func - Function to debounce
 * @param wait - Wait time in milliseconds
 * @returns Debounced function
 *
 * @example
 * const debouncedSearch = debounce(search, 300)
 * debouncedSearch("query") // Only calls search after 300ms of no more calls
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout;

  return function executedFunction(...args: Parameters<T>) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };

    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

/**
 * Validates if a string is a valid URL
 *
 * @param url - URL string to validate
 * @returns True if valid URL
 *
 * @example
 * isValidUrl("https://example.com") // => true
 * isValidUrl("not a url") // => false
 */
export function isValidUrl(url: string): boolean {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}
