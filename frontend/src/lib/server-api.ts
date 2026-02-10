import { cookies } from "next/headers";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

/**
 * Server-side fetch helper. Reads the auth token from cookies and
 * forwards it to the backend API. Used inside server components for
 * TanStack Query prefetching.
 *
 * Silently returns `null` on any error so that client-side useQuery
 * can still pick up the data with the localStorage token.
 */
export async function serverFetch<T = unknown>(
  path: string,
  options?: { params?: Record<string, string> },
): Promise<T | null> {
  try {
    const cookieStore = await cookies();
    const token = cookieStore.get("ta_access_token")?.value;

    if (!token) return null;

    const url = new URL(path, API_BASE_URL);
    if (options?.params) {
      for (const [k, v] of Object.entries(options.params)) {
        url.searchParams.set(k, v);
      }
    }

    const res = await fetch(url.toString(), {
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      // Opt out of Next.js fetch cache — fresh data per request
      cache: "no-store",
    });

    if (!res.ok) return null;

    return (await res.json()) as T;
  } catch {
    return null;
  }
}
