# Intake

Notes on outside work that Walkdown could take from, written so they can later be turned into
review items, specs, and fixtures. Each note is dated. It cites its source by repository,
commit, file, and line, and says what Walkdown has today. Nothing here is built. A note is
input to a review, not a decision.

| Note | Source | Read at |
|---|---|---|
| [CLOUDFLARE-SECURITY-AUDIT.md](CLOUDFLARE-SECURITY-AUDIT.md) | cloudflare/security-audit-skill (MIT) | `c1c8a8c`, 2026-09-14 |
| [NVIDIA-SKILLSPECTOR.md](NVIDIA-SKILLSPECTOR.md) | NVIDIA/SkillSpector (Apache-2.0) | `efb4e8c`, 2026-10-30 |

## Combined order (2026-10-30)

Both notes merged, ordered by value for effort. When an item is picked up, it becomes a review
item and gets an id in the next REVIEW file.

1. **Claude Code settings shipped in the repository** (SS-1). The largest gap: permission
   modes, `allow` lists, keys that run commands (`statusLine`, `apiKeyHelper`, ...),
   code-running and traffic-redirecting `env`, and MCP auto-enable. Today Walkdown reads only
   the `hooks` key. Stage 1, stage 5 grants.
2. **Pin state for what an install runs** (CF-1, SS-2). Each MCP server, hook command, and
   install line is `exact`, `range`, or `none`. Stage 1 and stage 4, paired in stage 5.
3. **Never honor a suppression shipped in the audited repository** (SS-13). Probably true
   already; write the rule down and add a test. Cheap.
4. **Phrase rows** (SS-5 to SS-8, SS-12): reading other agents' configuration, disclosing the
   context, refusal and warning suppression, steering recommendations, handing work to
   another model, special addresses, container escape, certificate checks off, and registry
   redirects in config files. Each row needs a THREATS or PHRASES source and a base rate on
   the corpus.
5. **Letters spread apart** (SS-4): a fold rule for `i g n o r e`, and the "remove x then run"
   shape as a phrase. Measure the benign count first.
6. **Census flags** (SS-9, SS-11): compiled files with no source; padding that pushes text out
   of view.
7. **Name clashes** (CF-2, SS-3): skills, commands, and MCP servers named like host built-ins
   or like each other. Needs a dated list of built-ins.
8. **The coverage ledger behind stage 7** (CF-3, SS-14), with outside facts named one by one
   (CF-5) and unread reference targets placed beside the line that named them.
9. **Text inside archives** (SS-10), under limits.
10. **Stage 6 hardening** (SS-15): two CLI flags to verify, a random delimiter around audited
    text.
11. **Outside test material** (SS-16, CF-7): SkillSpector's fixtures as known positives
    someone else wrote, and the Cloudflare skill as a calibration audit and a source of
    benign labeled lines.
12. **Measurements, not features**: a repeated sweep (CF-6), SkillSpector beside Walkdown
    (SS-17), carried marks when a skill's grants change (CF-4), and renderer limits (CF-8).

**Owner's calls**, raised in the notes and not settled here:
- an exit code for an incomplete run (SS-14);
- which THREATS class each new phrase row belongs to;
- whether steering recommendations (SS-7) is in scope.

**Licenses.** Cloudflare is MIT. SkillSpector is Apache-2.0, except for its YARA rules
(DRL-1.1) and its confusables table (Unicode license). Copy text or fixtures only with the
notices that `CREDITS.md` and `THIRD-PARTY-NOTICES.md` already follow.
