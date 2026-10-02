# vocab.py: spec

Loads `vocab.yaml`, the one data file holding every stage 4 part 2 word list
(CONTEXT-part2.md): the harness-rubric tiers and confirmation wording, the
endpoint TLDs and registry and local hosts, the conditional words and kinds,
and the term-table shapes and safety vocabulary. Each list cites its source
document in a `source` field.

## Inputs

- `path`: a vocab file; default `vocab.yaml` beside this script.
- `rows`: the loaded pattern table (`patterns.load_table`), to check the tiers.

## Outputs

`load_vocab(path=None, rows=None) -> Vocab`, with compiled regexes
(case-insensitive, like `patterns.yaml`):

- `tiers`: J row id to `prohibited` or `confirm-first`; `ignore_unless_tier`.
- `confirm`: list of compiled confirmation regexes; `neg_before`, `neg_after`,
  `neg_forms`.
- `schemes`, `tlds`, `registry` (set of hosts), `local_names`, `local_suffixes`,
  `local_ipv4_prefix`.
- `cond_words`, `on_kinds`, `in_kinds`, `harness_names`, `kinds`: ordered list
  of `(kind, compiled regex)`.
- `explicit_kw`, `explicit_by`, `mapping`, `glossary_heading`,
  `procedural_heading`, `not_terms` (set), `max_term_words`, `safety`.

Raises `VocabError` when the file cannot be read, a section or list lacks its
`source`, a regex does not compile, a kind is not one of the seven in CONTEXT
table order, a tier is not `prohibited` or `confirm-first`, or (with `rows`) a
`phrase.J.prohibited` row has no tier.

## Must never

- Hold a word list anywhere but `vocab.yaml`.
- Judge anything: the file holds locators only.

## Done when (each backed by a test in `tests/test_vocab.py`)

1. The shipped `vocab.yaml` loads against the shipped `patterns.yaml`: every
   section and list has a `source`, every regex compiles, and every J row has a tier.
2. The kinds are exactly harness, clock, version, state, environment, absence, error, in that order.
3. A J row without a tier, a regex that does not compile, and a list without a source each raise `VocabError`.
4. No regex in the file contains a backspace byte.
