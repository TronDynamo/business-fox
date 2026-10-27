#!/usr/bin/env node
'use strict';
// BUSINESS-FOX RELEASE VERIFIER -- a small, standalone, dependency-free script. Read every line of it yourself;
// it uses nothing but Node's built-in crypto/fs/path, on purpose, so there's nothing hidden to trust.
//
// What it checks, and what each check actually proves:
//   1. SIGNATURE (always runs): confirms MANIFEST.json was genuinely signed by the published owner key --
//      i.e. the owner is standing behind this exact list of file hashes. This alone does NOT prove any
//      particular running server is using that code; it proves the manifest itself is authentic, not forged.
//   2. FILES (only with --root): re-hashes a real Business-Fox installation on YOUR machine and compares every
//      file to the signed manifest. This is the full tamper check -- the same one Business-Fox runs on itself
//      every few minutes -- useful if you own a copy and want to confirm your own install hasn't been altered.
//
// Usage:
//   node verify.js                       (signature-only check, using MANIFEST.json + OWNER_PUBLIC_KEY.pem in this folder)
//   node verify.js --root /path/to/BusinessFox   (also re-hashes that installation's files)
//   node verify.js --manifest M.json --key K.pem --root /path/to/BusinessFox   (explicit paths)

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

function arg(name, def) { const i = process.argv.indexOf('--' + name); return i !== -1 && process.argv[i + 1] ? process.argv[i + 1] : def; }
const manifestFile = arg('manifest', path.join(__dirname, 'MANIFEST.json'));
const keyFile = arg('key', path.join(__dirname, 'OWNER_PUBLIC_KEY.pem'));
const root = arg('root', null);

// identical in substance to Business-Fox's own core/src/integrity.js -- kept here as plain, readable code
// rather than imported, so this script never depends on anything but what you can see on this page.
const DEFAULT_COVERED = [
  { dir: 'core/src', ext: /\.js$/ }, { dir: 'config', ext: /\.(txt|md|json)$/ }, { dir: 'config/prompts', ext: /\.md$/ }, { dir: 'config/brand', ext: /\.(png|ttf|json|txt)$/ },
  { file: 'core/package.json' }, { file: 'core/package-lock.json' }, { dir: 'imagegen', ext: /\.(py|txt)$/ }, { file: 'docker-compose.yml' }, { file: 'docker-compose.override.yml' }, { file: 'compose.override.yml' }, { file: 'compose.yaml' }, { dir: 'scripts', ext: /\.js$/ }, { file: 'core/Dockerfile' }, { file: 'imagegen/Dockerfile' },
];
function listFiles(r, covered = DEFAULT_COVERED) {
  const out = [];
  for (const c of covered) {
    if (c.file) { if (fs.existsSync(path.join(r, c.file))) out.push(c.file); continue; }
    const d = path.join(r, c.dir); if (!fs.existsSync(d)) continue;
    for (const f of fs.readdirSync(d).sort()) { const rel = `${c.dir}/${f}`; if (c.ext.test(f) && fs.statSync(path.join(r, rel)).isFile()) out.push(rel); }
  }
  return out;
}
const sha = buf => crypto.createHash('sha256').update(buf).digest('hex');
function hashes(r, covered = DEFAULT_COVERED) { const o = {}; for (const f of listFiles(r, covered)) o[f] = sha(fs.readFileSync(path.join(r, f))); return o; }
function canonical(m) { return JSON.stringify({ version: m.version, created: m.created, files: Object.fromEntries(Object.entries(m.files).sort(([a], [b]) => a < b ? -1 : 1)) }); }

function fail(msg) { console.error('FAIL: ' + msg); process.exit(1); }

if (!fs.existsSync(manifestFile)) fail(`can't find ${manifestFile} -- download it from the verify page first`);
if (!fs.existsSync(keyFile)) fail(`can't find ${keyFile} -- download it from the verify page first`);
let manifest; try { manifest = JSON.parse(fs.readFileSync(manifestFile, 'utf8')); } catch (e) { fail('MANIFEST.json is not valid JSON -- it may be damaged or truncated'); }
const publicPem = fs.readFileSync(keyFile, 'utf8');

console.log(`Checking release ${manifest.version || '(no version)'}, signed ${manifest.created || '(no date)'}...`);

// 1. SIGNATURE
let sigOk = false;
try { sigOk = crypto.verify(null, Buffer.from(canonical(manifest)), crypto.createPublicKey(publicPem), Buffer.from(manifest.signature || '', 'base64')); } catch (e) {}
if (!sigOk) fail('the signature on MANIFEST.json does NOT match the published owner key -- this manifest was not genuinely signed, or has been altered since.');
console.log('PASS: MANIFEST.json is genuinely signed by the published owner key. The owner is standing behind this exact list of file hashes.');

// 2. FILES (optional)
if (!root) {
  console.log('\nNo --root given, so that\'s as far as this can go from the published files alone.');
  console.log('If you own a Business-Fox installation, re-run with --root pointing at it to also verify every file matches this signed manifest.');
  process.exit(0);
}
if (!fs.existsSync(root)) fail(`--root ${root} does not exist`);
const now = hashes(root);
const problems = [];
for (const [f, h] of Object.entries(manifest.files || {})) { if (!(f in now)) problems.push(`missing: ${f}`); else if (now[f] !== h) problems.push(`changed: ${f}`); }
for (const f of Object.keys(now)) if (!(f in (manifest.files || {}))) problems.push(`unexpected new file: ${f}`);
if (problems.length) { console.error(`\nFAIL: this installation does NOT match the signed release (${Object.keys(manifest.files || {}).length} files expected):`); for (const p of problems.slice(0, 20)) console.error('  - ' + p); process.exit(1); }
console.log(`\nPASS: all ${Object.keys(manifest.files).length} files at ${root} match the signed manifest exactly. This installation is verified, independently of anything Business-Fox says about itself.`);
