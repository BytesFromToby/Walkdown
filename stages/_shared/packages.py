"""The Python packages Walkdown imports. Spec: specs/shared.SPEC.md, packages.

One list, for the two places that need to know them: the front door, which checks that the interpreter it was started with
can import every core one before it runs anything (`walkdown.py`), and the account of a crashed step, which names a missing
import's module only when it is one of these (`steperror.py`): the name of a package of Walkdown's is a fix a person can make,
and any other module's name came from the repository or a message.
"""

# The import names of requirements.txt's packages, less pytest (no stage imports it): what every stage needs to run.
CORE_MODULES = ("yaml", "charset_normalizer", "pdfminer", "pypdf", "bs4", "lxml",
                "PIL", "regex", "confusable_homoglyphs", "detect_secrets", "zstandard")
# A stage imports these when they are there and does without them when they are not: the file-type detectors of the
# inventory, and the SDK of the sweep (requirements-soft.txt). The reader's OCR and HTML-render tools left with R35 and R36
# (2026-11-11), and pypdfium2 with the OCR of PDF pages.
OPTIONAL_MODULES = ("filetype", "magic", "typesafe_sdk")
OWN_MODULES = (*CORE_MODULES, *OPTIONAL_MODULES)
