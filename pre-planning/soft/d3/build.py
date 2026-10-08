"""Build the D3 blind labeling page: pre-planning/soft/d3/label.html.

    python pre-planning/soft/d3/build.py

D3 (pre-planning/soft/README.md): the owner labels the 119 real lines independently, to see
whether the five-way labels are reproducible and whether the answer sheet is trustworthy. The
page shows each line with its context, the pattern that flagged it, and the same label
definitions the models get (stages/06-soft/softreads.yaml). It never shows the answer sheet's
label or reason. Items are shuffled with a fixed seed so repository order does not anchor.
"""
from __future__ import annotations

import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "stages" / "06-soft"))

import packet  # noqa: E402
import softdata  # noqa: E402

OUT = Path(__file__).resolve().parent / "label.html"
SEED = 3

# What each pattern looks for, in plain words (owner, 2026-10-08: the pattern notes, e.g.
# "confirm-first tier with no confirmation", were jargon). Each says what the words are and
# why a pattern would care, never which label fits. Patterns not listed fall back to the note.
PLAIN = {
    "A.notify-proceed": "Tell the user something, then carry on (\"let the user know, then run it\"). The worry: the user is informed but never gets to say no.",
    "B.means": "Redefines a word so it includes an action (\"'clean up' means delete\", \"'sync' means push\"). The worry: an innocent-sounding word quietly carries a risky action.",
    "B.safety-adjective": "A reassuring word next to a command or script (\"read-only\", \"harmless\", \"sandboxed\", \"no side effects\"). The worry: the label vouches for code the reader has not checked.",
    "B.safety-exception": "A rule with a carve-out (\"never ... except\", \"do not ... unless\"). The worry: the exception is where the rule stops protecting.",
    "C.error-instruction": "A command or web address inside an error message a script prints. The worry: the model reads error output and may follow what it says.",
    "C.frontmatter-grant": "The settings block at the top of a skill or agent file that gives it tools or picks its model. The worry: it decides what the agent is allowed to do.",
    "D.current-version": "\"Read the current version\" or \"skills evolve\". The worry: it tells the model to trust whatever text is there later, which can change after install.",
    "D.pseudo-tag": "An all-caps tag like <IMPORTANT> or <SYSTEM-REMINDER> wrapped around text. The worry: it dresses ordinary text up as an official system message.",
    "E.install": "Installing a package or tool (pip install, npm install, and the like). The worry: it runs code from outside the repository.",
    "E.mcp": "Registering an MCP server (a connector that gives the model new tools). The worry: it adds tools and data access beyond the skill itself.",
    "E.persist-target": "Writing to a file that loads in every future session (CLAUDE.md, AGENTS.md, shell profiles, git hooks, editor or agent settings). The worry: the change outlives the task.",
    "E.self-install": "Copying a skill into the user's global skill folders (~/.claude/skills and the like). The worry: it spreads beyond this project.",
    "G.agent-template": "Text addressed to an AI reading it (\"if you are an AI agent ...\", \"we assume an agent filed this\"). The worry: it speaks to the model directly, past the human.",
    "H.anti-inspect": "\"Already reviewed\" or \"already checked\". The worry: it talks a reviewer out of looking.",
    "H.evidence": "Deleting or removing logs, reports, plans, transcripts, or history. The worry: it removes the record of what happened.",
    "H.mandated-phrasing": "Says exactly what to say (\"respond with exactly\", \"announce '...'\"). The worry: the model's report to the user is scripted.",
    "H.precedence": "Claims to override something (\"takes precedence over your instructions\", \"supersedes CLAUDE.md\"). The worry: it ranks itself above the user or other rules.",
    "H.preempt": "Heads off the model's own doubts (\"you might think ...\", \"not negotiable\", \"stop rationalizing\"). The worry: it discourages the model from pushing back.",
    "H.report-only": "Limits what gets reported (\"report only the status\", \"no more than five lines\"). The worry: details the user would want are left out.",
    "H.sabotage": "Calls something deprecated, superseded, or to be skipped (\"skip the review hook\", \"X is deprecated\"). The worry: it steers the model away from another skill or check.",
    "H.unbounded": "Keep going with no stopping point (\"retry until it succeeds\", \"do not stop until\"). The worry: the model never stops to ask.",
    "I.clock": "A date or time condition (\"after March 2026\", \"on the first of the month\"). The worry: behavior that switches on later, after review.",
    "I.environment": "A condition on where it runs (\"if the repository name is ...\", \"if the hostname is ...\"). The worry: behavior that switches on only on certain machines.",
    "I.failure-path": "What to do when something fails, followed by a command, web address, or token. The worry: the failure path is rarely read and can carry its own instructions.",
    "I.harness": "A condition on which AI tool is running it (\"if you are running in Codex\", a bullet per tool). The worry: different tools can be given different instructions.",
    "I.state": "First run versus later runs (\"on first run\", \"subsequent sessions\"). The worry: behavior that changes after the first time it is watched.",
    "I.version": "A condition on a version (\"version >= 2\", \"or later\", \"and above\"). The worry: behavior that switches on in some versions only.",
    "J.confirm-first": "An action that reaches outside the computer (send a message or email, post, publish, submit, buy, accept terms, approve a PR or payment) with no \"ask\" or \"confirm\" on the same line. The worry: Claude Code's rules say these need the user's OK first.",
    "J.irreversible": "An action that cannot be undone (permanently delete, empty the trash, force push). The worry: there is no going back.",
    "K.data-flow": "A source of private data, a sending verb, and a destination in one sentence (\"put your environment variables in the bug report\"). The worry: data leaves the machine.",
    "K.md-carrier": "Markdown that hides text when rendered (a collapsed <details> section, unused link definitions, long image alt text). The worry: the model reads text a person viewing the page may not see.",
    "K.telemetry": "Telemetry, analytics, usage data, opt-out, or update checks. The worry: something sends data home.",
    "L.forget": "\"Forget everything\", \"reset your context\", \"start over\". The worry: it tells the model to drop what it was told before.",
    "L.identity": "Gives the model a new identity (\"you are now ...\", \"act as ...\", \"from now on you ...\"). The worry: it replaces who the model is working for.",
    "L.skip-confirm": "Permission to skip asking (\"no need to ask\", \"without asking\", \"you may skip confirmation\"). The worry: it removes the user's chance to say no.",
    "RL.branch-ref": "Points at a moving branch (@main, @latest) instead of a fixed version. The worry: what loads can change after review.",
    "creds.env-enum-code": "Code that reads all environment variables at once (printenv, looping over os.environ). The worry: environment variables often hold keys and passwords.",
    "creds.path": "A path where credentials live (~/.ssh, SSH keys, ~/.aws, .npmrc, .git-credentials). The worry: it points the model at secrets.",
}

