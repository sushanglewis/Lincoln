import { describe, it, expect } from 'vitest'
import { createSyncManifest, findFileByPath } from '../../src/lib/manifest.js'

describe('manifest', () => {
  it('creates sorted sync manifest', () => {
    const manifest = createSyncManifest(
      '1.6.0',
      [
        { path: 'b.txt', sha256: '222' },
        { path: 'a.txt', sha256: '111' }
      ],
      ['settings.json']
    )
    expect(manifest.version).toBe('1.6.0')
    expect(manifest.files[0].path).toBe('a.txt')
    expect(manifest.settingsTouched).toEqual(['settings.json'])
  })

  it('finds file by path', () => {
    const manifest = createSyncManifest('1.6.0', [{ path: 'a.txt', sha256: '111' }])
    expect(findFileByPath(manifest, 'a.txt')?.sha256).toBe('111')
    expect(findFileByPath(manifest, 'missing')).toBeUndefined()
  })
})
