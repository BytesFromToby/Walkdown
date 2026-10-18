"""Language shift within Latin script, by function words. Spec: specs/language.SPEC.md."""
from __future__ import annotations

import regex

MIN_WORDS = 5
MIN_WORDS_DIACRITIC = 12
MIN_WORDS_DIACRITIC_LINE = 6
MATCHED_MAX = 10
TEXT_MAX = 500

ENGLISH = set("""
a an the and or nor but if then than so as of to in on at by for from with without into onto
out up down over under about above below after before between through during against within
is are was were be been being am do does did done doing have has had having will would can
could should may might must shall not no yes it its it's this that these those there here
i me my mine you your yours we us our ours they them their theirs he him his she her hers
who whom whose which what when where why how all any each every some such only also just
very more most less much many few other another same both either neither own too again
once ever never always often still even well now one two first next last new
don't doesn't didn't isn't aren't wasn't won't can't couldn't shouldn't wouldn't you're
we're they're i'm let's that's there's here's what's
""".split())

# Function words per language. A word that is also English, or common in technical English
# text, is left out by name (spec, "Must never"); ENGLISH is subtracted again below.
_OTHER_RAW = {
    "es": "el la los las del que un una por para con se su sus al lo como más pero le ya este "
          "esta estos si porque muy sobre también hay donde cuando todo todos debe nunca usted "
          "siempre ahora después antes cada sólo solo luego",
    "pt": "de os da dos das que um uma para não na nas por mais se como mas ao ele isso seu sua "
          "ou quando muito já também só pelo pela até esta este você deve nunca sem sempre "
          "agora depois antes cada todos todas seus suas nem",
    "fr": "le la les des du un une est que qui dans pour pas sur avec ce cette il elle nous "
          "vous ils sont au aux mais ou comme tout ne se sa ses leur être fait jamais tous "
          "toujours après avant maintenant puis chaque votre",
    "de": "der das und ist nicht mit sie auf für ein eine zu den dem von sich auch werden "
          "wird bei oder wenn nur noch aus nach wie ich wir ihr im zum zur über dass sind "
          "kann muss soll niemals ohne sein seine alle immer jetzt dann vor dein deine",
    "it": "il lo la gli le di del della che un una con si da sono ma anche questo questa "
          "nel nella alla dei delle più se cui essere tutto quando perché solo molto mai al all "
          "allo ai senza suo sua tutti ogni sempre ora poi prima dopo",
    "nl": "de het een dat te voor met zijn niet aan er om ook als maar bij nog door naar dan "
          "wel uit worden wordt moet kan geen deze dit je ze nooit zonder alle altijd nu daarna "
          "eerst jouw",
    "sv": "du och att det som är på för med inte har till av om jag vi ni den ett kan ska eller "
          "från när så också aldrig utan alla alltid nu sedan innan efter dess din ditt",
    "pl": "na się nie do że jest jak ale po co tak za od już przez dla czy są może lub oraz "
          "jeśli tylko przy nigdy bez jego jej ich wszystkie wszystko zawsze teraz potem przed "
          "aby żeby bardzo",
    "tr": "ve bir bu da de için ile ne çok gibi daha ama olarak olan sonra kadar değil yok mi "
          "şu ya veya eğer ise asla tüm hemen şimdi sadece hiç önce bunu şunu",
    "id": "yang di ke dari ini itu untuk dengan tidak akan ada adalah pada juga atau kami "
          "kita anda saya bisa harus jika sudah belum oleh dalam karena jangan tanpa kepada "
          "semua setiap lalu kemudian sebelum setelah segera hanya selalu bahwa kamu telah",
    "ro": "de și la cu pe în din care este fără să nu sau dar mai după înainte toate tot "
          "întotdeauna acum apoi niciodată că",
    "cs": "na se je že jeho bez aby do jak ale ze by jsou nebo když jen také vždy "
          "nyní potom před všechny všechno nikdy tento tato toto",
    "sw": "kwa bila yote hii kwamba ni wa na ya katika hiyo hili kila lakini au sana kabla "
          "baada sasa kamwe",
}
OTHER = {lang: {w for w in words.split() if len(w) >= 2} - ENGLISH
         for lang, words in _OTHER_RAW.items()}

WORD = regex.compile(r"\p{Latin}+(?:'\p{Latin}+)?")
FENCE = regex.compile(r"^\s{0,3}(`{3,}|~{3,})")
STRIP = [regex.compile(p) for p in (
    r"`[^`]*`",                    # inline code
    r"\]\([^)]*\)",                # link targets
    r"[a-zA-Z][a-zA-Z0-9+.-]*://\S+",  # URLs
    r"<!--|-->",                   # comment markers (the comment's text is kept)
    r"<[^>]*>",                    # HTML tags
)]