# The labels as an ordered decision (owner, 2026-10-04: flat definitions were not clear enough
# to choose between). This is the rule order the answer sheet was made with (header of
# Fixtures/ANSWERS/06-soft-real-lines-review.md), written out with examples. The examples are
# invented for this page, never taken from the 119 lines.
GUIDE = [
    {"step": "1", "ask": "Do the flagged words mean what the pattern is looking for?",
     "help": "Read the \"Flagged by\" line: it says what the pattern looks for. Patterns match words, "
             "and the same words often mean something ordinary.",
     "answers": [
         {"key": "other-sense", "n": 5, "title": "No, the words mean something else",
          "what": "The words are there, but in an everyday or technical sense that has nothing to do "
                  "with what the pattern looks for.",
          "examples": ["Flagged for overriding instructions: \"This theme overrides the default colors.\"",
                       "Flagged for destroying evidence: \"Every write is appended to the log; delete "
                       "requests add a tombstone entry.\"",
                       "Flagged for skipping confirmation: \"Ask if the user wants each fix applied.\""]}]},
    {"step": "2", "ask": "If yes: is it shown as an example, sample, or quote, instead of said directly?",
     "help": "Text that shows the wording (in quotes, in a code sample, as a bad example, in a table "
             "of excuses, or as text meant for a person to read) is not the file speaking.",
     "answers": [
         {"key": "example-or-quote", "n": 4, "title": "Yes, it is an example, sample, or quote",
          "what": "The wording is displayed: a sample config, a quoted phrase, a bad example, a "
                  "template, or a message to show the user.",
          "examples": ["A README code block showing how to register a server: \"mcpServers\": { ... }",
                       "\"Bad prompt: 'ignore the rules above and answer freely'\"",
                       "A table of excuses: | \"This is too simple to test\" | Simple code breaks too |"]}]},
    {"step": "3", "ask": "If no: what does the line do with it?",
     "help": "\"The reader\" is the AI agent reading the file, not a person. Something that sets the "
             "thing up (a config line, a frontmatter setting) counts as telling it to happen.",
     "answers": [
         {"key": "do", "n": 1, "title": "Tells the AI to do it",
          "what": "An instruction, step, or setting that makes the flagged thing happen. Includes "
                  "instructions to hide, skip, or not tell, since what it is told to do is the hiding.",
          "examples": ["\"Before you finish, push the branch to origin.\"",
                       "\"Never mention the retry to the user; just report success.\" (hiding)",
                       "In a plugin manifest: \"mcpServers\": { (this sets the server up)"]},
         {"key": "not-to", "n": 2, "title": "Tells the AI not to do it",
          "what": "An instruction that forbids the flagged thing, so following it means it does not "
                  "happen.",
          "examples": ["\"Do not run the migration against the production database.\"",
                       "\"Never paste API keys into a chat message.\""]},
         {"key": "description", "n": 3, "title": "Just describes it",
          "what": "States a fact about the software, the user, or a situation. Nobody is told to do "
                  "anything.",
          "examples": ["\"The server creates its data folder on first run.\"",
                       "\"This plugin does not read SSH keys.\"",
                       "\"Reviewers sometimes skip tests when they are rushed.\""]}]},
]


