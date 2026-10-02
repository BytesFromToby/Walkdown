3. **Present findings** — group issues by category. For each issue, show the task ID, description, and the specific problem.

4. **Fix with permission** — for each category, ask if the user wants to apply the suggested fixes. Use the UUIDs from the `task_list` response in step 1 for every `task_modify` / `task_doc_write` / `task_annotate` call — do not paraphrase or reuse UUIDs from earlier conversations. If you're unsure whether a UUID is still valid (e.g. after a long discussion), re-query with `task_info` before mutating.

## Guidelines
