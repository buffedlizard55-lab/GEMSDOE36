"""Exercise GitHub freshness rendering without network access."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_source_feed_partial_failure_and_changed_ref_are_not_scores():
    if not shutil.which("node"):
        pytest.skip("node not installed")
    js = r'''
const fs = require('fs');
const vm = require('vm');
const refs = JSON.parse(fs.readFileSync('docs/data/focus-refs.json', 'utf8'));
const elements = {};
for (const id of ['refresh-source-feed','source-feed-status','source-feed-list']) {
  elements[id] = { children: [], textContent: '', disabled: false,
    replaceChildren() { this.children = []; }, append(...x) { this.children.push(...x); },
    addEventListener(type, fn) { this.listener = fn; } };
}
global.document = { getElementById: id => elements[id], createElement: () => ({
  children: [], textContent: '', append(...x) { this.children.push(...x); }
})};
let githubCalls = 0;
global.fetch = async (url) => {
  if (url === 'data/focus-refs.json') return {ok: true, json: async () => refs};
  if (!url.startsWith('https://api.github.com/repos/buffedlizard55-lab/')) throw Error('unexpected network');
  githubCalls++;
  const repo = url.split('/')[5];
  if (repo === 'GEMSDOE27') return {ok: false, status: 403};
  const sha = repo === 'GEMSDOE25' ? 'f'.repeat(40) : refs[repo];
  return {ok: true, json: async () => ({sha, commit: {author: {date: '2026-10-26T12:00:00Z'}}})};
};
vm.runInThisContext(fs.readFileSync('docs/assets/live-feed.js', 'utf8'));
setTimeout(() => {
  const s = elements['source-feed-status'].textContent;
  const list = elements['source-feed-list'].children;
  if (!s.includes('8/9 checked') || !s.includes('1 changed') || !s.includes('do not prove')) throw Error(s);
  if (githubCalls !== 9 || list.length !== 9 || !list[2].textContent.includes('unavailable')) throw Error('partial failure handling');
  if (elements['refresh-source-feed'].disabled) throw Error('refresh remained disabled');
}, 25);
'''
    result = subprocess.run(["node", "-e", js], cwd=ROOT, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr


def test_source_feed_snapshot_failure_is_explicit_and_retry_enabled():
    if not shutil.which("node"):
        pytest.skip("node not installed")
    js = r'''
const fs = require('fs');
const vm = require('vm');
const els = {};
for (const id of ['refresh-source-feed','source-feed-status','source-feed-list']) {
  els[id] = {textContent:'', disabled:false, replaceChildren(){}, addEventListener(){}};
}
global.document = {getElementById: id => els[id], createElement: () => ({})};
let calls = 0;
global.fetch = async () => { calls++; return {ok:false, status:503}; };
vm.runInThisContext(fs.readFileSync('docs/assets/live-feed.js', 'utf8'));
setTimeout(() => {
  if (!els['source-feed-status'].textContent.includes('unavailable') || calls !== 1) throw Error('snapshot failure hidden');
  if (els['refresh-source-feed'].disabled) throw Error('retry disabled');
}, 25);
'''
    result = subprocess.run(["node", "-e", js], cwd=ROOT, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
