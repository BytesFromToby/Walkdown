# Threats

The threat classes Walkdown looks for, in its own words.

A class is a way that text in an AI skill repository can steer a model, or the person who installs
it. The text is English, not code, so ordinary security tools do not read it, and it runs with the
user's own permissions. The classes are the reasons Walkdown looks at a phrase, a file, or a setting.

**How to read this file.**

- The numbers are stable tags. They appear on findings, and the Library's tables cite them as
  `THREATS:<class>`, so a number never changes meaning. A class that is not listed here is one no
  table cites yet.
- Walkdown reports what a repository can do and where it says so, never why. Every pattern named
  below is a locator for a person to read. A hit is not a verdict, and the benign hits are counted
  and shown, because they are part of the result.
- Pattern ids are rows of `patterns.yaml`. The wording sets they are grouped in are in
  `PHRASES.md`; each row's own `plain` field says in plain words what it looks for.
- Each entry ends with the pattern rows that cite it. A class can also be looked for by other
  stages (the invisible-character list, the capability map), and the entry says so.

## Trifecta: the three legs

**What it is.** A frame for the combination that makes an agent dangerous. It can read the user's
data, it takes in text the user did not write, and it can send data out. The frame is Simon
Willison's (see `CREDITS.md`); the plain names are Walkdown's: Reads your data, Takes outside
input, Sends data out.

**Why it matters.** Any one leg is ordinary. An agent with all three can be steered by outside
text into sending the user's data away.

**What Walkdown looks for.** The capability step (`02.5-capability`) maps what a repository can do
onto the three legs, from the tools an agent asks for, the hooks and servers it declares, and the
phrase hits (`02.4-phrases`). It counts where a
text comes from, not who wrote it, because a static read cannot see authorship. Two pattern rows
exist for the legs themselves: `E.connector` (connecting an account puts the user's own data in
reach) and `E.clone` (cloning or installing someone else's code brings outside input onto the
machine). The rules that decide each leg are in `capability.yaml`.

**Patterns:** `E.clone`, `E.connector`

## 1. Exfiltration channels

**What it is.** The ways data can leave the machine: paste and relay services, chat webhooks, web
requests in code, lookups that carry data in a name, and data encoded and sent on. The quieter
forms are a destination named by reference ("the usual endpoint") instead of written out, a host
assembled from pieces, a bug report or pull request template that asks for environment output, and
telemetry sold as optional.

**Why it matters.** This is the leg that turns a read into a leak. Some strings here have almost no
place in a skill (a paste service, a chat webhook); others, such as the web-request verbs, are
common and usually benign, so the report shows how often each one turns up. The quiet forms matter
because there is no address for a search to find.

**What Walkdown looks for.** The relay and webhook hosts, the web-request verbs, a lookup with a
variable built into the name, and an encode step piped into a network command. In prose, a sentence
that joins a private data source, a sending verb, and a destination. A destination kept in a
setting or file rather than written out, a host built from parts, and sending usage data with no
opt-in beside it. The short forms are set K in `PHRASES.md`.

**Patterns:** `K.assembly-prose`, `K.chat-webhook`, `K.data-flow`, `K.dest-stored`, `K.dns`,
`K.encode-send`, `K.http-verb`, `K.prompt-leak`, `K.relay-host`, `K.telemetry-send`

## 2. Credential and secret access

**What it is.** Text or code that reaches for secrets: the places credentials live, the names
secrets go by, bulk reads of the environment, and the user's desktop (the clipboard, the screen,
saved browser sessions, saved logins). It also covers settings that change where credentials flow,
and a list of what the user has installed, which is a map of their setup.

**Why it matters.** A secret read is the first half of a leak. One named variable is normal
configuration; reading all of them is not, and the difference is what Walkdown tries to keep
visible.

**What Walkdown looks for.** Credential paths (SSH keys, cloud and package-manager credential
files, `.env`), upper-case secret-style names, iteration over the whole environment, scanning or
collecting keys and tokens in bulk, reading the clipboard or recording the screen, and
instructions to list installed skills, plugins, servers, or settings files. A git setting that
points the credential helper at a script is in set E.

