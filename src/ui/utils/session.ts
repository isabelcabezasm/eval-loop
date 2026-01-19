/**
 * Generate a unique session ID using crypto.randomUUID().
 *
 * This function creates a UUID v4 which provides sufficient uniqueness
 * for session identification across multiple concurrent users.
 *
 * @returns A unique session identifier string
 */
export function generateSessionId(): string {
  return crypto.randomUUID();
}
