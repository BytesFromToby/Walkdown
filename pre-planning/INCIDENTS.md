# Incidents — what actually went wrong, and what we would have caught

Real published cases, each mapped to whether this method would have found it and
at which pass. The misses matter more than the hits: they define the boundary of
what a static instruction-layer audit can ever do.

Compiled 2026-08-30.

---

## Caught

### Rules File Backdoor — Pillar Security, March 2025
AI coding assistant rule files (`.cursor/rules`, shared via cursor.directory and
GitHub) poisoned with instructions encoded in **invisible Unicode** — zero-width
joiners and bidirectional markers. Invisible in pull request review, fully
readable by the model. Injected rules override safety controls, generate
backdoored code, add unmentioned external script references, and exfiltrate
credentials. The assistant never mentions the added script tag in its response.
Compromised rules affect all future sessions and survive project forking.

**Caught at stage 2 (reader).** This is precisely the invisible-character scan. Superpowers
scored zero on it; this is what a non-zero score looks like.
**Also note:** "never mentions it in the response" is the audit-trail suppression
sub-class, and it is the reason that sub-class is ranked worst in THREATS class 5.

### OpenClaw / ClawHub — Unit 42, February–May 2026
Marketplace skills for an agent platform with broad local access. Five malicious
skills found after the marketplace had already added VirusTotal and ClawScan
screening. Two delivered macOS infostealers with C2 infrastructure. One used
**22 MB of padding characters in its README** to exceed scanner size thresholds
and bypass both scanners. Two used novel agentic techniques: runtime affiliate
injection controlling financial recommendations through external payloads, and
coordinated agents running crypto pump-and-dump.

**Caught at stage 1 (inventory).** The padding is a file-size outlier — a metric we
did not have until this incident, now Reporting 1.4 (was 1.6). Runtime affiliate
injection is remote instruction loading, class 3.
**The lesson worth keeping:** the evasion targeted the *scanner's* limits, not the
model's. Any automated pass has thresholds, and thresholds are the attack surface.

### Malicious MCP server: `postmark-mcp` — September 2025
A working, useful MCP server mirroring a legitimate vendor's product. Fifteen
clean releases. Version 1.0.16 added **one line** silently BCC'ing every email
processed to an attacker-controlled domain.

**Missed by a snapshot audit. Caught only by version delta.**
This is the "be useful first" attack from RED-TEAM.md §1, confirmed in the wild
with a real body count. Every scan of v1.0.0 through v1.0.15 was clean and correct.
The strongest attack class defeats the method as currently written.

---

## Partially caught

### Amazon Q VS Code extension — July 2025
An attacker obtained commit access to the official extension repository and landed
a destructive "wiper" prompt instructing the agent to delete local files and cloud
resources. Shipped in an official release to a large install base.

**Content would be caught at stage 4** — destructive commands in instruction text
are not subtle. **But only if someone audited the release**, and the trust signal
(official vendor, official marketplace) is exactly what stops anyone from looking.

**What this exposes:** the method has no temporal or social axis. Commit access
changes, first-time contributors landing changes in mature repos, and maintainer
identity churn are all invisible to it. RED-TEAM §7 flagged this; this incident
is the proof.

---

## Out of scope — and worth saying so plainly

These are real, serious, and a static artifact audit will never catch them. A
charter that does not name its blind spots is marketing.

### EchoLeak — CVE-2025-32711, Microsoft 365 Copilot, June 2025
Zero-click exfiltration. An attacker sends an ordinary email; indirect prompt
injection in its content causes the assistant to leak context data through a
markdown-rendered channel, with no user interaction at all.

**Out of scope.** There is no artifact to audit. The malicious instructions arrive
at runtime inside content the agent processes. This is a platform vulnerability,
not a supply chain one.

### Indirect prompt injection in the wild — Unit 42
Agents browsing attacker-controlled web pages and following instructions found in
the page content.

**Out of scope**, same reason. The payload is in the data the agent reads, not in
the package it installed.

### Replit agent deleting a production database — July 2025
An agent with production access took a destructive action outside its brief.

**Out of scope.** No malicious artifact, no attacker. A permissions and blast
radius problem.

**The boundary this draws:** Walkdown audits *artifacts that ship*. It does
not and cannot audit *content that arrives at runtime*. Say this in every report.
The trifecta control is the answer to the out-of-scope cases — break a leg at
install time — which is why RED-TEAM's defensive note matters more than any
detection we build.

---

## Added 2026-09-04

Three more, chosen because each one lands on a class that did not exist in
THREATS.md before this date. Citations checked on 2026-09-04; the sources are
appended below.

### Nx "s1ngularity" — npm, August 2025
A compromised publishing token pushed malicious versions of `nx` and its
plugins. The `postinstall` payload (`telemetry.js`) did something new: it
**invoked the developer's own AI coding CLIs** (Claude, Gemini, Amazon Q) with
permission-bypass flags and a prompt instructing the agent to inventory the
filesystem for SSH keys, `.env` files, wallets, and tokens, then exfiltrated
the results to a public GitHub repository created under the victim's account.

**Caught, in part, at stage 4.** The `postinstall` is class 8. The
permission-bypass flags in a string literal are the class 7 addition. The prompt
text inside a script is class 15 (instruction text in code). None of those
three greps existed before this date, and the first two are the cheapest tells
in the register.
**What it inverts:** every earlier case is prose that carries a payload. This
is code that carries prose. The instruction layer is now a payload format for
conventional malware, which means the method applies to any package that
contains a prompt, not only to packages that call themselves skills.
**Scope note:** an npm package is outside the project's corpus. The class it
proves is inside.

