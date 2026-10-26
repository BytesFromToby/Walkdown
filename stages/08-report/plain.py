"""Plain words for what each stage 4 pattern looks for. Spec: specs/review_html.SPEC.md.

Moved here from pre-planning/soft/d3/build.py (review C21, 2026-10-12): the owner found the
pattern notes ("confirm-first tier with no confirmation") to be jargon while labeling D3, and
the review page shows the same descriptions to the report reader. Each entry says what the
words are and why a pattern would care ("The worry: ..."), never whether the line is a
problem. Every row of stages/04-phrases/patterns.yaml has one (tests/test_plain.py); a new
pattern needs its plain description too.
"""
from __future__ import annotations

PLAIN = {
    # 4a reaching out: sending data out (K)
    "K.dest-ref": "A destination named by reference (\"the usual endpoint\", \"your team's webhook\") instead of an address. The worry: the model fills in where data goes from somewhere a reader cannot see.",
    "K.dest-stored": "Sending something to an address kept elsewhere (\"post the results to the endpoint stored in the config\"). The worry: where the data goes is decided by a file or setting a reviewer may never open.",
    "K.assembly-code": "Code that builds a string from pieces (\"a\" + \"b\", chr(), fromCharCode, reversed strings). The worry: an address or command built this way never shows up when you search for it.",
    "K.assembly-prose": "Instructions to build a web address or host name from parts (\"join these pieces to form the URL\"). The worry: the destination never appears whole anywhere in the text.",
    "K.telemetry": "Telemetry, analytics, usage data, opt-out, or update checks. The worry: something sends data home.",
    "K.telemetry-send": "Sending usage, crash, or analytics data (\"collects usage statistics\") with no opt-in beside it. The worry: data about the user leaves the machine unless they find the way to turn it off.",
    "K.md-carrier": "Markdown that hides text when rendered (a collapsed <details> section, link definitions that point at a web address, long image alt text). The worry: the model reads text a person viewing the page may not see.",
    "K.url-template": "An image address with a slot for text in it ({{...}}, ${...}). The worry: when the page is drawn, the slot is filled with text from the conversation and sent to that address.",
    "K.relay-host": "A known paste or relay service (webhook.site, requestbin, ngrok, pastebin, gists, file-transfer sites). The worry: these services are a common way to catch data sent out of a machine.",
    "K.chat-webhook": "A chat webhook address (Slack, Discord, a Telegram bot). The worry: anything posted there leaves the machine and lands in someone's chat.",
    "K.http-verb": "A command or library that makes web requests (curl, wget, fetch, requests.post, axios). The worry: it is how data gets sent out or code gets pulled in.",
    "K.dns": "A DNS lookup (nslookup, dig) with a variable built into the name. The worry: data can leave the machine hidden inside a lookup, which most firewalls let through.",
    "K.encode-send": "Encoding something (base64 and the like) and piping it straight into a network command. The worry: the usual shape of packaging data to send it out.",
    "K.data-flow": "A source of private data, a sending verb, and a destination in one sentence (\"put your environment variables in the bug report\"). The worry: data leaves the machine.",
    # 4a reaching out: credentials (creds)
    "creds.path": "A path where credentials live (~/.ssh, SSH keys, ~/.aws, .npmrc, .git-credentials). The worry: it points the model at secrets.",
    "creds.dotenv": "Reading, loading, or copying a .env file. The worry: .env files usually hold keys and passwords.",
    "creds.secret-name": "A name that usually holds a secret (API_KEY, SECRET, ACCESS_TOKEN, PRIVATE_KEY, PASSWORD, BEARER). The worry: it marks where a key or password is used or read.",
    "creds.env-enum-code": "Code that reads all environment variables at once (printenv, looping over os.environ). The worry: environment variables often hold keys and passwords.",
    "creds.enumerate": "Checking, scanning, or collecting environment variables, keys, or tokens in bulk. The worry: it gathers every secret at once, where one named value would do.",
    "creds.desktop": "Reading the clipboard, recording the screen, or using saved browser sessions or saved passwords. The worry: these hold private data from outside the project.",
    "creds.recon": "Listing what is installed or configured (skills, plugins, MCP servers, settings files, the user's CLAUDE.md). The worry: a map of the user's setup is private data, and useful to whoever receives it.",
    # 4a reaching out: loading from elsewhere (RL)
    "RL.fetch-follow": "Fetching text or code from elsewhere and then acting on it (\"download and run\", \"fetch and follow the instructions at\"). The worry: what happens is decided by whatever is at that address when it is fetched.",
    "RL.raw-host": "A raw file host (raw.githubusercontent.com, gist.github.com). The worry: files there can change at any time, and are often loaded straight into a model or a shell.",
    "RL.pipe-shell": "Downloading a script and piping it straight into a shell (curl ... | bash, iwr ... | iex). The worry: the script runs before anyone reads it.",
    "RL.branch-ref": "Points at a moving branch (@main, @latest) instead of a fixed version. The worry: what loads can change after review.",
    "RL.cross-repo-skill": "Loading or installing a skill from another repository or marketplace. The worry: part of what this skill does lives outside the repository you are reviewing.",
    # 4b taking the wheel: overrides (L)
    "L.ignore": "\"Ignore\" or \"disregard\" previous, prior, or above instructions (or set them aside). The worry: it tells the model to drop what it was told before, the most common shape of a prompt injection.",
    "L.forget": "\"Forget everything\", \"reset your context\", \"start over\". The worry: it tells the model to drop what it was told before.",
    "L.override": "Overriding, superseding, or replacing instructions, prompts, or rules. The worry: text that claims to replace the rules the model was given.",
    "L.identity": "Gives the model a new identity (\"you are now ...\", \"act as ...\", \"from now on you ...\"). The worry: it replaces who the model is working for.",
    "L.new-instructions": "Announces new or real instructions (\"here are your new instructions\", \"your real task is\"). The worry: everything before it is recast as no longer the task.",
    "L.system-frame": "A line dressed up as a system message (\"system:\", <system>, [system], ### Instruction). The worry: it imitates the format a model gives the most authority.",
    "L.guardrail": "Turning off rules or safeguards (\"bypass your guidelines\", \"no restrictions\", \"unrestricted mode\"). The worry: it asks the model to drop its own safety rules.",
    "L.context-end": "A fake end of the prompt (\"end of system prompt\", \"--- end\", </system>). The worry: it pretends the real instructions are over, so what follows reads as new ones.",
    "L.priority": "Claims top priority (\"this is the most important instruction\", \"IMPORTANT: ignore\"). The worry: it ranks itself above everything else the model was told.",
    "L.skip-confirm": "Permission to skip asking (\"no need to ask\", \"without asking\", \"you may skip confirmation\"). The worry: it removes the user's chance to say no.",
    # 4b taking the wheel: claimed consent (A)
    "A.prior-consent": "Says the user already approved or configured something (\"the user has already authorized this\"). The worry: the model is told consent exists without the user being asked.",
    "A.per-settings": "Cites the user's settings or preferences as the reason (\"per the user's settings\"). The worry: a claimed preference the model cannot check stands in for asking.",
    "A.install-consent": "Says installing counts as consent (\"installing this constitutes your approval\"). The worry: approval for later actions is claimed from the act of installing.",
    "A.standing": "Claims a standing approval or standing permission. The worry: one approval is stretched to cover actions the user never saw.",
    "A.persona-grant": "Tells the model it is authorized or permitted (\"you have been authorized to\"). The worry: the text grants permissions only the user can give.",
    "A.role-authority": "Gives the model a role with standing, full, or admin authority. The worry: a title is used to claim powers nobody granted.",
    "A.scope": "Stretches one confirmation over many actions (\"confirm once\", \"covers all subsequent\"). The worry: the user says yes once and later actions ride on it.",
    "A.dialogue": "A line that starts like a chat transcript (\"User:\", \"Assistant:\", \"System:\"). The worry: a made-up exchange can look like the user already said something.",
    "A.harness-mimicry": "Text formatted like the AI tool's own messages (<system-reminder>, <function_results>, [Tool result], hookSpecificOutput). The worry: it imitates messages the model trusts as coming from its own tool.",
    "A.notify-proceed": "Tell the user something, then carry on (\"let the user know, then run it\"). The worry: the user is informed but never gets to say no.",
    # 4b taking the wheel: definitions (B)
    "B.means": "Redefines a word so it includes an action (\"'clean up' means delete\", \"'sync' means push\"). The worry: an innocent-sounding word quietly carries a risky action.",
    "B.includes-verb": "Says one action includes another (\"cleanup includes deleting the remote branch\"). The worry: a routine word quietly carries a bigger action.",
    "B.def-destination": "Defines a word as a web address or a home-folder path. The worry: a destination hides behind an ordinary-looking word.",
    "B.when-says": "Maps something the user says to an action (\"when the user says 'ship it', push\"). The worry: a casual phrase from the user sets off a risky action.",
    "B.default-dest": "A default that names a destination (\"by default, uploads go to https://...\"). The worry: data goes somewhere the user never chose.",
    "B.absence": "A rule for when something is missing (\"if there is no CLAUDE.md\", \"is not configured\"). The worry: behavior that only runs when a setting or safeguard is absent.",
    "B.safety-exception": "A rule with a carve-out (\"never ... except\", \"do not ... unless\"). The worry: the exception is where the rule stops protecting.",
    "B.safety-adjective": "A reassuring word next to a command or script (\"read-only\", \"harmless\", \"sandboxed\", \"no side effects\"). The worry: the label vouches for code the reader has not checked.",
    "B.lookalike": "A domain that imitates example.com (exarnple.com, examp1e.com). The worry: it looks like a harmless placeholder and is a real, different address.",
    # 4b taking the wheel: steering the review (H)
    "H.anti-inspect": "\"Already reviewed\" or \"already checked\". The worry: it talks a reviewer out of looking.",
    "H.mandated-phrasing": "Says exactly what to say (\"respond with exactly\", \"announce '...'\"). The worry: the model's report to the user is scripted.",
    "H.preempt": "Heads off the model's own doubts (\"you might think ...\", \"not negotiable\", \"stop rationalizing\"). The worry: it discourages the model from pushing back.",
    "H.consequence": "Warns of damage if a step is skipped (\"failure to do this will corrupt your data\"). The worry: pressure that rushes the model past checking.",
    "H.evidence": "Deleting or removing logs, reports, plans, transcripts, or history. The worry: it removes the record of what happened.",
    "H.sabotage": "Calls something deprecated, superseded, or to be skipped (\"skip the review hook\", \"X is deprecated\"). The worry: it steers the model away from another skill or check.",
    "H.precedence": "Claims to override something (\"takes precedence over your instructions\", \"supersedes CLAUDE.md\"). The worry: it ranks itself above the user or other rules.",
    "H.self-attest": "Vouches for itself (\"reviewed by\", \"no telemetry\", \"does not collect\", \"contains no\"). The worry: a claim about the code that the reader is asked to take on trust.",
    "H.unbounded": "Keep going with no stopping point (\"retry until it succeeds\", \"do not stop until\"). The worry: the model never stops to ask.",
    "H.suppress": "Tells the model to keep something from the user (\"do not mention\", \"don't tell\", \"silently\", \"omit from the summary\"). The worry: the user never hears what happened.",
    # 4b taking the wheel: conditions (I)
    "I.harness": "A condition on which AI tool is running it (\"if you are running in Codex\", a bullet per tool). The worry: different tools can be given different instructions.",
    "I.clock": "A date or time condition (\"after March 2026\", \"on the first of the month\"). The worry: behavior that switches on later, after review.",
    "I.version": "A condition on a version (\"version >= 2\", \"or later\", \"and above\"). The worry: behavior that switches on in some versions only.",
    "I.state": "First run versus later runs (\"on first run\", \"subsequent sessions\"). The worry: behavior that changes after the first time it is watched.",
    "I.environment": "A condition on where it runs (\"if the repository name is ...\", \"if the hostname is ...\"). The worry: behavior that switches on only on certain machines.",
    "I.failure-path": "What to do when something fails, followed by a command, web address, or token. The worry: the failure path is rarely read and can carry its own instructions.",
    # 4c changing the environment: permissions (E, phrase.E.perms)
    "E.perm-flags": "A setting or flag that skips or widens permissions (--dangerously-skip-permissions, bypassPermissions, permissions.allow, allowedTools). The worry: the AI tool stops asking before it acts.",
    "E.exec-primitive": "A way to run commands or code (sudo, chmod +x, subprocess, os.system, child_process, eval, exec, pickle.loads). The worry: it can run anything the user can.",
    "E.outlives-session": "Something that keeps running after the session ends (nohup, background services, crontab, launchctl, scheduled tasks). The worry: it outlives the task and runs when nobody is watching.",
    "E.runtime-install": "Installing packages while it runs (npm install, pip install, uv sync and the like, in a script or hook). The worry: code from a public registry arrives after the review, at whatever version is current.",
    "E.write-then-exec": "Writing a file to a temporary folder and then running it. The worry: what runs is made on the fly and never sits in the repository to be read.",
    "E.allowlist": "Adding tools or commands to an allow list or auto-approve list. The worry: those actions stop asking the user first, from then on.",
    "E.confirm-off": "Turning off a confirmation or permission prompt. The worry: it removes the user's chance to say no.",
    "E.install-global": "Installing globally or as a plugin (npm install -g, npx -y, plugin install, marketplace add). The worry: it installs beyond this project and stays.",
    # 4c changing the environment: settings and persistence (E, phrase.E.env)
    "E.redirect-var": "A variable that reroutes network traffic (ANTHROPIC_BASE_URL, HTTPS_PROXY, a custom package registry). The worry: requests, possibly with keys in them, go through a server someone else picked.",
    "E.git-keys": "A git setting that persists (insteadOf, credential.helper, core.hooksPath, clean and smudge filters). The worry: it changes how git behaves, or what it runs, in every later command.",
    "E.mcp": "Registering an MCP server (a connector that gives the model new tools). The worry: it adds tools and data access beyond the skill itself.",
    "E.install": "Installing a package or tool (pip install, npm install, and the like). The worry: it runs code from outside the repository.",
    "E.self-install": "Copying a skill into the user's global skill folders (~/.claude/skills and the like). The worry: it spreads beyond this project.",
    "E.memory": "A memory or local-settings file (MEMORY.md, memory/, CLAUDE.local.md, settings.local.json). The worry: what is written there loads into future sessions.",
    "E.connector": "Connecting an account (\"connect your Gmail\", \"sign in with GitHub\", \"authorize Drive\"). The worry: it gives the model access to the user's own data.",
    "E.clone": "Cloning or pulling in another repository (git clone, gh repo clone, submodule add). The worry: outside code and text arrive that nobody reviewed here.",
    "E.editor-autorun": "An editor setting that runs a task when a folder opens (.vscode/tasks.json with runOn folderOpen, .idea/). The worry: code runs just by opening the project.",
    "E.export": "Setting an environment variable in prose (export NAME=value). The worry: it changes settings for everything run afterward.",
    "E.persist-target": "Writing to a file that loads in every future session (CLAUDE.md, AGENTS.md, shell profiles, git hooks, editor or agent settings). The worry: the change outlives the task.",
    "E.harness-binary": "Patching, rewriting, or re-signing the AI tool's own program (codesign --force, modifying the claude binary). The worry: it changes the tool that enforces the rules.",
    "E.persist-redirect": "Writing with >> or tee into a shell profile, git hooks, or git config. The worry: the change runs in every later shell or git command.",
    # 4c changing the environment: second-order text (C)
    "C.frontmatter-grant": "The settings block at the top of a skill or agent file that gives it tools or picks its model. The worry: it decides what the agent is allowed to do.",
    "C.fan-out": "Sends a subagent per item (\"dispatch a subagent for each file\") to apply or change things. The worry: one instruction becomes many actions at once, each harder to watch.",
    "C.note-to-ai": "A note addressed to the AI (\"NOTE TO AI\", \"INSTRUCTIONS FOR THE ASSISTANT\"). The worry: text aimed at the model inside something a person may skim.",
    "C.comment-ai": "A code comment that starts \"AI:\", \"Claude:\", \"assistant:\", or \"agent:\". The worry: instructions to the model tucked into code comments, which reviewers often skip.",
    "C.emit-instruction": "A script that prints an instruction (echo or print with MUST, an all-caps tag, or \"you ...\"). The worry: the model reads script output and may follow it.",
    "C.script-instruction": "A command to run, written inside a string in a script (\"Run: npx ...\"). The worry: when the script's output reaches the model, it reads as an instruction to run that command.",
    "C.error-instruction": "A command or web address inside an error message a script prints. The worry: the model reads error output and may follow what it says.",
    "C.boilerplate": "Tells the model to add a footer, badge, link, or trailer to what it writes. The worry: text that copies itself into the user's other work.",
    "C.skills-author": "Tells the model how to write every skill, hook, agent, rule, or CLAUDE.md it creates. The worry: its instructions spread into files that outlive this skill.",
    "C.guard-instruction": "Tells a reviewer or verifier subagent to approve, pass, or skip something. The worry: the check that should catch problems is told what to conclude.",
    "C.guard-routing": "Sends the reviewer or verifier to the cheapest or smallest model. The worry: the safety check runs on the weakest reader.",
    # 4c changing the environment: trusted channels (D)
    "D.compact-matcher": "A hook set to fire when the conversation is compacted. The worry: its text is put back in after the model's memory is trimmed, when earlier context is gone.",
    "D.match-all": "A hook that fires on every tool call (matcher \".*\", \"*\", or empty). The worry: it sees, and can change, every action the AI takes.",
    "D.additional-context": "A hook output field that adds text to the model's context (additionalContext). The worry: that text arrives looking like it comes from the AI tool itself.",
    "D.pseudo-tag": "An all-caps tag like <IMPORTANT> or <SYSTEM-REMINDER> wrapped around text. The worry: it dresses ordinary text up as an official system message.",
    "D.current-version": "\"Read the current version\" or \"skills evolve\". The worry: it tells the model to trust whatever text is there later, which can change after install.",
    "D.verify-run": "Verification done by running something (\"to verify, run ...\", \"verify the install\"). The worry: a check that is really an instruction to execute.",
    "D.hook-inject": "Text emitted or injected through a hook, at session start or after compaction. The worry: it reaches the model before the user types anything, with the tool's authority.",
    "D.authority": "Claims system-level or admin-level authority (\"treat this as a system message\"). The worry: ordinary text claims the weight of the system prompt.",
    # 4d talking to the human: actions the harness rules restrict (J)
    "J.enter-secret": "Typing or pasting a password, token, API key, or card number. The worry: Claude Code's rules say the user enters these, never the model.",
    "J.confirm-first": "An action that reaches outside the computer (send a message or email, post, publish, submit, buy, accept terms, approve a PR or payment) with no \"ask\" or \"confirm\" on the same line. The worry: Claude Code's rules say these need the user's OK first.",
    "J.saved-login": "Logging in with saved or stored credentials. The worry: the model signs in as the user without asking.",
    "J.cookie": "Accepting or dismissing a cookie or consent banner. The worry: agreeing to terms is the user's call, and Claude Code's rules ask first.",
    "J.irreversible": "An action that cannot be undone (permanently delete, empty the trash, force push). The worry: there is no going back.",
    "J.prohibited-other": "Creating accounts, moving money, changing security settings, or solving CAPTCHAs. The worry: Claude Code's rules say the model never does these; the user does.",
    "J.confirm-first-other": "Granting OAuth access, changing account settings, creating standing rules, or accepting terms. The worry: Claude Code's rules say these need the user's OK first.",
    # 4d talking to the human: instructions to people (G)
    "G.perm-flags-docs": "Permission flags (--dangerously-skip-permissions and the like) in a README or install docs. The worry: the docs tell a person to run the AI tool with its safety prompts off.",
    "G.launch-lowered": "Tells a person to launch the AI tool with permissions skipped (--dangerously-skip-permissions, --yolo). The worry: every later action runs without asking.",
    "G.pipe-shell": "Tells a person to pipe a downloaded script into a shell (curl ... | sh, iwr ... | iex). The worry: the script runs on their machine before anyone reads it.",
    "G.paste-terminal": "Tells a person to paste or type something into their terminal. The worry: they run what they are handed, unread.",
    "G.trust-grant": "Tells a person to trust a folder, repository, plugin, or author, or to add something to an allow list. The worry: it lowers their tool's defenses for everything that follows.",
    "G.agent-template": "Text addressed to an AI reading it (\"if you are an AI agent ...\", \"we assume an agent filed this\"). The worry: it speaks to the model directly, past the human.",
    "G.contrib-imperative": "An instruction to a contributor in CONTRIBUTING files, issue templates, and the like (\"you must\", \"please run\"). The worry: a visitor's AI agent reading the file may follow it as an instruction.",
}


def describe(patterns) -> list[tuple[str, str]]:
    """(id, plain words) per pattern id, in the order given, each once. An id with no entry
    (a retired pattern in an old run) keeps its id and says so."""
    out, seen = [], set()
    for p in patterns or []:
        if p in seen:
            continue
        seen.add(p)
        out.append((p, PLAIN.get(p) or "A search pattern this version of Walkdown no longer has."))
    return out
