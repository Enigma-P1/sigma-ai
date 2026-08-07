/** One error shape for every engine call, so UI code has one thing to
 * catch instead of guessing which endpoint throws what. */

export interface PydanticErrorItem {
  type: string;
  loc: (string | number)[];
  msg: string;
  input?: unknown;
}

export class ApiError extends Error {
  status: number;
  /** Parsed 422 detail (array of pydantic errors), when the failure was a
   * schema validation failure. */
  validation?: PydanticErrorItem[];
  /** Raw string detail from a non-validation HTTP error (404 / 403 / 409). */
  detail?: string;

  constructor(message: string, status: number, opts: { validation?: PydanticErrorItem[]; detail?: string } = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.validation = opts.validation;
    this.detail = opts.detail;
  }
}

/** Turn a pydantic error `loc` (e.g. ["body","problem_statement","what"])
 * into a dotted field path, dropping FastAPI's leading "body" segment. */
export function locToPath(loc: (string | number)[]): string {
  const parts = loc[0] === "body" ? loc.slice(1) : loc;
  return parts.join(".");
}

/** Group validation errors by dotted field path for quick Field lookups. */
export function groupValidationByField(items: PydanticErrorItem[]): Record<string, PydanticErrorItem[]> {
  const out: Record<string, PydanticErrorItem[]> = {};
  for (const item of items) {
    const path = locToPath(item.loc);
    (out[path] ??= []).push(item);
  }
  return out;
}
