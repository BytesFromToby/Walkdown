#!/usr/bin/env bash
set -e
cd /home/dana/projects/needs-repo
gh pr list --json title | jq '.[].title'
