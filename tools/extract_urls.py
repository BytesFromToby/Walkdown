#!/usr/bin/env python3
"""Walkdown: pull every outbound reference from a skill repo.

Static only. Reads text, never executes anything. Points outside the repo are
what matter -- a URL in a SKILL.md is an instruction the model may act on.

Usage: python3 extract_urls.py <path-to-repo>
"""
import os, re, sys, collections

URL_RE = re.compile(r'(?:https?://|ftp://|git@)[^\s<>"\')\]}`,;]+', re.I)
# NOTE: deliberately excludes .sh/.ts/.py-style TLD collisions -- the first
# run of this matched 30+ shell script filenames as "domains". Known-clean repo
# as noise calibration.
BARE_RE = re.compile(r'(?<![\w/.-])(?:[a-z0-9-]+\.)+(?:com|net|org|io|dev|ai|me|app|xyz|ru|cn|tk|gg|info|biz)\b(?:/[^\s<>"\')\]}`,;]*)?', re.I)
SCRIPT_EXT = re.compile(r'\.(sh|ts|py|js|md|cjs|mjs|json|yml|yaml|txt|cmd|log|lock|toml|ini|cfg)$', re.I)
SKIP_DIRS = {'.git', 'node_modules', '__pycache__', '.venv'}
BIN_EXT = {'.png', '.jpg', '.jpeg', '.gif', '.zip', '.pdf', '.ico', '.woff', '.woff2'}

def host(u):
    h = re.sub(r'^(https?://|ftp://|git@)', '', u, flags=re.I)
    return h.split('/')[0].split(':')[0].lower().rstrip('.')

def main(root):
    hits = collections.defaultdict(list)   # host -> [(relpath, lineno, url)]
    scanned = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if os.path.splitext(fn)[1].lower() in BIN_EXT:
                continue
            p = os.path.join(dirpath, fn)
            rel = os.path.relpath(p, root)
            try:
                with open(p, 'r', encoding='utf-8', errors='replace') as fh:
                    lines = fh.readlines()
            except Exception:
                continue
            scanned += 1
            for i, line in enumerate(lines, 1):
                for m in URL_RE.finditer(line):
                    hits[host(m.group(0))].append((rel, i, m.group(0)))
                for m in BARE_RE.finditer(line):
                    if '://' in line[max(0, m.start()-8):m.start()]:
                        continue
                    if SCRIPT_EXT.search(m.group(0).split('/')[0]):
                        continue
                    hits[host(m.group(0))].append((rel, i, m.group(0)))

    print(f"scanned {scanned} text files under {root}\n")
    print(f"{'COUNT':>6}  {'HOST':<40}  IN SKILL.md?")
    print("-" * 72)
    for h, occ in sorted(hits.items(), key=lambda kv: -len(kv[1])):
        in_skill = any('SKILL.md' in r for r, _, _ in occ)
        print(f"{len(occ):>6}  {h:<40}  {'YES' if in_skill else ''}")

    print("\n\n=== REFERENCES APPEARING INSIDE SKILL.md FILES ===")
    print("(these are instructions a model may act on, not just docs)\n")
    for h, occ in sorted(hits.items()):
        sk = [(r, i, u) for r, i, u in occ if 'SKILL.md' in r]
        if sk:
            for r, i, u in sk:
                print(f"  {r}:{i}\n    {u}")

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '.')
