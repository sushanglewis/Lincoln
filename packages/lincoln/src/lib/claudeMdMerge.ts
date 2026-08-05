const BEGIN = '<!-- lincoln:begin -->'
const END = '<!-- lincoln:end -->'

export function mergeManagedBlock(
  existing: string | undefined,
  block: string
): string {
  const wrapped = `${BEGIN}\n${block}\n${END}`
  const text = existing ?? ''

  const beginIndex = text.indexOf(BEGIN)
  const endIndex = text.indexOf(END)

  if (beginIndex !== -1 && endIndex !== -1 && endIndex > beginIndex) {
    return (
      text.slice(0, beginIndex) +
      wrapped +
      text.slice(endIndex + END.length)
    )
  }

  if (text.trim().length === 0) {
    return wrapped
  }

  return `${text.trimEnd()}\n\n${wrapped}\n`
}

export function extractManagedBlock(existing: string): string | undefined {
  const beginIndex = existing.indexOf(BEGIN)
  const endIndex = existing.indexOf(END)
  if (beginIndex === -1 || endIndex === -1 || endIndex <= beginIndex) {
    return undefined
  }
  return existing
    .slice(beginIndex + BEGIN.length, endIndex)
    .replace(/^\n+|\n+$/g, '')
}
