const API_BASE =
  import.meta.env.VITE_API_BASE ??
  "http://127.0.0.1:8000";


export async function apiFetch<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const response =
    await fetch(
      `${API_BASE}${path}`,
      init,
    );

  if (!response.ok) {
    const body =
      await response
        .json()
        .catch(
          () => null,
        );

    throw new Error(
      body?.detail ??
        `HTTP ${response.status}`,
    );
  }

  if (
    response.status === 204
  ) {
    return undefined as T;
  }

  return response.json();
}


export {
  API_BASE,
};