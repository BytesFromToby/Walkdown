#!/usr/bin/env python3
"""Pass 1 - Normalize. Read each file twice where possible; report divergence.
Static only. Nothing is executed."""
import os, sys, re, unicodedata, json

INVISIBLE = {
    '​':'ZWSP','‌':'ZWNJ','‍':'ZWJ','⁠':'WORD-JOINER',
    '﻿':'BOM','­':'SOFT-HYPHEN','᠎':'MONGOLIAN-VS',
    '⁡':'FN-APP','⁢':'INVIS-TIMES','⁣':'INVIS-SEP','⁤':'INVIS-PLUS',
}
BIDI = {'‪':'LRE','‫':'RLE','‬':'PDF','‭':'LRO','‮':'RLO',
        '⁦':'LRI','⁧':'RLI','⁨':'FSI','⁩':'PDI'}
TAGS = lambda ch: 0xE0000 <= ord(ch) <= 0xE007F
HTML_COMMENT = re.compile(r'<!--(.*?)-->', re.S)
HIDDEN_CSS = re.compile(r'(display\s*:\s*none|visibility\s*:\s*hidden|font-size\s*:\s*0|opacity\s*:\s*0)', re.I)
RICH = {'.pdf','.docx','.xlsx','.pptx','.doc','.xls','.ppt','.rtf','.odt'}
IMG  = {'.png','.jpg','.jpeg','.gif','.webp','.bmp','.svg','.tiff'}
SKIP = {'.git','node_modules','__pycache__','.venv'}

def main(root):
    fmt = {'text':0,'rich':0,'image':0,'other':0}
    rich_files, image_files = [], []
    findings = []
    nonascii = []
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in SKIP]
        for f in fn:
            p = os.path.join(dp,f); rel = os.path.relpath(p,root)
            ext = os.path.splitext(f)[1].lower()
            if ext in RICH:  fmt['rich']+=1;  rich_files.append(rel);  continue
            if ext in IMG:   fmt['image']+=1; image_files.append(rel); continue
            try: raw = open(p, encoding='utf-8').read()
            except Exception: fmt['other']+=1; continue
            fmt['text']+=1
            # invisible / bidi / tag chars
            for i,ch in enumerate(raw):
                if ch in INVISIBLE: findings.append((rel,'INVISIBLE',INVISIBLE[ch],i))
                elif ch in BIDI:    findings.append((rel,'BIDI',BIDI[ch],i))
                elif TAGS(ch):      findings.append((rel,'UNICODE-TAG',hex(ord(ch)),i))
            # html comments
            for m in HTML_COMMENT.finditer(raw):
                body = m.group(1).strip()
                if body:
                    ln = raw[:m.start()].count('\n')+1
                    findings.append((rel,'HTML-COMMENT',body[:120].replace('\n',' '),ln))
            # css hiding
            for m in HIDDEN_CSS.finditer(raw):
                ln = raw[:m.start()].count('\n')+1
                findings.append((rel,'CSS-HIDE',m.group(1),ln))
            # non-ascii census (homoglyph surface)
            odd = {c for c in raw if ord(c)>127 and unicodedata.category(c)[0]=='L'}
            if odd: nonascii.append((rel, ''.join(sorted(odd))[:40]))
    print("## Format census\n")
    for k,v in fmt.items(): print(f"- {k}: {v}")
    print(f"\nRich-format files (need two-path reading): {len(rich_files)}")
    for r in rich_files: print(f"  - {r}")
    print(f"\nImage files (no text layer; model still reads them): {len(image_files)}")
    for r in image_files: print(f"  - {r}")
    print(f"\n## Divergence / hidden-text findings: {len(findings)}\n")
    if not findings: print("None.")
    for rel,kind,detail,loc in findings[:80]:
        print(f"- {kind}  {rel} @ {loc}\n    {detail}")
    print(f"\n## Files containing non-ASCII letters: {len(nonascii)}\n")
    for rel,chars in nonascii[:30]: print(f"- {rel}: {chars}")

main(sys.argv[1])
