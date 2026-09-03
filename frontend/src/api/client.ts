const API_BASE =
  (
    import.meta.env
      .VITE_API_BASE
    ?? ""
  ).replace(
    /\/$/,
    "",
  );


interface ErrorBody {
  code?: string;
  message?: string;
  detail?: string;
  request_id?: string;
  details?: unknown;
}


export class ApiError
  extends Error {
  readonly status: number;
  readonly code: string;
  readonly requestId: string | null;
  readonly details: unknown;

  constructor(
    message: string,
    options: {
      status: number;
      code?: string;
      requestId?: string | null;
      details?: unknown;
    },
  ) {
    super(message);

    this.name = "ApiError";
    this.status = options.status;
    this.code =
      options.code ??
      `HTTP_${options.status}`;
    this.requestId =
      options.requestId ?? null;
    this.details = options.details;
  }
}


function createRequestId(): string {
  return crypto.randomUUID();
}


async function parseError(
  response: Response,
): Promise<ApiError> {
  const body =
    await response
      .json()
      .catch(
        () => null,
      ) as ErrorBody | null;

  const requestId =
    body?.request_id ??
    response.headers.get(
      "X-Request-ID",
    );

  return new ApiError(
    body?.message ??
      body?.detail ??
      `请求失败（HTTP ${response.status}）`,
    {
      status: response.status,
      code: body?.code,
      requestId,
      details: body?.details,
    },
  );
}


async function request(
  path: string,
  init?: RequestInit,
): Promise<Response> {
  const headers =
    new Headers(init?.headers);

  if (!headers.has(
    "X-Request-ID",
  )) {
    headers.set(
      "X-Request-ID",
      createRequestId(),
    );
  }

  const response =
    await fetch(
      `${API_BASE}${path}`,
      {
        ...init,
        headers,
      },
    );

  if (!response.ok) {
    throw await parseError(
      response,
    );
  }

  return response;
}


export async function apiFetch<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const response =
    await request(path, init);

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}


export async function apiBlob(
  path: string,
  init?: RequestInit,
): Promise<Blob> {
  const response =
    await request(path, init);

  return response.blob();
}


export function formatApiError(
  error: unknown,
  fallback: string,
): string {
  if (error instanceof ApiError) {
    const requestText =
      error.requestId
        ? `（请求 ID：${error.requestId}）`
        : "";

    return `${error.message}${requestText}`;
  }

  if (error instanceof TypeError) {
    return fallback;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return fallback;
}


export {
  API_BASE,
};
