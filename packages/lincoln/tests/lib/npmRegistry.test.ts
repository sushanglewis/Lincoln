import { describe, it, expect } from 'vitest'
import { createRegistryClient } from '../../src/lib/npmRegistry.js'

function jsonResponse(body: unknown, init?: { status?: number; statusText?: string }): Response {
  return new Response(JSON.stringify(body), {
    status: init?.status ?? 200,
    statusText: init?.statusText ?? 'OK',
    headers: { 'content-type': 'application/json' }
  })
}

describe('createRegistryClient', () => {
  it('returns the latest dist-tag version', async () => {
    const fetchImpl = (async () =>
      jsonResponse({
        name: '@sushanglewis/lincoln',
        'dist-tags': { latest: '1.6.0' },
        versions: { '1.5.0': {}, '1.6.0': {} }
      })) as typeof fetch

    const client = createRegistryClient('https://registry.example.com', fetchImpl)
    expect(await client.latestVersion('@sushanglewis/lincoln')).toBe('1.6.0')
  })

  it('encodes scoped package names in the request URL', async () => {
    let capturedUrl = ''
    const fetchImpl = (async (input: string | URL) => {
      capturedUrl = String(input)
      return jsonResponse({
        'dist-tags': { latest: '1.6.0' },
        versions: { '1.6.0': {} }
      })
    }) as typeof fetch

    const client = createRegistryClient('https://registry.example.com', fetchImpl)
    await client.latestVersion('@sushanglewis/lincoln')
    expect(capturedUrl).toBe('https://registry.example.com/@sushanglewis%2Flincoln')
  })

  it('strips trailing slashes from the registry URL', async () => {
    let capturedUrl = ''
    const fetchImpl = (async (input: string | URL) => {
      capturedUrl = String(input)
      return jsonResponse({
        'dist-tags': { latest: '1.6.0' },
        versions: { '1.6.0': {} }
      })
    }) as typeof fetch

    const client = createRegistryClient('https://registry.example.com/', fetchImpl)
    await client.latestVersion('lincoln')
    expect(capturedUrl).toBe('https://registry.example.com/lincoln')
  })

  it('throws when the registry returns a non-2xx status', async () => {
    const fetchImpl = (async () =>
      jsonResponse({ error: 'Not found' }, { status: 404, statusText: 'Not Found' })) as typeof fetch

    const client = createRegistryClient('https://registry.example.com', fetchImpl)
    await expect(client.latestVersion('@sushanglewis/lincoln')).rejects.toThrow(/404/)
  })

  it('throws when the packument has no latest dist-tag', async () => {
    const fetchImpl = (async () =>
      jsonResponse({
        name: '@sushanglewis/lincoln',
        'dist-tags': {},
        versions: {}
      })) as typeof fetch

    const client = createRegistryClient('https://registry.example.com', fetchImpl)
    await expect(client.latestVersion('@sushanglewis/lincoln')).rejects.toThrow(/latest/)
  })

  it('lists all published versions', async () => {
    const fetchImpl = (async () =>
      jsonResponse({
        'dist-tags': { latest: '1.6.0' },
        versions: { '1.4.0': {}, '1.5.0': {}, '1.6.0': {} }
      })) as typeof fetch

    const client = createRegistryClient('https://registry.example.com', fetchImpl)
    const versions = await client.versions('@sushanglewis/lincoln')
    expect(versions).toEqual(['1.4.0', '1.5.0', '1.6.0'])
  })

  it('resolves a dist-tag to a concrete version', async () => {
    const fetchImpl = (async () =>
      jsonResponse({
        'dist-tags': { latest: '1.6.0', next: '2.0.0-beta.1' },
        versions: { '1.6.0': {}, '2.0.0-beta.1': {} }
      })) as typeof fetch

    const client = createRegistryClient('https://registry.example.com', fetchImpl)
    expect(await client.resolveVersion('@sushanglewis/lincoln', 'next')).toBe('2.0.0-beta.1')
  })

  it('resolves an exact version that exists in the packument', async () => {
    const fetchImpl = (async () =>
      jsonResponse({
        'dist-tags': { latest: '1.6.0' },
        versions: { '1.5.0': {}, '1.6.0': {} }
      })) as typeof fetch

    const client = createRegistryClient('https://registry.example.com', fetchImpl)
    expect(await client.resolveVersion('@sushanglewis/lincoln', '1.5.0')).toBe('1.5.0')
  })

  it('throws when a requested version is not published', async () => {
    const fetchImpl = (async () =>
      jsonResponse({
        'dist-tags': { latest: '1.6.0' },
        versions: { '1.5.0': {}, '1.6.0': {} }
      })) as typeof fetch

    const client = createRegistryClient('https://registry.example.com', fetchImpl)
    await expect(client.resolveVersion('@sushanglewis/lincoln', '99.0.0')).rejects.toThrow(
      /99\.0\.0/
    )
  })
})