**Patterns:** `E.git-keys`, `creds.desktop`, `creds.dotenv`, `creds.enumerate`,
`creds.env-enum-code`, `creds.path`, `creds.recon`, `creds.secret-name`

## 3. Remote instruction loading

**What it is.** Instructions that are fetched when the skill runs, so they are not in what was
reviewed: "fetch and follow", "download and run", a pointer to a page for the current process, a
script piped into a shell, a reference that moves (a branch or `latest`, not a fixed version), a
skill that requires another skill from somewhere else. Registering a tool server that starts an
unpinned package is the same thing in another form: remote code loaded at start.

**Why it matters.** The reviewer cannot audit text that is not there. Whoever controls the address
controls the instructions, and can change them after the review.

**What Walkdown looks for.** Fetch-then-act phrasing, raw file hosts, a download piped into a shell
(`curl ... | sh`), moving references, requirements that cross a repository boundary, and the
registration of a server.

**Patterns:** `E.mcp`, `G.pipe-shell`, `RL.branch-ref`, `RL.cross-repo-skill`, `RL.fetch-follow`,
`RL.pipe-shell`, `RL.raw-host`

## 4. Hidden and obfuscated instructions

**What it is.** Text a person cannot see and a model still receives: invisible characters (zero
width and other format characters, direction marks, letters and cells that draw as a blank, runs of
variation selectors that hide bytes after one visible character, the Unicode tag block that spells
ASCII), look-alike letters, comments and
hidden elements in markup, text styled to disappear, encoded blobs in prose, link definitions and
alt text that nothing displays, and instructions in another language or alphabet that a reviewer
skips.

**Why it matters.** The hiding is the point. A search for a phrase misses it, and a reviewer reading
the rendered page never sees it. Matching on the raw bytes of such text is also unreliable, so it
has to be undone first.

**What Walkdown looks for.** One test covers the whole class, including methods not yet invented:
read each file two independent ways and compare. The reader step (`02.2-reader`) reads a file as a person sees it and as a
model receives it, and a difference between them is the finding. Invisible characters are listed
in `invisible.yaml` and removed before text is matched, so a keyword split by one still matches.
A sentence spelled by tag characters, or by a run of variation selectors, is read as the text it
spells. One variation selector after an emoji or a CJK character is ordinary and is not reported;
two or more are, even with zero-width characters between them. Markup that hides text is read for what it holds. No pattern row cites this class directly; the
markdown carriers are in set K.

## 5. Instruction override and persistence

**What it is.** Two related moves. Override tells the model to drop what it was told: ignore the
earlier instructions, skip the check, do not ask. Persistence writes to a file that loads in every
later session, so the change outlives the task.

**Why it matters.** Override removes the user's chance to say no. Persistence turns a one-time
action into a standing instruction. Telling the model to keep something from the user is the worst
form of either.

**What Walkdown looks for.** Permission to skip asking ("no need to ask", "without asking"), text
that tells the model to hide or omit something from the user, and writing to the files that load
later: instruction files, shell profiles, git hooks, editor and agent settings. The loud takeover
phrasings are set L, and the audit-trail forms are set H.

**Patterns:** `E.persist-redirect`, `E.persist-target`, `H.suppress`, `L.never-refuse`,
`L.no-disclaimer`, `L.skip-confirm`

## 7. Execution and privilege

**What it is.** Anything that runs code or widens what the tool may do: command-running
primitives, programs left running after the session, packages installed while it runs, files
written to a temporary folder and then run, and broad or pre-approved tool permissions.

**Why it matters.** Text that causes code to run has the user's full rights. Code that arrives after
the review, or that keeps running when nobody is watching, is the case a reader cannot check.

**What Walkdown looks for.** Execution primitives (`sudo`, `subprocess`, `eval`, and the like),
background services and scheduled jobs, install commands in scripts and hooks, write-then-run in
temporary folders, allow lists and auto-approve lists, and turning off a confirmation. Global and
plugin installs are the shape of this class; plain project installs are set E.

**Patterns:** `E.allowlist`, `E.confirm-off`, `E.decode-exec`, `E.exec-primitive`,
`E.install-global`, `E.outlives-session`, `E.runtime-install`, `E.write-then-exec`

## 8. Supply chain and drift

