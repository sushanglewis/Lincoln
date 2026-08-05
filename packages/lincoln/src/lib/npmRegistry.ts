const DEFAULT_REGISTRY_URL = 'https://registry.npmjs.org'
const FETCH_TIMEOUT_MS = 15_000

export interface NpmDistTags {
  latest?: string
  [tag: string]: string | undefined
}

export interface NpmVersionMetadata {
  version?: string
  dist?: {
    tarball?: string
  }
}

export interface NpmPackument {
  name?: string
  'dist-tags'?: NpmDistTags
  versions?: Record<string, NpmVersionMetadata>
}

export interface RegistryClient {
  latestVersion(packageName: string): Promise<string>
  versions(packageName: string): Promise<string[]>
  resolveVersion(packageName: string, range: string): Promise<string>
}

export function createRegistryClient(
  registryUrl: string = DEFAULT_REGISTRY_URL,
  fetchImpl: typeof fetch = fetch
): RegistryClient {
  const baseUrl = registryUrl.replace(/\/+$/, '')

  async function fetchPackument(packageName: string): Promise<NpmPackument> {
    const url = `${baseUrl}/${encodePackageName(packageName)}`
    const response = await fetchImpl(url, {
      headers: { Accept: 'application/json' },
      signal: AbortSignal.timeout(FETCH_TIMEOUT_MS)
    })
    if (!response.ok) {
      throw new Error(
        `npm registry returned ${response.status} ${response.statusText} for ${packageName}`
      )
    }
    return (await response.json()) as NpmPackument
  }

  return {
    async latestVersion(packageName: string): Promise<string> {
      const packument = await fetchPackument(packageName)
      const latest = packument['dist-tags']?.latest
      if (!latest) {
        throw new Error(`npm registry has no latest dist-tag for ${packageName}`)
      }
      return latest
    },

    async versions(packageName: string): Promise<string[]> {
      const packument = await fetchPackument(packageName)
      return Object.keys(packument.versions ?? {})
    },

    async resolveVersion(packageName: string, range: string): Promise<string> {
      const packument = await fetchPackument(packageName)
      const tagTarget = packument['dist-tags']?.[range]
      if (tagTarget) {
        return tagTarget
      }
      if (packument.versions && range in packument.versions) {
        return range
      }
      throw new Error(`Version not found for ${packageName}: ${range}`)
    }
  }
}

function encodePackageName(packageName: string): string {
  if (packageName.startsWith('@')) {
    const slash = packageName.indexOf('/')
    if (slash === -1) {
      return encodeURIComponent(packageName)
    }
    const scope = packageName.slice(1, slash)
    const name = packageName.slice(slash + 1)
    return `@${encodeURIComponent(scope)}%2F${encodeURIComponent(name)}`
  }
  return encodeURIComponent(packageName)
}
