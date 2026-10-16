# endpoints.py: spec

The endpoint census (CONTEXT-part2 section 2, REPORTING 4.1, THREATS 1): every
network host named anywhere in the scanned text, where it is named, and whether
the documentation names it. Replaces `tools/extract_urls.py` (removed 2026-10-03; in git history) (rebuilt from this
spec, not ported). Text only: no lookup, no DNS, no HTTP.

## Inputs

- A folded line (`hosts_in_line`), or the occurrences of a whole run (`census`).
- `vocab`: `vocab.load_vocab()` (schemes, TLDs, registry and local hosts).

## Rules

`hosts_in_line(folded, vocab) -> list[str]`, distinct, in order of first appearance:

- URLs: `<scheme>://[user@]host[:port]` for a scheme in `vocab.schemes`, and
  `git@host:`. The host is a dotted name, `localhost`, an IPv4 address, or a
  bracketed IPv6 address. A host holding template characters (`$`, `{`, `<`,
  `%`), or a single label other than `localhost` (`http://host:port`), is a
  placeholder and is skipped.
- Bare domains outside any URL: two or more labels ending in a TLD from
  `vocab.tlds`, not preceded by a word character, `.`, `-`, or `/`, and not
  followed by a further label, a word character, or `(` (a method call such as
  `logger.info(` is code, not a host). File names (`script.sh`, `SKILL.md`,
  `summary.json`) never count because those extensions are not in the TLD list.
- Bare `localhost` with a port (`localhost:3000`), and a bare IPv4 address with
  a port, count as hosts.
- Hosts are lowercased; a trailing dot, the port, and a leading `www.` are removed.

`addresses_in_line(folded, vocab) -> list[(host, address)]` (added 2026-10-16, for the report's
outside-links list): the same hosts in the same order, each with the whole text that names it,
from the scheme (or `git@`, `localhost:`, or the bare name) to the end of its path, as written.
Trailing sentence punctuation (`.,;:!?*'"`) and closing brackets with no opening partner (a
Markdown link's `)`) are dropped; `[` and `]` end an address (a Markdown link's `](`). A bare name
or `host:port` runs on only into a path (`/`). A bare address that is the visible text of a full
address for the same host on the same line (`[x.io](https://x.io)`) is not listed again.
`hosts_in_line` is its distinct hosts.

`is_local(host, vocab)`: `localhost`, `::1`, `0.0.0.0`, any `127.x.x.x`, and
names ending `.local` or `.localhost`.

`census(occurrences, vocab) -> list[dict]` where each occurrence is
`(host, file, line, where)` or `(host, file, line, where, address)` and `where` is `instructions`, `docs`, or `code`:
one finding per distinct host, ordered by host:
`{check: "endpoint.host", file: null, line: null, host, documented, local,
kind, where, occurrences}`:

- `occurrences`: every `{file, line, where}`, one per line naming the host,
  ordered by file then line. A row gains `urls`, the distinct addresses named on that line
  in order, when its occurrences carried any (stage 4 always passes them).
- `where`: `{instructions: n, docs: n, code: n}` counting those occurrences.
- `documented`: true when at least one occurrence is `docs`.
- `local`: `is_local`.
- `kind`: `local` when local, `registry` when the host is in `vocab.registry`,
  else `other`. Context only.

`summary(findings) -> dict`: `hosts`, `undocumented`, `local`, and `by_kind`.

## Must never

- Fetch, resolve, or look anything up.
- Read a script or file name as a domain.
- Call a host good, bad, suspicious, or benign.

## Done when (each backed by a test in `tests/test_endpoints.py`)

1. `https://Www.Api.Example.invalid:8443/x` gives `api.example.invalid`; `git@github.com:o/r.git` gives `github.com`.
2. `run scripts/post.sh and read SKILL.md, then summary.json` gives no host; `logger.info("x")` gives no host; `see docs.example.com for more` gives `docs.example.com`.
3. `https://${HOST}/api`, `https://<your-domain>/`, and `http://host:8080/` give no host.
4. `http://localhost:3000`, `127.0.0.1:8080`, and `printer.local` are local with kind `local`; `registry.npmjs.org` has kind `registry`.
5. A host named in docs and in instructions is documented; a host named only in instructions and code is not; a host named only in docs is documented; `where` counts agree with `occurrences`.
6. Two mentions on one line give one occurrence.
7. Addresses are whole and trimmed: a Markdown link's `)` and a full stop are dropped, a
   balanced `(...)` in a path is kept, a `git@` remote and a bare name with a path are whole,
   a placeholder host gives no address; the hosts are those of `hosts_in_line`; a Markdown link
   gives one address, ending at `](`.
8. A census row lists its line's distinct addresses as `urls`; a row given none has no `urls`.
