import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const appRoot = path.resolve(__dirname, '..')

// Client-side calls that must respect NEXT_PUBLIC_BASE_PATH (see
// src/lib/base-path.ts). Without this, behind admin.gennomx.com/ai,
// fetch('/api/...') and router.push('/route') escape to admin.gennomx.com/...
// instead of admin.gennomx.com/ai/...
const SCAN_DIRS = ['src/components', 'src/app', 'src/lib']

// Explicit exceptions: `relative file path -> allowed lines`.
const ALLOWLIST = new Set()

function walk(dir, files = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (entry.name.startsWith('.')) continue
    const full = path.join(dir, entry.name)
    if (entry.isDirectory()) {
      walk(full, files)
    } else if (/\.(tsx?|jsx?|mjs)$/.test(entry.name) && !entry.name.includes('.test.')) {
      files.push(full)
    }
  }
  return files
}

function lineNumberAt(content, index) {
  return content.slice(0, index).split('\n').length
}

function findViolations(filePath, content) {
  const violations = []
  const callRegex = /\b(fetch|router\.push|router\.replace)\(/g
  let match
  while ((match = callRegex.exec(content))) {
    const afterParen = match.index + match[0].length
    let i = afterParen
    while (content[i] === ' ' || content[i] === '\n' || content[i] === '\t' || content[i] === '\r') i++

    const quoteChar = content[i]
    if (quoteChar !== '`' && quoteChar !== "'" && quoteChar !== '"') continue
    if (content[i + 1] !== '/') continue
    if (content[i + 2] === '/') continue

    const relPath = path.relative(appRoot, filePath).replace(/\\/g, '/')
    const line = lineNumberAt(content, match.index)
    if (ALLOWLIST.has(`${relPath}:${line}`)) continue

    violations.push({
      file: relPath,
      line,
      call: match[1],
      snippet: content.slice(match.index, Math.min(content.length, match.index + 60)).replace(/\n/g, ' '),
    })
  }
  return violations
}

const allViolations = []
for (const dir of SCAN_DIRS) {
  const absDir = path.join(appRoot, dir)
  if (!fs.existsSync(absDir)) continue
  for (const file of walk(absDir)) {
    const content = fs.readFileSync(file, 'utf8')
    if (!content.includes('fetch(') && !content.includes('router.push(') && !content.includes('router.replace(')) continue
    allViolations.push(...findViolations(file, content))
  }
}

if (allViolations.length > 0) {
  console.error(`\nbasePath check failed: ${allViolations.length} client-side call(s) with absolute paths that bypass withBasePath():\n`)
  for (const v of allViolations) {
    console.error(`  ${v.file}:${v.line} — ${v.call}(${v.snippet}...)`)
  }
  console.error('\nUse withBasePath(...) from "@/lib/base-path" for route redirects and relative API paths through apiUrl(...) from "@/lib/api-base".\n')
  process.exit(1)
}

console.log('base path check passed')
