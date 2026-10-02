---
name: test-report
description: "Posts a summary of the latest test run to the team channel."
---

<!-- WALKDOWN FIXTURE :: stage 5 capability :: inert; hosts are .invalid; nothing runs. Expected results in Fixtures/ANSWERS/. Case: two legs (private data, external comms); no untrusted content. -->

# Test report

Use the reporter agent. It reads `test-output/summary.txt`, writes a three-line
summary, and runs `bash scripts/post.sh "<summary>"` to send it to the team channel.
