"""Score D3: the owner's blind labels against the answer sheet and the saved model runs.

    python pre-planning/soft/d3/score.py [owner-labels.json]

Writes pre-planning/soft/d3/RESULTS.md and prints it. Measures:
- how often two careful human readings agree, five-way and as the one bit the report uses
  ("an instruction to do the matched action", yes or no), with Cohen's kappa;
- each saved model run against the owner, against the answer sheet, and on the lines where
  owner and sheet agree (the consensus set).
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
LABELS = ("do", "not-to", "description", "example-or-quote", "other-sense")


def sheet() -> dict:
    d = json.loads((ROOT / "Fixtures/ANSWERS/06-soft.json").read_text("utf-8"))
    case = next(c for c in d["cases"] if c["root"] == "real-lines")
    return {e["id"]: {"label": e["match"]["label"]["eq"], "file": e["file"], "line": e["line"],
                      "source": e["note"].split(" -- ")[0],
                      "why": e["note"].split(" -- ", 1)[1] if " -- " in e["note"] else ""}
            for e in case["expect"] if e["check"] == "soft.label"}


def kappa(pairs) -> float | None:
    pairs = list(pairs)
    n = len(pairs)
    if not n:
        return None
    po = sum(a == b for a, b in pairs) / n
    ca, cb = collections.Counter(a for a, _ in pairs), collections.Counter(b for _, b in pairs)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return None if pe == 1 else (po - pe) / (1 - pe)


def agree(pairs) -> str:
    pairs = list(pairs)
    if not pairs:
        return "n/a"
    k = kappa(pairs)
    hit = sum(a == b for a, b in pairs)
    return (f"{hit}/{len(pairs)} = {hit / len(pairs):.0%}"
            + (f", kappa {k:.2f}" if k is not None else ""))


def binary(label: str) -> str:
    return "do" if label == "do" else "not"


def models() -> dict:
    out = {}
    for p in sorted((HERE / "model-labels").glob("*.json")):
        d = json.loads(p.read_text("utf-8"))
        out[p.stem] = {(x["file"], x["line"]): x["label"] for x in d["labels"]}
    return out


def main(argv=None) -> int:
    path = Path((argv or sys.argv[1:] or [str(HERE / "owner-labels.json")])[0])
    owner_doc = json.loads(path.read_text("utf-8"))
    owner = {x["id"]: x for x in owner_doc["labels"]}
    sh = sheet()
    both = [i for i in sh if i in owner and owner[i]["label"] in LABELS]
    unsure = [i for i in sh if i in owner and owner[i]["label"] == "unsure"]
    L = [f"# D3 results ({owner_doc.get('date', '')})", "",
         f"Owner labeled {len(owner)} of {len(sh)} lines ({len(unsure)} unsure). "
         f"Compared on {len(both)}.", "",
         "## Two human readings: owner against the answer sheet", "",
         f"- Five labels: {agree((owner[i]['label'], sh[i]['label']) for i in both)}",
         f"- The one bit the report uses (do / not): "
         f"{agree((binary(owner[i]['label']), binary(sh[i]['label'])) for i in both)}", "",
         "Kappa corrects for chance agreement: above 0.8 is strong, 0.6 to 0.8 substantial, "
         "0.4 to 0.6 moderate, below 0.4 weak.", "",
         "Confusion (rows: owner, columns: sheet):", "",
         "| owner \\ sheet | " + " | ".join(LABELS) + " |",
         "|---|" + "---|" * len(LABELS)]
    conf = collections.Counter((owner[i]["label"], sh[i]["label"]) for i in both)
    for a in LABELS:
        L.append(f"| {a} | " + " | ".join(str(conf[(a, b)]) for b in LABELS) + " |")
    consensus = [i for i in both if owner[i]["label"] == sh[i]["label"]]
    L += ["", f"## Models ({len(consensus)} lines where owner and sheet agree)", "",
          "| run | vs owner (5) | vs owner (do/not) | vs sheet (5) | on consensus (5) | on consensus (do/not) |",
          "|---|---|---|---|---|---|"]
    for name, m in models().items():
        def got(i):
            return m.get((sh[i]["file"], sh[i]["line"]))
        ids = [i for i in both if got(i)]
        cons = [i for i in consensus if got(i)]
        L.append(f"| {name} | {agree((got(i), owner[i]['label']) for i in ids)} | "
                 f"{agree((binary(got(i)), binary(owner[i]['label'])) for i in ids)} | "
                 f"{agree((got(i), sh[i]['label']) for i in ids)} | "
                 f"{agree((got(i), owner[i]['label']) for i in cons)} | "
                 f"{agree((binary(got(i)), binary(owner[i]['label'])) for i in cons)} |")
    dis = [i for i in both if owner[i]["label"] != sh[i]["label"]]
    L += ["", f"## Disagreements ({len(dis)})", "",
          "| id | source | owner | sheet | sheet's reason | owner's note |", "|---|---|---|---|---|---|"]
    for i in sorted(dis, key=lambda x: int(x.rsplit("-", 1)[1])):
        L.append(f"| {i} | {sh[i]['source']} | {owner[i]['label']} | {sh[i]['label']} | "
                 f"{sh[i]['why']} | {owner[i].get('note', '')} |")
    text = "\n".join(L) + "\n"
    (HERE / "RESULTS.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