def words_of(line: str) -> list[str]:
    s = line.replace("’", "'")
    for p in STRIP:
        s = p.sub(" ", s)
    return [w.lower() for w in WORD.findall(s)]


def score(words: list[str]) -> tuple[int, int, list[str]]:
    """(english, other, matched): other is the best single language, never a sum."""
    english = sum(1 for w in words if w in ENGLISH)
    best, matched = 0, []
    for vocab in OTHER.values():
        hits = [w for w in words if w in vocab]
        if len(hits) > best:
            best, matched = len(hits), hits
    return english, best, matched


def _function_rule(words):
    english, other, matched = score(words)
    hit = len(words) >= MIN_WORDS and len(set(matched)) >= 2 and other > english
    return hit, english, other, matched


def _diacritic_rule(words, english):
    if len(words) < MIN_WORDS_DIACRITIC or english * 20 >= len(words):
        return False
    accented = sum(1 for w in words if not w.isascii())
    return accented * 100 >= 15 * len(words)


def _diacritic_line_rule(words, english):
    if len(words) < MIN_WORDS_DIACRITIC_LINE or english:
        return False
    accented = sum(1 for w in words if not w.isascii())
    return accented * 100 >= 30 * len(words)


def _fenced(lines: list[str]) -> set[int]:
    """0-based indexes of fence lines and the lines inside closed fences. A fence that never
    closes hides nothing: the model reads the rest of the file either way."""
    out, start, fence = set(), None, None
    for i, line in enumerate(lines):
        m = FENCE.match(line)
        if fence is None:
            if m:
                start, fence = i, m.group(1)
        elif m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence):
            out.update(range(start, i + 1))
            fence = None
    return out


def paragraphs(lines: list[str], markdown: bool) -> list[list[tuple[int, str]]]:
    """Prose paragraphs as lists of (1-based line number, line)."""
    out, cur = [], []
    fenced = _fenced(lines) if markdown else set()
    for i, line in enumerate(lines, start=1):
        if i - 1 in fenced:
            if cur:
                out.append(cur)
                cur = []
            continue
        if line.strip():
            cur.append((i, line))
        elif cur:
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


def _unit(first, last, rule, words, english, other, matched):
    return {"line": first, "end_line": last, "rule": rule, "words": words,
            "english": english, "other": other, "matched": matched[:MATCHED_MAX]}


def passages(lines: list[str], markdown: bool) -> list[dict]:
    units = []
    for para in paragraphs(lines, markdown):
        per_line = [(n, words_of(text)) for n, text in para]
        ws = [w for _, lw in per_line for w in lw]
        hit, english, other, matched = _function_rule(ws)
        if hit:
            # cite only the lines that carry the other language: trim English lines at the ends
            keep = [i for i, (_, lw) in enumerate(per_line) if score(lw)[1]]
            span = per_line[keep[0]:keep[-1] + 1]
            ws = [w for _, lw in span for w in lw]
            english, other, matched = score(ws)
            units.append(_unit(span[0][0], span[-1][0], "function-words", len(ws), english,
                               other, matched))
            continue
        if _diacritic_rule(ws, english):
            units.append(_unit(para[0][0], para[-1][0], "diacritics", len(ws), english, other, []))
            continue
        for n, lw in per_line:
            hit, english, other, matched = _function_rule(lw)
            if hit and len(para) > 1:
                units.append(_unit(n, n, "function-words", len(lw), english, other, matched))
            elif _diacritic_line_rule(lw, english):
                units.append(_unit(n, n, "diacritics", len(lw), english, other, []))
    return units


def stats(lines: list[str], markdown: bool) -> dict:
    paras = paragraphs(lines, markdown)
    judged = sum(1 for p in paras if sum(len(words_of(t)) for _, t in p) >= MIN_WORDS)
    return {"paragraphs": len(paras), "judged": judged, "short": len(paras) - judged}


def language_findings(file: str, lines: list[str], markdown: bool,
                      line_based: bool = True) -> list[dict]:
    out = []
    for u in passages(lines, markdown):
        text = "\n".join(lines[u["line"] - 1:u["end_line"]])
        f = {"check": "read.language", "file": file,
             "line": u["line"] if line_based else None}
        if line_based:
            f["end_line"] = u["end_line"]
        else:
            f["text_line"], f["end_text_line"] = u["line"], u["end_line"]
        f.update({k: u[k] for k in ("rule", "words", "english", "other", "matched")})
        f["text"] = text[:TEXT_MAX]
        if len(text) > TEXT_MAX:
            f["truncated"] = True
        out.append(f)
    return out
