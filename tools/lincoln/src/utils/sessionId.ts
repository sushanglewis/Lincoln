export interface GenerateSessionIdOptions {
  now?: Date
  descriptor?: string
}

export function generateSessionId(options: GenerateSessionIdOptions = {}): string {
  const now = options.now ?? new Date()
  const date = now.toISOString().slice(0, 10)
  const slug = normalizeDescriptor(options.descriptor)
  return `${date}-${slug}`
}

function normalizeDescriptor(descriptor: string | undefined): string {
  if (!descriptor) {
    return 'recording'
  }

  const normalized = descriptor
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9一-龥]+/g, '-')
    .replace(/^-+|-+$/g, '')

  return normalized.slice(0, 80) || 'recording'
}
