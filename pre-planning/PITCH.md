# Walkdown: spoken pitch

> **Walkdown, a pre-flight check for AI skills.**

The tagline. Use it wherever the name appears alone (README, repo description,
the first line spoken). "Pre-flight check" is the descriptor, never the name:
it explains the tool instantly because the phrase is common, and it is common
enough that several AI-agent scanners already use it as theirs (checked
2026-09-25).

**Audience: builders.** People who write skills, agents, plugins, and CLAUDE.md
files (CUSTOMERS.md, builder as primary customer since 2026-09-24). Rewritten
2026-09-25 around what the tool concretely finds. The earlier version spoke to
someone deciding whether to install a skill; that reader is served by the same
report but is no longer who the pitch is for.

## One line

Three versions, best first. Pick by context.

**Primary**

> Walkdown is a pre-flight check for AI skills. It finds the hidden characters,
> dead links, orphan files, and risky instructions a marketplace scanner would
> flag, and shows you exactly where each one is.

**Findings first** (when the listener already knows what a skill is)

> Walkdown checks your skill repo for hidden characters, dead links, orphan
> files, remote fetches, and broad tool grants, then shows you what each one asks
> the model to do and what it grants.

**Core idea first** (when the listener cares about the method)

> Walkdown shows skill builders what their instructions ask a model to do and
> what installing them grants. It finds hidden characters, dead links, orphan
> files, and anything a marketplace scanner would flag.

## 15 seconds

Walkdown is a pre-flight check for AI skills. Before you ship, it walks your repo
and finds the hidden characters, dead links, orphan files, remote fetches, and
broad tool grants a marketplace scanner would flag. Every finding comes with the
file, the line, and the quote.

## 45 seconds

You build skills for AI assistants. A markdown file, plain English. When someone
installs it, it loads into the model and runs with their permissions.

Marketplaces now scan skills before listing them. The scanners hand back a score
and a label, and a lot of what they flag is the skill doing its stated job. You
get told a line is risky without being told what it does.

Walkdown is a pre-flight check you run first. It finds invisible characters the
model reads and you don't see. Links to files that don't exist, and files
nothing links to. Instructions to fetch more instructions from somewhere else.
Agents granted more tools than their job needs. Each finding comes with the file,
the line, the quote, and how common that pattern is in clean repos. It gives no
score. You know what the skill is for, so the call stays with you.

The first run was on a popular, well-built repo. Its install doc said "fetch and
follow instructions from this URL." Written in good faith, and still a line
nobody can review, because the instructions live somewhere else. That's the kind
of thing you want to find before a scanner does.

---

## Likely follow-ups

- **"How is this different from SkillSpector?"** SkillSpector answers the
  installer's question: install or don't. Walkdown answers the builder's
  question: what does each line do, and what would a narrower version look like.
  Run both, and Walkdown explains the other tool's flags.
- **"Does it catch malware?"** It reports capability and hidden or unusual
  text, with evidence. Whether a capability is a problem depends on what the
  skill is for, and the builder is the one who knows that.
- **"Does my skill leave my machine?"** The deterministic checks run locally.
  If you add a model for the soft reads, you choose which one.

## Delivery note

Lead with their situation (they built something, a scanner stands between it and
users), name two or three concrete findings, land on the one example, and stop.
Let them ask the next question.

The findings list is the part that lands: people picture their own repo when
they hear "hidden characters" or "files nothing links to." Keep it concrete. The
word "vulnerabilities" stays out; it is the verdict the tool does not give, and
"what a scanner would flag" says the same thing in the builder's terms.
