```bash
# WALKDOWN FIXTURE :: class 18 (NEGATIVE) :: inert.
# This .md file OPENS with a fenced code block, which makes `file` (libmagic)
# misclassify it as JavaScript/shell. That is detector NOISE, not an attack.
# The extension-vs-magic metric must ship with this false-positive baseline.
echo "hello"
```

# Ordinary document

This is a normal Markdown file. It just happens to start with a code fence, which
is exactly the case that produced 5 false "JavaScript" hits on superpowers
(FABLENOTES). Must NOT be treated as an extension-vs-content attack.
