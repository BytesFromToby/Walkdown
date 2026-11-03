"""Library/README.md lists every Library file; Library/SOURCES.md lists every source the tables cite and
every table cites it by ID or by a section of the two public documents; Library/THREATS.md and
Library/PHRASES.md hold an entry for every class and set a table cites (restructure step 3, L6 to L8,
and step 3b). Written from the step 3 and 3b briefs."""
import re
from pathlib import Path

import yaml

LIB = Path(__file__).resolve().parents[3] / "Library"
ROOT = LIB.parent
DATA = sorted(p.name for p in LIB.iterdir() if p.suffix in (".yaml", ".json"))
DOCS = ["PHRASES.md", "THREATS.md"]
# a link with a real host; "https://..." in an example sentence is not one
URL = re.compile(r"https?://[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+(?:[:/][^\s\"'<>)\],;`]*)?")
HEADING = re.compile(r"^## (\w+)[.:] ", re.M)


def _read(name):
    return (LIB / name).read_text(encoding="utf-8")


def _links_in_tables():
    """Every link in a data file, as written (a made-up address on a reserved name, like the x.invalid
    example in patterns.yaml, is not a source)."""
    found = {}
    for name in DATA:
        for m in URL.finditer(_read(name)):
            link = m.group(0).rstrip(".")
            if re.match(r"https?://[^/]*\.invalid(/|$)", link):
                continue
            found.setdefault(link, []).append(name)
    return found


def _entries():
    """{id: {field: text}} for the S and I entries of SOURCES.md."""
    text = _read("SOURCES.md")
    out = {}
    for block in re.split(r"(?m)^### ", text)[1:]:
        head, _, body = block.partition("\n")
        m = re.match(r"([SI]\d\d) (.+)", head)
        if not m:
            continue
        fields = {}
        for f in re.finditer(r"(?ms)^- ([A-Za-z ]+?): (.*?)(?=^- [A-Za-z ]+?: |\Z)", body):
            fields[f.group(1)] = " ".join(f.group(2).split())
        out[m.group(1)] = {"title": m.group(2), **fields}
    return out


def _sections(doc):
    """{key: section text} for the entries of PHRASES.md (key = the set letter) or THREATS.md (the class
    number, or `trifecta`, lower case)."""
    text = _read(doc)
    out = {}
    for block in re.split(r"(?m)^## ", text)[1:]:
        head, _, body = block.partition("\n")
        m = re.match(r"(\w+)[.:] ", head)
        assert m, f"{doc}: heading {head!r} is not '<key>. title' or '<key>: title'"
        key = m.group(1).upper() if doc == "PHRASES.md" else m.group(1).lower()
        assert key not in out, f"{doc}: {key} twice"
        out[key] = body
    return out


def _rows():
    return yaml.safe_load(_read("patterns.yaml"))["patterns"]


def _refs(source):
    return [r.strip() for r in str(source).split(";") if r.strip()]