### CurXecute (CVE-2025-54135) and MCPoison (CVE-2025-54136) — Cursor, August 2025
CurXecute: a prompt injection reaching the agent through any connected MCP
server could cause it to **write `.cursor/mcp.json`**, and Cursor executed the
newly listed server command without confirmation. MCPoison: an MCP server entry
approved once stayed approved when its command was changed, because trust was
bound to the entry's name and not its content.

**Trigger out of scope; mechanism in scope.** The injection arrives at runtime
(same boundary as EchoLeak). But the mechanism is a persistence target this
register did not list: an MCP config file is an execution grant, and a skill
that instructs writing one is class 5 and class 17 in a single line. MCPoison
is the version-delta problem at the config level: approval of a name, not a
hash. Both are now in the persistence-target list and both argue for "pin by
content" in every writeup.

### GitHub MCP toxic agent flow — Invariant Labs, May 2025
A public issue on a public repository carried instructions. A developer asked
an agent with the GitHub MCP server to look at open issues. The agent read the
issue, followed it, pulled data from the developer's private repositories, and
posted it in a public pull request.

**Out of scope**, same reason as EchoLeak: no artifact shipped. Recorded because
it is the cleanest published demonstration of the trifecta as a design failure,
and because the destination was the user's own public surface, which is the
RED-TEAM §10 pattern with a real body count. Any report that says "the skill
only writes to the user's own repository" should cite this case before calling
that safe.

---

## What these incidents changed

Three additions, each earned by a specific case:

1. **File-size outliers** (OpenClaw padding) → Reporting §1.6. Any automated pass
   has thresholds; publish yours or they become the attack surface.
2. **Undocumented endpoints** (Unit 42's recommendation) → cross-reference every
   URL found in code against the URLs mentioned in documentation. A network
   destination the docs never mention is the cheapest high-signal check available,
   and the URL extractor already produces half of it.
3. **Version delta is now the highest-priority gap**, not a nice-to-have. Postmark
   proves a snapshot audit is defeated by patience alone.

---

## Sources

- Pillar Security. *New Vulnerability in GitHub Copilot and Cursor: How Hackers Can
  Weaponize Code Agents Through Compromised Rule Files.* March 2025.
  https://www.pillar.security/blog/new-vulnerability-in-github-copilot-and-cursor-how-hackers-can-weaponize-code-agents
  Coverage: https://thehackernews.com/2025/03/new-rules-file-backdoor-attack-lets.html
- Unit 42, Palo Alto Networks. *OpenClaw's Skill Marketplace and the Emerging AI
  Supply Chain Threat.* 2026. https://unit42.paloaltonetworks.com/openclaw-ai-supply-chain-risk/
- Unit 42. *Fooling AI Agents: Web-Based Indirect Prompt Injection Observed in the
  Wild.* https://unit42.paloaltonetworks.com/ai-agent-prompt-injection/
- Snyk. *Malicious MCP Server on npm: postmark-mcp Harvests Emails.* September 2025.
  https://snyk.io/blog/malicious-mcp-server-on-npm-postmark-mcp-harvests-emails/
  Vendor statement: https://postmarkapp.com/blog/information-regarding-malicious-postmark-mcp-package
- BleepingComputer. *Amazon AI coding agent hacked to inject data wiping commands.*
  July 2025. https://www.bleepingcomputer.com/news/security/amazon-ai-coding-agent-hacked-to-inject-data-wiping-commands/
- Rescana / Hack The Box on CVE-2025-32711 (EchoLeak).
  https://www.hackthebox.com/blog/cve-2025-32711-echoleak-copilot-vulnerability
- Help Net Security. *Prompt injection still drives most agentic AI security
  failures in production.* June 2026.
  https://www.helpnetsecurity.com/2026/06/11/owasp-prompt-injection-ai-security-failures/
- IBM X-Force. *What OpenClaw reveals about agentic AI security risks.*
  https://www.ibm.com/think/x-force/what-openclaw-reveals-about-agentic-ai-security-risks

Accessed 2026-08-30.

Added 2026-09-04:

- Nx. *S1ngularity: What Happened, How We Responded, What We Learned.*
  https://nx.dev/blog/s1ngularity-postmortem
  GitHub advisory GHSA-cxm3-wv7p-598c / CVE-2025-10894:
  https://github.com/advisories/GHSA-cxm3-wv7p-598c
  Snyk. *Weaponizing AI Coding Agents for Malware in the Nx Malicious Package.*
  https://snyk.io/blog/weaponizing-ai-coding-agents-for-malware-in-the-nx-malicious-package/
  safedep. https://safedep.io/nx-build-system-compromise/
- Tenable. *FAQ: CVE-2025-54135, CVE-2025-54136 (CurXecute and MCPoison).*
  https://www.tenable.com/blog/faq-cve-2025-54135-cve-2025-54136-vulnerabilities-in-cursor-curxecute-mcpoison
  NVD entry: https://www.tenable.com/cve/CVE-2025-54135
- Invariant Labs. *GitHub MCP Exploited: Accessing private repositories via MCP.*
  https://invariantlabs.ai/blog/mcp-github-vulnerability
  Tracking issue: https://github.com/github/github-mcp-server/issues/844

Accessed 2026-09-04.