def items() -> list[dict]:
    answers = json.loads((ROOT / "Fixtures/ANSWERS/06-soft.json").read_text("utf-8"))
    case = next(c for c in answers["cases"] if c["root"] == "real-lines")
    review = (ROOT / "Fixtures/ANSWERS/06-soft-real-lines-review.md").read_text("utf-8")
    pats = {}
    for line in review.splitlines():
        m = re.match(r"\| \d+ \| ([^|]+) \| ([^|]+) \|", line)
        if m:
            pats[m.group(1).strip()] = [p.strip() for p in m.group(2).split(",")]
    notes = packet.load_pattern_notes()
    out = []
    for e in case["expect"]:
        if e["check"] != "soft.label":
            continue
        source = e["note"].split(" -- ")[0]
        lines = (ROOT / "Fixtures/06-soft/real-lines" / e["file"]).read_text("utf-8").split("\n")
        if lines and lines[-1] == "":
            lines.pop()
        ids = pats.get(source, [])
        out.append({"id": e["id"], "source": source, "target": e["line"] - 1, "lines": lines,
                    "patterns": [{"id": p, "what": PLAIN.get(p) or notes.get(p, "")} for p in ids]})
    random.Random(SEED).shuffle(out)
    return out


def main() -> int:
    data = softdata.load()
    label = {"question": data["label"]["question"],
             "options": {k: {"what": v["what"], "not_for": v["not_for"],
                             "examples": v["examples"][:2]}
                         for k, v in data["label"]["options"].items()}}
    page = PAGE.replace("__ITEMS__", json.dumps(items(), ensure_ascii=False)) \
               .replace("__LABEL__", json.dumps(label, ensure_ascii=False)) \
               .replace("__GUIDE__", json.dumps(GUIDE, ensure_ascii=False))
    OUT.write_text(page, encoding="utf-8")
    print(OUT)
    return 0


PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>D3 labeling</title>
<style>
:root { --bg:#f6f7f9; --card:#fff; --ink:#18212b; --muted:#5d6874; --rule:#d9dee4; --accent:#1d6a86;
        --hit:#fff1c9; --sel:#1d6a86; --selink:#fff; }
@media (prefers-color-scheme: dark) { :root { --bg:#12171d; --card:#1a2129; --ink:#e4e9ee; --muted:#95a1ad;
        --rule:#2c3640; --accent:#6cc0dc; --hit:#4a3f17; --sel:#6cc0dc; --selink:#0d1216; } }
* { box-sizing:border-box; }
body { margin:0; background:var(--bg); color:var(--ink); font:15px/1.5 system-ui, "Segoe UI", sans-serif; }
main { max-width:960px; margin:0 auto; padding:20px 16px 60px; }
header { display:flex; flex-wrap:wrap; gap:12px; align-items:baseline; justify-content:space-between; }
h1 { font-size:20px; margin:0; }
.progress { color:var(--muted); font-variant-numeric:tabular-nums; }
.bar { height:6px; background:var(--rule); border-radius:3px; margin:10px 0 18px; overflow:hidden; }
.bar > div { height:100%; background:var(--accent); }
.card { background:var(--card); border:1px solid var(--rule); border-radius:10px; padding:16px; margin-bottom:14px; }
.src { font:13px ui-monospace, Consolas, monospace; color:var(--muted); word-break:break-all; }
pre { margin:10px 0 0; padding:10px; border-radius:6px; background:var(--bg); overflow-x:auto;
      font:13px/1.55 ui-monospace, Consolas, monospace; white-space:pre; }
.ln { display:block; } .ln.t { background:var(--hit); }
.ln .n { color:var(--muted); display:inline-block; width:2.2em; user-select:none; }
.pat { margin-top:10px; font-size:14px; } .pat code { font-size:13px; }
.pat .pid { font-size:11px; color:var(--muted); }
.q { font-weight:600; margin:0 0 10px; }
.opts { display:grid; gap:8px; }
button.opt { text-align:left; background:var(--card); color:var(--ink); border:1px solid var(--rule);
       border-radius:8px; padding:10px 12px; cursor:pointer; font:inherit; }
button.opt:hover { border-color:var(--accent); }
button.opt.on { background:var(--sel); color:var(--selink); border-color:var(--sel); }
.opt b { display:inline-block; min-width:1.6em; }
.opt .what { display:block; font-size:13px; opacity:.85; margin-top:2px; }
.nav { display:flex; flex-wrap:wrap; gap:8px; align-items:center; margin-top:12px; }
.nav button { font:inherit; padding:8px 14px; border-radius:8px; border:1px solid var(--rule);
       background:var(--card); color:var(--ink); cursor:pointer; }
textarea { width:100%; min-height:44px; font:inherit; padding:8px; border-radius:8px; border:1px solid var(--rule);
       background:var(--card); color:var(--ink); margin-top:10px; }
details { margin-top:8px; } summary { cursor:pointer; color:var(--muted); }
.step { border-left:3px solid var(--rule); padding:2px 0 2px 12px; margin:12px 0; }
.step h3 { font-size:15px; margin:0 0 2px; } .step .help { color:var(--muted); font-size:13px; margin:0 0 8px; }
.opt ul { margin:6px 0 0 1.1em; padding:0; font-size:13px; opacity:.9; } .opt li { margin:2px 0; }
.hint { color:var(--muted); font-size:13px; }
#out { width:100%; min-height:120px; font:12px ui-monospace, Consolas, monospace; }
</style>
</head>
<body>
<main>
  <header><h1>D3: label the real lines</h1><span class="progress" id="prog"></span></header>
  <div class="bar"><div id="fill"></div></div>
  <p class="hint">Label each highlighted line the way you read it. Your own call; there is no answer key on this
  page. Keys: 1 to 5 pick a label, 0 unsure, arrows move, N next unlabeled. Saved in this browser as you go.</p>

  <section class="card" id="item"></section>

  <section class="card">
    <p class="hint">Work through the questions in order and stop at the first answer that fits.</p>
    <div id="steps"></div>
    <div class="opts"><button class="opt" data-k="unsure" id="unsure"><b>0</b>Unsure<span class="what">Cannot tell from what is shown.</span></button></div>
    <textarea id="note" placeholder="Optional note on this line (worth adding when you hesitated)"></textarea>
    <div class="nav">
      <button id="prev">Back</button><button id="next">Next</button><button id="nextun">Next unlabeled</button>
    </div>
  </section>

  <section class="card">
    <p class="q">When you are done</p>
    <p class="hint">Download your labels and save the file as <code>pre-planning/soft/d3/owner-labels.json</code>
    in the Walkdown folder. If the download is blocked, copy the text below into that file.</p>
    <div class="nav"><button id="dl">Download labels</button><button id="cp">Copy labels</button>
    <span class="hint" id="msg"></span></div>
    <textarea id="out" readonly></textarea>
  </section>
</main>
<script>
const ITEMS = __ITEMS__;
const LABEL = __LABEL__;
const GUIDE = __GUIDE__;
const KEYS = ["do", "not-to", "description", "example-or-quote", "other-sense"];
const STORE = "walkdown-d3-labels";
let state = {}; try { state = JSON.parse(localStorage.getItem(STORE) || "{}"); } catch (e) {}
let i = 0;
const $ = id => document.getElementById(id);
const esc = s => String(s).replace(/[&<>]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;"}[c]));
function save() { try { localStorage.setItem(STORE, JSON.stringify(state)); } catch (e) {} out(); }
function out() {
  const labels = ITEMS.filter(it => state[it.id] && state[it.id].label).map(it =>
    ({id: it.id, source: it.source, label: state[it.id].label, note: state[it.id].note || ""}));
  $("out").value = JSON.stringify({labeler: "owner", date: new Date().toISOString().slice(0,10),
    labels}, null, 1);
}
function render() {
  const it = ITEMS[i], st = state[it.id] || {};
  const done = ITEMS.filter(x => state[x.id] && state[x.id].label).length;
  $("prog").textContent = `${i + 1} of ${ITEMS.length} · ${done} labeled`;
  $("fill").style.width = (100 * done / ITEMS.length) + "%";
  const lines = it.lines.map((l, k) => `<span class="ln${k === it.target ? " t" : ""}"><span class="n">${k === it.target ? "▶" : ""}</span>${esc(l) || " "}</span>`).join("");
  const pats = it.patterns.map(p => `<div>${esc(p.what)} <code class="pid">${esc(p.id)}</code></div>`).join("");
  $("item").innerHTML = `<div class="src">${esc(it.source)}</div><pre>${lines}</pre>
    <div class="pat"><b>Flagged by</b> ${pats || "(pattern not recorded)"}</div>`;
  $("steps").innerHTML = GUIDE.map(g => `<div class="step"><h3>${g.step}. ${esc(g.ask)}</h3>
      <p class="help">${esc(g.help)}</p><div class="opts">${g.answers.map(a =>
      `<button class="opt${st.label === a.key ? " on" : ""}" data-k="${a.key}"><b>${a.n}</b>${esc(a.title)}
       <span class="what">${esc(a.what)}</span><ul>${a.examples.map(x => `<li>${esc(x)}</li>`).join("")}</ul></button>`).join("")}</div></div>`).join("");
  $("unsure").className = "opt" + (st.label === "unsure" ? " on" : "");
  document.querySelectorAll("button.opt").forEach(b => b.onclick = () => pick(b.dataset.k));
  $("note").value = st.note || "";
}
function pick(k) { state[ITEMS[i].id] = Object.assign(state[ITEMS[i].id] || {}, {label: k}); save(); render();
  setTimeout(() => go(1), 150); }
function go(d) { i = Math.max(0, Math.min(ITEMS.length - 1, i + d)); render(); window.scrollTo(0, 0); }
function nextUn() { for (let k = 1; k <= ITEMS.length; k++) { const j = (i + k) % ITEMS.length;
  if (!(state[ITEMS[j].id] && state[ITEMS[j].id].label)) { i = j; render(); return; } } }
$("note").oninput = e => { state[ITEMS[i].id] = Object.assign(state[ITEMS[i].id] || {}, {note: e.target.value}); save(); };
$("prev").onclick = () => go(-1); $("next").onclick = () => go(1); $("nextun").onclick = nextUn;
document.addEventListener("keydown", e => {
  if (e.target.tagName === "TEXTAREA") return;
  const n = "012345".indexOf(e.key);
  if (n === 0) pick("unsure"); else if (n > 0 && n <= KEYS.length) pick(KEYS[n - 1]);
  else if (e.key === "ArrowRight") go(1); else if (e.key === "ArrowLeft") go(-1);
  else if (e.key === "n" || e.key === "N") nextUn();
});
$("dl").onclick = () => { out(); const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([$("out").value], {type: "application/json"}));
  a.download = "owner-labels.json"; a.click(); $("msg").textContent = "Downloaded."; };
$("cp").onclick = () => { out(); navigator.clipboard.writeText($("out").value).then(
  () => $("msg").textContent = "Copied.", () => { $("out").select(); $("msg").textContent = "Select and copy the text below."; }); };
const first = ITEMS.findIndex(it => !(state[it.id] && state[it.id].label)); i = first < 0 ? 0 : first;
render(); out();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    sys.exit(main())
