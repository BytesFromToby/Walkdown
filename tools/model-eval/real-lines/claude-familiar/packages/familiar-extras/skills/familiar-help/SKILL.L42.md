| "add lore", "remember that..." | `familiar-lore` | Pass `add` with the entry text |
| "delete lore entry 2", "remove that last lore" | `familiar-lore` | Pass `delete` with the index number from the list |
| "reset lore", "clear your backstory", "forget everything" | `familiar-lore` | Pass `reset: true` |
| "start a focus timer", "pomodoro for 25 min", "set a timer for X on Y" | `familiar-focus` | action: `start`, pass `task` and optional `duration` in minutes |
| "how much time left", "check my focus timer" | `familiar-focus` | action: `check` |