def _walk(node, where):
    """(where, reference text) for every `source` string and every value of a `sources` mapping."""
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "source" and isinstance(v, str):
                yield where, v
            elif k == "sources" and isinstance(v, dict):
                for kk, vv in v.items():
                    yield f"{where}.sources.{kk}", vv
            else:
                yield from _walk(v, f"{where}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            name = v.get("id") or v.get("name") if isinstance(v, dict) else None
            yield from _walk(v, f"{where}[{name or i}]")


def _resolves(ref, ids, phrases, threats):
    if re.fullmatch(r"[SI]\d\d", ref):
        return ref in ids
    m = re.fullmatch(r"(PHRASES|THREATS):(\S+)", ref)
    if not m:
        return False
    return m.group(2) in phrases if m.group(1) == "PHRASES" else m.group(2).lower() in threats


# ---------------------------------------------------------------- the index


def test_the_readme_has_one_row_for_every_file_and_no_other():
    rows = re.findall(r"(?m)^\| `([^`]+)` \|", _read("README.md"))
    assert sorted(rows) == sorted(DATA + DOCS)
    assert len(DATA) == 13  # the 11 that moved, invisible.yaml, and capability.yaml


def test_each_readme_row_says_what_it_holds_who_reads_it_and_what_checks_it():
    for line in _read("README.md").splitlines():
        m = re.match(r"\| `([^`]+)` \| (.+) \| (.+) \| (.+) \|$", line)
        if m and m.group(1) in DATA + DOCS:
            assert all(c.strip() for c in m.groups()), m.group(1)


def test_the_readme_states_the_rule():
    text = _read("README.md")
    assert "Data only" in text and "never code" in text.lower()
    assert "dated, with its source" in text
    assert "No table holds a link" in text


# ---------------------------------------------------------------- no link in a table; every source resolves


def test_no_table_holds_a_link():
    assert _links_in_tables() == {}


def test_every_source_in_every_table_resolves_to_an_id_or_a_section():
    ids = set(_entries())
    phrases, threats = set(_sections("PHRASES.md")), set(_sections("THREATS.md"))
    seen, bad = 0, []
    for name in DATA:
        if not name.endswith(".yaml"):
            continue
        for where, text in _walk(yaml.safe_load(_read(name)), name):
            refs = _refs(text)
            seen += 1
            if not refs or not all(_resolves(r, ids, phrases, threats) for r in refs):
                bad.append((where, text))
    assert seen > 150, "the walk found too few source fields"
    assert bad == []


def test_a_reason_kept_under_a_source_key_names_no_document_and_no_link():
    """softreads.yaml keeps four reasons under `*_source` keys (the answer cap, the wait before a second
    try, the sweep's flag probability, the sweep's system text for a model that takes text). They are prose with a date or a
    rule. They hold no link, no path, and no ID."""
    seen = []

    def walk(node, where):
        if isinstance(node, dict):
            for k, v in node.items():
                if isinstance(v, str) and k.endswith("_source"):
                    seen.append(where + "." + k)
                    assert not URL.search(v), (where, k)
                    assert not re.search(r"\b(?:pre-planning|stages|Library)/|\.(?:md|py)\b|\b[SI]\d\d\b", v), (where, k)
                else:
                    walk(v, where + "." + k)
    for name in DATA:
        if name.endswith(".yaml"):
            walk(yaml.safe_load(_read(name)), name)
    assert sorted(seen) == ["softreads.yaml.answer_cap_source", "softreads.yaml.retry_wait_source",
                            "softreads.yaml.sweep.flag_p_source", "softreads.yaml.sweep.system_source"]


def test_every_pattern_row_cites_a_set_or_a_class_first():
    ids = set(_entries())
    phrases, threats = set(_sections("PHRASES.md")), set(_sections("THREATS.md"))
    for r in _rows():
        refs = _refs(r["source"])
        assert refs and re.match(r"(PHRASES|THREATS):", refs[0]), r["id"]
        assert all(_resolves(x, ids, phrases, threats) for x in refs), r["id"]


def test_the_tables_that_must_cite_do_cite():
    """A source field cannot be dropped to make the check above pass: these hold one by design."""
    for name, expect in {"loading.yaml": 4, "hosts.yaml": 7, "trigger.yaml": 5, "fit.yaml": 3, "clean.yaml": 2,
                         "capability.yaml": 1, "invisible.yaml": 11, "softreads.yaml": 8, "vocab.yaml": 8,
                         "patterns.yaml": 125}.items():
        got = list(_walk(yaml.safe_load(_read(name)), name))
        assert len(got) >= expect, (name, len(got), expect)


# ---------------------------------------------------------------- SOURCES.md


def test_sources_ids_run_in_order_with_no_gap():
    ids = list(_entries())
    s = [i for i in ids if i.startswith("S")]
    i_ = [i for i in ids if i.startswith("I")]
    assert s == [f"S{n:02d}" for n in range(1, len(s) + 1)]
    assert i_ == [f"I{n:02d}" for n in range(1, len(i_) + 1)]
    assert len(s) == 20  # 19 links, and RFC 2606 (S18), named in vocab.yaml without one


def test_each_outside_source_has_a_title_a_link_a_date_what_was_taken_and_where_cited():
    for i, e in _entries().items():
        if not i.startswith("S"):
            continue
        assert e["title"].strip(), i
        assert re.search(r"https?://\S+", e.get("Link", "")), i
        assert e.get("Last checked", "").strip(), i
        assert e.get("Taken", "").strip(), i
        assert e.get("Cited in", "").strip(), i


def test_each_outside_source_is_cited_in_the_files_it_names_by_its_id():
    for i, e in _entries().items():
        if not i.startswith("S"):
            continue
        cited = re.findall(r"`([a-z]+\.(?:yaml|json))`", e["Cited in"])
        assert cited, i
        for name in cited:
            assert (LIB / name).is_file(), (i, name)
            assert re.search(rf"\b{i}\b", _read(name)), (i, name)


def test_the_two_public_documents_are_public_entries():
    entries = _entries()
    assert entries["I01"]["title"].startswith("PHRASES") and entries["I02"]["title"].startswith("THREATS")
    for i, doc in (("I01", "Library/PHRASES.md"), ("I02", "Library/THREATS.md")):
        assert f"`{doc}`" in entries[i]["Where"] and "public" in entries[i]["Where"], i
        assert "in the repository" in entries[i]["Where"], i
        assert (ROOT / doc).is_file(), i
        assert "not published" not in entries[i]["Where"], i


def test_each_other_document_says_where_it_lives_and_the_words_match_the_path():
    """A stage file (and anything else that ships) is "in the repository (path)" and must exist; a
    file under pre-planning/ or a removed tool is "not published (path)" (the release removes
    pre-planning/ and cases/, so a published copy cannot be asked to hold those files)."""
    entries = _entries()
    others = [i for i in entries if i.startswith("I") and i not in ("I01", "I02")]
    assert others, "no other documents listed"
    shipped_roots = ("stages/", "Library/")
    for i in others:
        e = entries[i]
        where = e["Where"]
        assert e.get("What it holds", "").strip() and e.get("Cited in", "").strip(), i
        assert "internal" not in where, (i, "stage files ship; say in the repository or not published")
        paths = [(m.start(), m.group(1)) for m in re.finditer(r"`([^`]+\.(?:md|py))`", where)]
        assert paths, i
        for pos, path in paths:
            marker = "in the repository" if path.startswith(shipped_roots) else "not published"
            assert marker in where[max(0, pos - 30):pos], (i, path, marker)
            if marker == "in the repository":
                assert (ROOT / path).is_file(), (i, path)
        if len({p.startswith(shipped_roots) for _, p in paths}) == 2:
            assert "partly both" in where, i  # one entry with a part of each says so


def test_each_internal_document_is_cited_where_it_says():
    entries = _entries()
    for i, e in entries.items():
        if not i.startswith("I") or i in ("I01", "I02"):
            continue
        for name in re.findall(r"`([a-z]+\.(?:yaml|json))`", e["Cited in"]):
            assert re.search(rf"\b{i}\b", _read(name)), (i, name)


def test_sources_says_how_a_table_cites_and_that_no_table_holds_a_link():
    text = _read("SOURCES.md")
    assert "No table holds a raw link" in text
    assert "PHRASES:<set>" in text and "THREATS:<class>" in text


# ---------------------------------------------------------------- the public documents


def test_every_class_and_set_a_table_cites_has_an_entry_and_no_entry_is_uncited():
    ids = set(_entries())
    cited = {"PHRASES": set(), "THREATS": set()}
    for name in DATA:
        if not name.endswith(".yaml"):
            continue
        for _, text in _walk(yaml.safe_load(_read(name)), name):
            for ref in _refs(text):
                m = re.fullmatch(r"(PHRASES|THREATS):(\S+)", ref)
                if m:
                    cited[m.group(1)].add(m.group(2) if m.group(1) == "PHRASES" else m.group(2).lower())
    assert cited["PHRASES"] == set(_sections("PHRASES.md"))
    assert cited["THREATS"] == set(_sections("THREATS.md"))
    assert ids  # the IDs file parsed


def test_each_entry_says_what_it_is_why_it_matters_and_what_walkdown_looks_for():
    for doc in DOCS:
        for key, body in _sections(doc).items():
            for label in ("What it is.", "Why it matters.", "What Walkdown looks for."):
                assert f"**{label}**" in body, (doc, key, label)


def test_each_entry_names_exactly_the_pattern_rows_that_cite_it():
    citing = {}
    for r in _rows():
        for ref in _refs(r["source"]):
            citing.setdefault(ref, set()).add(r["id"])
    ids = {r["id"] for r in _rows()}
    for doc, prefix in (("PHRASES.md", "PHRASES"), ("THREATS.md", "THREATS")):
        for key, body in _sections(doc).items():
            m = re.search(r"\*\*Patterns:\*\*(.*?)(?:\n\s*\n|\Z)", body, re.S)
            want = citing.get(f"{prefix}:{key}", set())
            if m is None:
                assert not want, (doc, key, "rows cite this entry but it names none", sorted(want))
                continue
            named = set(re.findall(r"`([^`]+)`", m.group(1)))
            assert named <= ids, (doc, key, sorted(named - ids))
            assert named == want, (doc, key, sorted(named ^ want))


def test_the_public_documents_hold_no_em_dash_and_no_link():
    for doc in DOCS + ["README.md", "SOURCES.md"]:
        text = _read(doc)
        assert "—" not in text, doc
    for doc in DOCS:
        assert not URL.search(_read(doc)), doc
