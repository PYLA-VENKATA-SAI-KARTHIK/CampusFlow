/**
 * CampusFlow Error Normalization Utility
 *
 * Normalizes any error (AxiosError, FastAPI/Pydantic validation error lists,
 * RFC 7807 problem details, JavaScript Errors, strings) into a clean,
 * human-readable string suitable for direct React rendering.
 *
 * Guarantees that raw objects/arrays (e.g. {type, loc, msg, input, ctx})
 * are never passed as React children.
 */

export function extractErrorMessage(
  error: unknown,
  fallback: string = 'An unexpected error occurred. Please try again.'
): string {
  if (!error) return fallback;

  if (typeof error === 'string') {
    return error.trim().length > 0 ? error.trim() : fallback;
  }

  if (typeof error === 'object') {
    const err = error as Record<string, any>;

    // 1. Axios HTTP Response error
    if (err.response?.data) {
      const data = err.response.data;

      // Plain string response
      if (typeof data === 'string' && data.trim().length > 0) {
        return data.trim();
      }

      // FastAPI / Pydantic validation error array: { detail: [{ loc, msg, type, input }] }
      if (Array.isArray(data.detail)) {
        const messages = data.detail
          .map((item: any) => {
            if (typeof item === 'string') return item;
            if (item && typeof item === 'object') {
              if (item.msg) {
                const field =
                  Array.isArray(item.loc) && item.loc.length > 0
                    ? item.loc[item.loc.length - 1]
                    : null;
                if (field && field !== 'body' && field !== '__root__') {
                  return `${field}: ${item.msg}`;
                }
                return item.msg;
              }
            }
            return null;
          })
          .filter(Boolean);

        if (messages.length > 0) {
          return messages.join('. ');
        }
      }

      // RFC 7807 / standard detail string: { detail: "..." }
      if (typeof data.detail === 'string' && data.detail.trim().length > 0) {
        return data.detail.trim();
      }

      // RFC 7807 problem details title: { title: "..." }
      if (typeof data.title === 'string' && data.title.trim().length > 0) {
        return data.title.trim();
      }

      // Generic message field: { message: "..." }
      if (typeof data.message === 'string' && data.message.trim().length > 0) {
        return data.message.trim();
      }
    }

    // 2. Network / Offline Axios error
    if (err.isAxiosError && !err.response) {
      return 'Unable to reach the server. Please check that the backend is running and your connection is active.';
    }

    // 3. Standard JS Error
    if (typeof err.message === 'string' && err.message.trim().length > 0) {
      return err.message.trim();
    }
  }

  return fallback;
}
