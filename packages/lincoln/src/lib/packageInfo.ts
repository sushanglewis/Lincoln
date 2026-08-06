import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

/**
 * Finds the directory containing the running lincoln package's package.json.
 * Returns undefined when no package.json can be located.
 */
export function readLocalPackageRoot(): string | undefined {
  try {
    let dir = path.dirname(fileURLToPath(import.meta.url))
    const root = path.parse(dir).root
    while (dir !== root) {
      const pkgPath = path.join(dir, 'package.json')
      if (fs.existsSync(pkgPath)) {
        const parsed = JSON.parse(fs.readFileSync(pkgPath, 'utf8')) as { name?: string }
        if (parsed.name === '@sushanglewis/lincoln') {
          return dir
        }
      }
      dir = path.dirname(dir)
    }
  } catch {
    // ignore and return undefined
  }
  return undefined
}

/**
 * Reads the version of the running lincoln package from its own package.json.
 * Walks upward from the current module file until it finds the package.json.
 * Returns undefined when the package.json cannot be located or parsed.
 */
export function readLocalPackageVersion(): string | undefined {
  try {
    const root = readLocalPackageRoot()
    if (!root) return undefined
    const parsed = JSON.parse(fs.readFileSync(path.join(root, 'package.json'), 'utf8')) as {
      version?: string
    }
    return typeof parsed.version === 'string' ? parsed.version : undefined
  } catch {
    return undefined
  }
}

/**
 * Resolves the bundled framework payload directory inside the running package.
 */
export function resolvePayloadRoot(): string | undefined {
  const root = readLocalPackageRoot()
  if (!root) return undefined
  const payload = path.join(root, 'framework')
  return fs.existsSync(payload) ? payload : undefined
}
