/**
 * timeUtils.js
 * Centralized healthcare time & date formatting utilities for ORMA AI.
 * Handles UTC ISO strings, user-configured timezones (e.g. Asia/Kolkata, Asia/Calcutta),
 * 12-hour AM/PM formats, and accessible relative timestamps.
 */

/**
 * Normalizes input timestamp into a valid Date object.
 * Appends 'Z' to UTC ISO strings if timezone designator is omitted by backend.
 */
function parseTimestamp(timestamp) {
  if (!timestamp) return new Date();
  if (timestamp instanceof Date) return timestamp;
  if (typeof timestamp === 'number') return new Date(timestamp);
  
  if (typeof timestamp === 'string') {
    let s = timestamp.trim();
    // If ISO string lacks timezone offset/indicator, treat as UTC
    if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/.test(s) && !s.endsWith('Z') && !/[+-]\d{2}:\d{2}$/.test(s)) {
      s = s + 'Z';
    }
    const d = new Date(s);
    return isNaN(d.getTime()) ? new Date() : d;
  }
  return new Date();
}

/**
 * Resolves valid IANA timezone string, falling back to browser default.
 */
function resolveTimezone(tz) {
  if (tz && typeof tz === 'string' && tz.trim() !== '' && tz !== 'UTC') {
    try {
      // Validate timezone name
      Intl.DateTimeFormat(undefined, { timeZone: tz });
      return tz;
    } catch {
      // Fallback
    }
  }
  return Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';
}

/**
 * Formats time in 12-hour format with AM/PM (e.g. "7:29 AM", "12:05 PM").
 */
export function formatLocalTime(timestamp, userTimezone) {
  const date = parseTimestamp(timestamp);
  const tz = resolveTimezone(userTimezone);

  try {
    return new Intl.DateTimeFormat('en-US', {
      timeZone: tz,
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    }).format(date);
  } catch (err) {
    return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });
  }
}

/**
 * Formats date as "Aug 18, 2026" or "Tuesday, August 18".
 */
export function formatLocalDate(timestamp, userTimezone, format = 'short') {
  const date = parseTimestamp(timestamp);
  const tz = resolveTimezone(userTimezone);

  const options = format === 'long'
    ? { timeZone: tz, weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' }
    : { timeZone: tz, month: 'short', day: 'numeric', year: 'numeric' };

  try {
    return new Intl.DateTimeFormat('en-US', options).format(date);
  } catch (err) {
    return date.toLocaleDateString('en-US');
  }
}

/**
 * Formats date and time: "Aug 18, 2026 • 7:29 AM".
 */
export function formatLocalDateTime(timestamp, userTimezone) {
  const dateStr = formatLocalDate(timestamp, userTimezone, 'short');
  const timeStr = formatLocalTime(timestamp, userTimezone);
  return `${dateStr} • ${timeStr}`;
}

/**
 * Formats relative time elapsed: "Just now", "2 min ago", "1 hr ago".
 */
export function formatRelativeTime(timestamp) {
  const date = parseTimestamp(timestamp);
  const now = new Date();
  const diffSec = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (diffSec < 45) {
    return 'Just now';
  }
  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) {
    return `${diffMin} min ago`;
  }
  const diffHour = Math.floor(diffMin / 60);
  if (diffHour < 24) {
    return `${diffHour} hr ago`;
  }
  const diffDay = Math.floor(diffHour / 24);
  if (diffDay < 7) {
    return `${diffDay}d ago`;
  }
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

/**
 * Formats emergency notification timestamp: "2 min ago • 7:29 AM" or "Just now • 7:29 AM".
 */
export function formatEmergencyTimestamp(timestamp, userTimezone) {
  const rel = formatRelativeTime(timestamp);
  const localTime = formatLocalTime(timestamp, userTimezone);
  return `${rel} • ${localTime}`;
}
