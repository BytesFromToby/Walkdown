# Credits

Walkdown builds on other people's ideas, research, and tools. This page names them.

## Ideas

- **The lethal trifecta**, by Simon Willison. An agent that combines access to private data,
  exposure to untrusted content, and a way to communicate externally can be made to leak that
  data. Walkdown's "What this touches" step and the checklist at the top of every report are organized around it;
  the plain terms ("Can read your data", "Can take outside input", "Can send data out") are Walkdown's.
  [The lethal trifecta for AI agents](https://simonw.substack.com/p/the-lethal-trifecta-for-ai-agents)
- **Interpretable Context Methodology (ICM)**, by Jake Van Clief: context kept in inspectable
  files, organized as numbered steps that each have a written contract. Walkdown is laid out as
  an ICM workspace.

## Prior work on agent skill security

Walkdown's threat classes were compared against these, and the differences are recorded in
`pre-planning/THREATS.md`.

- **OWASP Agentic Skills Top 10** (AST01 to AST10).
  [owasp.org](https://owasp.org/www-project-agentic-skills-top-10/)
- **"Agent Skills in the Wild"**, an analysis of 31,132 published skills and the SkillScan tool.
  [arXiv 2601.10338](https://arxiv.org/abs/2601.10338)
- **safedep**, an eleven-class agent skills threat model, and the `vet` scanner.
  [Threat model](https://safedep.io/agent-skills-threat-model/),
  [safedep/vet](https://github.com/safedep/vet)
- **Red Hat**, agent skills threats and controls.
  [Article](https://developers.redhat.com/articles/2026/03/10/agent-skills-explore-security-threats-and-controls)
- **NVIDIA SkillSpector**, a scanner for agent skills, and an independent evaluation of it whose
  false-positive findings support two of Walkdown's rules (report capability, and count the
  benign hits). [nvidia/skillspector](https://github.com/nvidia/skillspector),
  [evaluation](https://towardsdatascience.com/from-green-checkmark-to-real-judgment-auditing-ai-agent-skills-with-skillspector/)
- **Cisco AI Defense skill-scanner**, run alongside Walkdown on a calibration audit for
  comparison. [cisco-ai-defense/skill-scanner](https://github.com/cisco-ai-defense/skill-scanner)

The real-world incidents the method is measured against (rules-file backdoors, malicious MCP
packages, coding-agent supply chain attacks, and others) are cited with their sources in
`pre-planning/INCIDENTS.md`.

## Test data

Short excerpts from three MIT-licensed repositories are used as labeled test lines for the model-read
measurements, kept under `tools/model-eval/`. The three repositories are named, and their licenses
reproduced, in [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md).

## Software

Required (`requirements.txt`):

| Package | License | Used for |
|---|---|---|
| PyYAML | MIT | the Library tables and the fixture data |
| charset-normalizer | MIT | detecting text encodings |
| pdfminer.six | MIT | reading PDF text |
| pypdf | BSD-3-Clause | reading PDF structure |
| beautifulsoup4 | MIT | reading HTML |
| lxml | BSD-3-Clause | parsing HTML and XML |
| Pillow | MIT-CMU | reading images and their metadata |
| regex | Apache-2.0 | the phrase patterns |
| confusable_homoglyphs | MIT | finding look-alike characters |
| pytest | MIT | the test suite |
| detect-secrets | Apache-2.0 | finding committed secrets |
| zstandard | BSD-3-Clause | reading zstd archives |

Optional, used when installed:


Optional model reads, chosen at run time (`requirements-soft.txt`):

- **Jev** by TypeSafe (`typesafe-sdk`, MIT): the coverage sweep (`--sweep jev`). Before 0.4.0 it also
  did the labeling.
  [docs.typesafe.ai](https://docs.typesafe.ai)
- **Claude Code CLI** by Anthropic: the pinpoint read (`--pinpoint claude-cli`), run with no tools and
  no project context. Before 0.4.0 it also did the relational reads.

Used before 0.4.0 and no longer part of Walkdown:

- **Laya** by Convai Innovations (`laya`, Apache-2.0, with PyTorch): a small local labeler. It was
  evaluated and retired (2026-10-03), and its backend code was removed in 0.4.0.
  [convaiinnovations/laya](https://huggingface.co/convaiinnovations/laya)
