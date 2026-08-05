export function runPostinstall(): number {
  if (process.env.CI || process.env.NODE_ENV === 'test') {
    return 0
  }

  console.log('Lincoln installed globally.')
  console.log('Run "lincoln install" to finish setup.')
  return 0
}

if (import.meta.url === `file://${process.argv[1]}`) {
  process.exit(runPostinstall())
}