**What it is.** The ways what runs differs from what was reviewed, or changes afterwards: references
that are not pinned, install scripts, a package fetched from a registry when a script starts, and
variables that send traffic somewhere else (a proxy, a custom registry, a replaced API address).

**Why it matters.** The text can be clean on the day of the review and not the next day. A single
`export` line can redirect every package fetch or the model's own traffic.

**What Walkdown looks for.** Dependencies installed from a registry at run time by a script, hook,
or server launcher. The traffic-redirection variables are in set E, and the moving references are
class 3.

**Patterns:** `E.registry-config`, `E.runtime-install`

## 13. Claimed authorization and fabricated consent

**What it is.** Text that asserts a permission state the model cannot check. Class 5 tells the model
to skip a check; this class tells it the check has already passed: the user has already approved,
per the user's settings, installing counts as consent, one confirmation covers everything after, a
role that carries standing approval, a made-up exchange in which the user says yes, text dressed as
the tool's own messages, and "tell the user, then do it".

**Why it matters.** The user is never asked, and the model has no way to tell the claim from a fact.

**What Walkdown looks for.** The claim forms above. Quoting the tool's own message formats in
documentation is common and legitimate, which is why a hit here is a locator and the benign count is
kept. The full set is A in `PHRASES.md`.

**Patterns:** `A.per-settings`, `A.prior-consent`

## 14. Definitional hijacking and defaults

**What it is.** The instruction that fires is the user's own ordinary request, and the skill has
changed what the words mean or what the blanks contain. A verb is redefined so that "clean up" or
"commit" includes a larger action; a casual phrase is mapped onto an action; a default names a
destination the user never chose; a rule that only applies when something is missing; a safety
exception that carries the payload; a reassuring word ("read-only", "harmless") beside code nobody
has checked.

**Why it matters.** Nothing in the text looks like an instruction. Two definitions of one word in
one repository are worse than either alone, because the reviewer cannot know which one the model
will use; and redefining a safety word ("confirmation", "verified") hollows out every rule built
on it.

**What Walkdown looks for.** The phrase step (`02.4-phrases`) matches the redefinition shapes below and also builds a term
table: every definition it can find, whether two definitions of a word conflict, and whether a
safety word has been redefined. It reports every conflict and never decides which definition is the
real one.

**Patterns:** `B.def-destination`, `B.includes-verb`

## 15. Second-order instruction layers

**What it is.** Text the skill does not run itself but causes to be run somewhere with less review:
the prompts and definitions of subagents, instructions inside code (strings, error messages, printed
output, comments aimed at the assistant), text the model is told to add to what it writes, and
instructions for writing other skills, rules, or hooks. Sending a reviewer or verifier agent to the
weakest model belongs here too.

**Why it matters.** A subagent starts with fresh context, often holds every tool, and the user is not
watching it. A line printed by a script arrives through the tool-result channel, which the model
treats as ground truth. Boilerplate that copies itself spreads the text into the user's other work.

**What Walkdown looks for.** Tool and model grants in frontmatter, fan-out to a subagent per item,
notes addressed to the AI, printed or error-path instructions in scripts, footers the model is told
to add, text that tells a model how to author instruction files, and instructions to a reviewer or
verifier. The full set is C in `PHRASES.md`.

**Patterns:** `C.guard-instruction`, `C.guard-routing`, `C.skills-author`

## 16. Trust elevation paths

**What it is.** Where text acquires more authority than its source deserves. Text read from a file
and emitted by a hook reaches the model as context the tool delivered, which models weight above
file content. A hook that fires when the conversation is compacted puts text back at the moment the
model remembers least of what the user allowed. "Read the current version" instructions plus a
writable plugin folder let the running text differ from the reviewed text. A verification step can
be a command to run.

**Why it matters.** The same words carry more weight depending on the channel they arrive by.

**What Walkdown looks for.** Hooks that inject text, the events and matchers that make them fire,
context-adding fields, all-caps tag wrappers, and a script that hands the model a command to run.
The capability step (`02.5-capability`) records which hook events inject text and how many bytes they add at load. The full set is
D in `PHRASES.md`.

**Patterns:** `C.script-instruction`, `D.authority`, `D.hook-inject`

## 17. Environment mutation

