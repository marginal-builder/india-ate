export function joinBase(base: string, path: string): string {
  const normalizedBase = base.endsWith("/") ? base : `${base}/`;
  if (!path || path === "/") {
    return normalizedBase;
  }
  const normalizedPath = path.startsWith("/") ? path.slice(1) : path;
  return `${normalizedBase}${normalizedPath}`;
}

export function withBase(path: string): string {
  return joinBase(import.meta.env.BASE_URL, path);
}
