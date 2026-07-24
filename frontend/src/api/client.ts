export const API_BASE = '/api/v1'

export class ApiError extends Error {
  status: number
  constructor(status: number, detail: string) {
    super(detail)
    this.status = status
  }
}

async function parseError(resp: Response): Promise<never> {
  let detail = `Error ${resp.status}`
  try {
    const body = await resp.json()
    if (typeof body.detail === 'string') detail = body.detail
    else if (Array.isArray(body.detail)) {
      detail = body.detail
        .map((e: { loc?: unknown[]; msg?: string }) => `${(e.loc ?? []).join('.')}: ${e.msg}`)
        .join('; ')
    }
  } catch {
    /* respuesta sin cuerpo JSON */
  }
  throw new ApiError(resp.status, detail)
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(`${API_BASE}${path}`, init)
  if (!resp.ok) await parseError(resp)
  if (resp.status === 204) return undefined as T
  return resp.json()
}

function jsonInit(method: string, body: unknown): RequestInit {
  return {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, body === undefined ? { method: 'POST' } : jsonInit('POST', body)),
  patch: <T>(path: string, body: unknown) => request<T>(path, jsonInit('PATCH', body)),
  delete: (path: string) => request<void>(path, { method: 'DELETE' }),
  upload: <T>(path: string, formData: FormData) =>
    request<T>(path, { method: 'POST', body: formData }),
}