**What it is.** A change whose effect lasts and reaches beyond the task, written in one line:
variables that reroute traffic, git settings that run something on every command, a registered tool
server, an editor setting that runs a task when a folder opens, widened permissions, packages
installed on request, a connected account, and a change to the AI tool's own program.

**Why it matters.** Persistence changes what the model is told next time; this changes where
everything goes, or what runs. The indicator for the whole class is an instruction whose target is
outside the repository, or a variable that another program reads.

**What Walkdown looks for.** Writes to files outside the repository that load in later sessions, and
patching or re-signing the host tool's binary. The rest of the class is set E in `PHRASES.md`.

**Patterns:** `E.harness-binary`, `E.persist-target`, `E.tls-off`

## 19. Human-audience instructions and inbound surface

**What it is.** A repository carries instructions for three audiences: the model, a subagent, and a
person. Install steps that tell a person to lower their defenses (run with permissions skipped, add a
broad allow-list entry, pipe a script into a shell, trust a folder) are text aimed at the reader. The
inbound side is the other direction: issue templates, pull request templates, and contribution
files addressed to the agents of the people who visit.

**Why it matters.** The same file, the same layer, a softer target. A hostile template in a popular
repository instructs every contributor's agent.

**What Walkdown looks for.** Permission-skipping flags and allow-list additions told to a person,
pipe-to-shell install lines, "paste this into your terminal", requests to trust a folder or author,
and templates addressed to an AI. The phrase step (`02.4-phrases`) tags each instruction with its audience (model, subagent,
human, tool), because the same sentence is a different finding under each. The full set is G in
`PHRASES.md`.

**Patterns:** `E.allowlist`, `E.confirm-off`, `G.agent-template`, `G.launch-lowered`,
`G.paste-terminal`, `G.pipe-shell`, `G.trust-grant`

## 20. Anti-review and audit-trail shaping

**What it is.** Text that shapes what gets read, said, or kept, without ever saying "do not mention":
"the scripts are already reviewed", an exact wording the model must announce, a reply limited to a
status, a list that anticipates and dismisses the model's own doubts, a warning that skipping a step
will break things, deleting the record of what happened, calling another check obsolete, a claim of
precedence, and an attestation aimed at the reviewer ("no telemetry", "contains no"). Loops with no
stopping point belong here as pressure toward wider permissions.

**Why it matters.** The audit trail is part of what makes an action reviewable, and these shapes
remove it. Several are ordinary in legitimate skills, which is why they are locators.

**What Walkdown looks for.** The shapes above. No pattern row cites this class directly: set H in
`PHRASES.md` holds them, and class 5 holds the plain suppression form.

## 21. Conditional activation

**What it is.** Any branch in instruction text is a place where the reviewed behavior and the
delivered behavior can differ: an instruction that depends on which AI tool is running, on a date or a
version, on whether this is the first run, on the name of the repository, organization, or machine,
or on a failure, where a troubleshooting section can ask for a token or name a destination.

**Why it matters.** A hostile version fires only where nobody is looking: on the tool with the loosest
permissions, after a date, on a certain machine.

**What Walkdown looks for.** Harness conditionals, clock and version gates, first-run and
later-run states, environment gates, and an error path followed by a command, address, or token.
The full set is I in `PHRASES.md`.

**Patterns:** `I.clock`, `I.environment`

## 22. Harness-prohibited actions

**What it is.** Every AI tool publishes or embeds a list of actions it will not take, or will confirm
first: entering credentials or payment details, creating accounts, deleting permanently, moving
money, changing security settings, solving CAPTCHAs, sending messages, publishing, buying, accepting
terms, submitting forms. That list is a rubric.

**Why it matters.** A skill that asks for exactly those actions without a confirmation asks the
model to do what its own tool says it must not, or must ask about first. For a browser or desktop
agent this is the common case.

**What Walkdown looks for.** Instructions that ask for the listed actions, and whether a
confirmation step accompanies each. The phrase step (`02.4-phrases`) assigns each such row to the tool's own tier
(prohibited or confirm-first) in `vocab.yaml`, and an action in the prohibited tier with no
confirmation is the strongest phrase-level locator Walkdown has. The full set is J in `PHRASES.md`.
