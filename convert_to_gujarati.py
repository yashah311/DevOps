"""
Scanned PDF -> Easy Gujarati PDF
Zero system dependencies (no Tesseract needed).
Providers (set in style_config.yaml):
  gemini  - Google Gemini Flash (FREE, just needs https://aistudio.google.com/apikey)
  github  - GitHub Models (fine-grained PAT with Models:Read scope)
  none    - Google Translate only (no key, lower quality)
"""
import os, sys, re, base64, io, time
from pathlib import Path
import yaml
import fitz
from PIL import Image
from openai import OpenAI
from reportlab.lib.pagesizes import A4, LETTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Force UTF-8 console output
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR    = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "style_config.yaml"

def load_config():
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)

def page_to_b64(page, dpi):
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    # Resize to max 2000px wide to keep tokens reasonable
    if img.width > 2000:
        ratio = 2000 / img.width
        img = img.resize((2000, int(img.height * ratio)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode()


def clean_text(text: str) -> str:
    """Strip Unicode Private Use Area characters that leak from LLM tokenisers,
    dot-leaders from OCR'd table-of-contents pages, and other artefacts.
    """
    import unicodedata

    # ── 1. Strip PUA characters ───────────────────────────────────
    cleaned = []
    for ch in text:
        cp = ord(ch)
        # Drop: BMP PUA (U+E000-U+F8FF), Supplementary PUA-A (U+F0000-U+FFFFF),
        #        Supplementary PUA-B (U+100000-U+10FFFF), and unassigned surrogates
        if (0xE000 <= cp <= 0xF8FF) or (0xF0000 <= cp <= 0xFFFFF) or \
           (0x100000 <= cp <= 0x10FFFF) or unicodedata.category(ch) == 'Cs':
            if cleaned and cleaned[-1] != ' ':
                cleaned.append(' ')
            continue
        cleaned.append(ch)
    result = ''.join(cleaned)

    # ── 2. Detect ToC lines first, then strip remaining dot-leaders ──────
    # A ToC line ends with a roman/arabic page number, with or without dot-leaders.
    # We mark these with U+2063 (INVISIBLE SEPARATOR) so build_pdf() can render
    # the page number flush right.  Two passes:
    #   Pass A — original source lines that still have dot-leaders
    #   Pass B — LLM output that already stripped the dot-leaders
    # Use lambdas so group() substitution works correctly (raw \1 in a non-raw
    # string is \x01, not a regex backreference).
    # Page numbers may be roman (xv), arabic (15), or Gujarati digits (૧૫)
    _PAGE_NUM_RE = r'([IVXLCDMivxlcdm]{2,8}|[0-9]{1,4}|[\u0ae6-\u0aef]{1,4})'
    _SEP = '\u2063'

    # Pass A: "text . . . xxv"  (2 or more dot-leaders)
    result = re.sub(
        r'(.{2,}?)\s*(?:[.\u00b7\u2022\u2027\u22c5]\s*){2,}\s*' + _PAGE_NUM_RE + r'\s*$',
        lambda m: m.group(1).rstrip() + _SEP + m.group(2),
        result,
        flags=re.MULTILINE,
    )
    # Pass B: "Gujarati text xxv"  (LLM already removed dot-leaders)
    # Only mark lines that don't already have U+2063 and end with a standalone
    # roman numeral (≥2 chars) or up to 4-digit number after whitespace.
    # Guard: skip short footnote-reference lines like "નોંધ ૩" or "IIIa, નોંધ ૧"
    # (≤ 30 chars containing the Gujarati word for "note").
    def _pass_b(m):
        full = m.group(0)
        if _SEP in full:
            return full
        if len(full.strip()) <= 30 and 'નોંધ' in full:
            return full   # footnote ref — don't mark as ToC
        return m.group(1).rstrip() + _SEP + m.group(2)
    result = re.sub(
        r'^(.{4,}?)\s+' + _PAGE_NUM_RE + r'\s*$',
        _pass_b,
        result,
        flags=re.MULTILINE,
    )
    # Pass C: Gujarati digits may be glued directly to the text (no space before them).
    # e.g. "...પ્રથમ પ્રયાસ૪૮"  or "...ભાગ ૧૩૩" (already caught by B, skipped here).
    def _pass_c(m):
        full = m.group(0)
        if _SEP in full:
            return full
        if len(full.strip()) <= 30 and 'નોંધ' in full:
            return full   # footnote ref — don't mark as ToC
        return m.group(1).rstrip() + _SEP + m.group(2)
    result = re.sub(
        r'^(.{4,}?)([\u0ae6-\u0aef]{1,4})\s*$',
        _pass_c,
        result,
        flags=re.MULTILINE,
    )
    # Strip any remaining dot-leaders not part of a ToC entry
    result = re.sub(r'(\s*[.\u00b7\u2022\u2027\u22c5]\s*){3,}', ' ', result)

    # ── 2b. Replace characters NotoSerifGujarati can't render ─────
    # Smart/curly quotes → straight quotes
    result = result.translate(str.maketrans('\u2018\u2019\u201c\u201d', "''\"\"" ))
    # Em-dash / en-dash → hyphen
    result = result.translate(str.maketrans('\u2014\u2013', '--'))
    # Dagger, double-dagger, bullet, ellipsis → simple equivalents
    result = result.translate(str.maketrans({'\u2020': '', '\u2021': '', '\u2022': '-', '\u2026': '...'}))
    # Thin/zero-width spaces and other invisible formatting chars
    result = re.sub(r'[\u200b\u200c\u200d\u00ad\ufeff]', '', result)

    # ── 3. Remove empty brackets/parens left after PUA stripping ──
    # e.g.  "( )"  "[]"  "(  )"  that held only PUA chars
    result = re.sub(r'\(\s*\)', '', result)
    result = re.sub(r'\[\s*\]', '', result)

    # ── 4. Collapse multiple spaces (but not newlines) ────────────
    result = re.sub(r'[ \t]{2,}', ' ', result)

    # ── 5. Drop lines that are purely noise after the above ───────
    lines = []
    for line in result.splitlines():
        stripped = line.strip()
        # Preserve markdown table rows and separator rows (contain '|') regardless of content
        if '|' in stripped:
            lines.append(line)
        # Skip lines made up only of whitespace/punctuation/digits (stray page numbers, rule lines)
        elif stripped and not re.fullmatch(r'[\s.,;:!?\-\u2013\u2014_/\\0-9\u200b\u200c\u200d]+', stripped):
            lines.append(line)
        else:
            lines.append('')   # keep blank lines as paragraph separators

    result = '\n'.join(lines)

    # ── 6. Strip characters from scripts NotoSerifGujarati can't render ──
    # Keep: ASCII (0x00-0x7F), Latin Extended (0x80-0x24F),
    #        Devanagari (0x900-0x97F) for Sanskrit shlokas,
    #        Gujarati (0xA80-0xAFF),
    #        General Punctuation + Symbols (0x2000-0x2BFF),
    #        Indic Number Forms (0xA830-0xA83F)
    ALLOWED = (
        (0x0000, 0x024F),   # ASCII + Latin Extended
        (0x0900, 0x097F),   # Devanagari (Sanskrit)
        (0x0A80, 0x0AFF),   # Gujarati
        (0x2000, 0x2BFF),   # General punctuation, arrows, math, etc.
        (0xA830, 0xA83F),   # Indic number forms
        (0xFB00, 0xFB4F),   # Alphabetic presentation forms (ligatures)
    )
    out_chars = []
    for ch in result:
        cp = ord(ch)
        if any(lo <= cp <= hi for lo, hi in ALLOWED):
            out_chars.append(ch)
        elif ch in '\n\r\t':
            out_chars.append(ch)
        else:
            # Replace with space to avoid word-merge, then collapse later
            if out_chars and out_chars[-1] != ' ':
                out_chars.append(' ')
    result = re.sub(r'[ \t]{2,}', ' ', ''.join(out_chars))

    # (Latin letters are now preserved — Playwright/Chromium handles font fallback
    #  for Latin/Roman numeral terms automatically.)

    return result


def build_page_prompt(cfg, page_num, total):
    """Vision prompt: LLM does OCR + Gujarati rewrite in one shot (used when ocr.provider=none)."""
    s        = cfg["style"]
    tone     = s.get("tone", "conversational")
    audience = s.get("audience", "general Gujarati speaker")
    domain   = s.get("domain", "general")
    preserve = ", ".join(s.get("preserve_terms", []))
    extra    = s.get("extra_instruction", "")
    return f"""This is page {page_num} of {total} from a scanned document.
Domain: {domain} | Tone: {tone} | Audience: {audience}

Step 1 - READ the scanned text carefully (it may be English, Sanskrit, Gujarati or mixed).
Step 2 - REWRITE it in natural, easy everyday Gujarati that {audience} can understand.
         Do NOT translate word-by-word. Write as if explaining clearly to a friend.
         Preserve terms as-is: {preserve}
         {extra}

CRITICAL: Output ONLY standard Unicode Gujarati script (U+0A80-U+0AFF range).
Do NOT output any placeholder characters, box characters, private-use characters,
or non-printable characters. Every word must be a real Gujarati word.
No English. No labels. No page numbers."""


def build_rewrite_prompt(cfg, raw_ocr_text, chunk_num, total_chunks, style_override=None):
    """Text-only prompt: LLM rewrites OCR text to Gujarati (used after Sarvam OCR).

    style_override — if provided (a translation_modes entry), its extra_instruction
    replaces the default task description, enabling Jadanuvaad / Bhavanuvad modes.
    domain and preserve_terms are always taken from the base style section.
    """
    base   = cfg["style"]
    s      = style_override if style_override is not None else base
    tone     = s.get("tone", "conversational")
    audience = s.get("audience", base.get("audience", "general Gujarati speaker"))
    domain   = base.get("domain", "general")              # always from base style
    preserve = ", ".join(base.get("preserve_terms", []))  # always from base style
    extra    = s.get("extra_instruction", "")

    if style_override is not None:
        # Mode-specific prompt — extra_instruction carries the full task description
        return f"""Below is OCR-extracted text (section {chunk_num} of {total_chunks}) from a {domain} document.
The text may be in English, Sanskrit, Gujarati or mixed scripts.

{extra}

- Preserve these terms exactly as-is (do not translate them): {preserve}
- Keep any structure (headings, lists, tables) in Markdown format.

CRITICAL: Output ONLY standard Unicode Gujarati (U+0A80–U+0AFF range).
No placeholder/box/private-use characters. No English output. No labels or page numbers.

OCR TEXT:
{raw_ocr_text}"""

    # Default moodboard prompt (unchanged)
    return f"""Below is OCR-extracted text (section {chunk_num} of {total_chunks}) from a {domain} document.
The text may be in English, Sanskrit, Gujarati or mixed scripts.

TASK: Rewrite this in natural, easy everyday Gujarati that {audience} can understand.
- Tone: {tone}. Do NOT translate word-by-word — write as if explaining clearly to a friend.
- Preserve these terms exactly as-is: {preserve}
- Keep any structure (headings, lists, tables) in Markdown format.
- {extra}

CRITICAL: Output ONLY standard Unicode Gujarati (U+0A80–U+0AFF range).
No placeholder/box/private-use characters. No English output. No labels or page numbers.

OCR TEXT TO REWRITE:
{raw_ocr_text}"""


def _parse_retry_delay(exc) -> float:
    """Extract retryDelay seconds from a 429 error body, default 60s."""
    try:
        body = exc.response.json() if hasattr(exc, 'response') else {}
        for item in body.get('error', {}).get('details', []):
            if 'retryDelay' in item:
                delay_str = item['retryDelay']  # e.g. "49s" or "49.96s"
                return float(re.sub(r'[^0-9.]', '', delay_str)) + 2
    except Exception:
        pass
    msg = str(exc)
    m = re.search(r'retry.*?(\d+\.?\d*)s', msg, re.IGNORECASE)
    return float(m.group(1)) + 2 if m else 62.0


def process_page_with_vision(client, model, prompt, b64_img, max_retries=4):
    for attempt in range(max_retries):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {
                            "url": f"data:image/jpeg;base64,{b64_img}",
                            "detail": "high"
                        }},
                    ],
                }],
                max_tokens=4096,
            )
            return _strip_llm_preamble(resp.choices[0].message.content.strip())
        except Exception as e:
            code = getattr(e, 'status_code', None) or getattr(getattr(e, 'response', None), 'status_code', None)
            if code == 429 and attempt < max_retries - 1:
                wait = _parse_retry_delay(e)
                print(f"\n    Rate limited. Waiting {wait:.0f}s before retry {attempt+2}/{max_retries} ...", flush=True)
                time.sleep(wait)
            else:
                raise



def _has_gujarati(s: str) -> bool:
    return any(0x0A80 <= ord(c) <= 0x0AFF for c in s)

def _has_gujarati_letters(s: str) -> bool:
    """True if s contains actual Gujarati LETTERS (not just digits U+0AE6-U+0AEF)."""
    return any((0x0A80 <= ord(c) <= 0x0AE5) or (0x0AF0 <= ord(c) <= 0x0AFF) for c in s)

def _has_indic(s: str) -> bool:
    """True if line contains Gujarati OR Devanagari (Sanskrit shlokas)."""
    return any((0x0A80 <= ord(c) <= 0x0AFF) or (0x0900 <= ord(c) <= 0x097F) for c in s)

def _has_indic_letters(s: str) -> bool:
    """Like _has_indic but ignores Gujarati digits — used for untranslated-English detection.
    Prevents lines like 'Story ૧ was ...' (Gujarati digit only) from being treated as
    translated Gujarati and slipping through the filter.
    """
    return _has_gujarati_letters(s) or any(0x0900 <= ord(c) <= 0x097F for c in s)

# LLM filler/commentary patterns
_FILLER_PATTERNS = re.compile(
    r'let me know|feel free|hope this (helps|is helpful)|if you (need|have)|'
    r'here is the (rewritten|translated|following|text)|'
    r'below is the|i have (rewritten|translated|kept|preserved|used|maintained)|'
    r"i've (rewritten|translated|kept|preserved)|"
    r'please (note|find below)|as requested|'
    r'note:\s*(this|the above|i)|'
    r'i have kept|preserv(ed|ing) the (exact |original )?terms|'
    r'scanned (with|by|using)',
    re.IGNORECASE,
)

# Gujarati self-commentary/preamble patterns — LLM explaining its own translation process.
# These lines never appear in real translated text; they are meta-commentary artifacts.
_GUJARATI_FILLER_RE = re.compile(
    r'અનુવાદ\s+કરત[ીઓ]\s+વખત'        # "અનુવાદ કરતી/કરતો વખતે" (while translating)
    r'|મૂળ\s+લખ.*?અનુવાદ'              # "મૂળ લખ... અનુવાદ" (original text... translation)
    r'|શબ્દોને\s+યાંત્રિક\s+રીત'       # "શબ્દોને યાંત્રિક રીતે" (mechanically following words)
    r'|ટ[િી]પ્પ[ણ].*?(?:ઓ|ઓ\s).*?(?:સ|ક)ર'  # "ટિપ્પણીઓ કરે/સમજ" (making comments)
    r'|(?:કેટ[લ]|અન્ય)\s*[ીઇ]?ક?\s*નો'  # "કેટલીક નૉ" / "અન્ય નો" (some/other notes)
    r'|મારી\s+પ્રાથ[િ]?મ[િ]?કતા'       # "મારી પ્રાથ(િ)મ(િ)કતા" (my priority)
    r'|વ[િ]?વ[િ]?ધ\s+સંસ્કર.*?વ.*?ચ.*?ન.*?ત[ફ]'  # various versions between/differences
    r'|(?:સ્[પ]ષ્ટ[ત]|વ[િ]ચ)[ા].*?જ[ળ]વ'  # clarity/preserving meaning
    ,
    re.IGNORECASE,
)

# OKEN / generic scanner watermark — matches both English and Gujarati variants:
# "OKEN scanner", "Scanned by OKEN", "સ્કેન કરવામાં આવ્યું OKEN સ્કેનર દ્વારા"
# "OKEN" is a scanner app brand name — it never appears legitimately in a translated text.
_SCANNER_WATERMARK_RE = re.compile(
    r'(?i)(oken\s*scan|scan(?:ned)?\s+(?:by|with|using)\s+oken|oken\s+scanner|\boken\b)',
)

# Bare page-number headings that OCR produces: ## xi / ## xii / ## 5 / ## ૧
# These are physical page numbers turned into markdown headings — pure noise.
_PAGE_NUM_HEADING_RE = re.compile(
    r'^#{1,3}\s*'
    r'(?:[IVXLCDMivxlcdm]{1,8}'    # Roman numerals
    r'|\d{1,4}'                      # Arabic digits
    r'|[\u0AE6-\u0AEF]{1,4}'        # Gujarati digits ૦-૯
    r')\s*$'
)

# Standalone label headings injected by the LLM: ## CONTENTS, ## TRANSLATION,
# ## અનુવાદ (= "translation" in Gujarati), ## ભાષાંતર, ## અર્થ
# Also catches LLM mode-label headings like ## જાદનુવાદ મોડ / શબ્દશઃ અનુવાદ
_LABEL_HEADING_RE = re.compile(
    r'^#{1,3}\s*'
    r'(?:CONTENTS?|TRANSLATION|INDEX|TABLE\s+OF\s+CONTENTS|LITERAL\s+TRANSLATION'
    r'|SENSE\s+TRANSLATION|SUMMARY\s+TRANSLATION|MEANING.BASED\s+TRANSLATION'
    r'|\u0A85\u0AA8\u0AC1\u0AB5\u0ABE\u0AA6'   # અનુવાદ
    r'|\u0AAD\u0ABE\u0AB7\u0ABE\u0A82\u0AA4\u0AB0'  # ભાષાંતર
    r'|\u0A85\u0AB0\u0ACD\u0AA5'                # અર્થ
    r'|\u0A9C\u0ABE\u0AA6\u0AA8\u0AC1\u0AB5\u0ABE\u0AA6'  # જાદનુવાદ
    r'|\u0AB6\u0AAC\u0ACD\u0AA6\u0AB6\u0A83'         # શબ્દશઃ
    r'|\u0AAE\u0ACB\u0AA1'                       # મોડ (mode)
    r'|\u0AAD\u0ABE\u0AB5\u0ABE\u0AA8\u0AC1\u0AB5\u0ABE\u0AA6'  # ભાવાનુવાદ
    r').*$',
    re.IGNORECASE,
)

# Plain (non-heading) LLM mode-label lines — same labels without ## prefix
# Also matches lines like "શબ્દશઃ / પંક્તિ-દર-પંક્તિ અનુવાદ - Literal Translation"
_MODE_LABEL_LINE_RE = re.compile(
    r'^(?:\u0A9C\u0ABE\u0AA6\u0AA8\u0AC1\u0AB5\u0ABE\u0AA6'  # જાદનુવાદ
    r'|\u0AB6\u0AAC\u0ACD\u0AA6\u0AB6\u0A83'                  # શબ્દશઃ
    r'|\u0AAD\u0ABE\u0AA8\u0AC1\u0AB5\u0ABE\u0AA6'            # ભાનુવાદ
    r'|\u0AAD\u0ABE\u0AB5\u0ABE\u0AA8\u0AC1\u0AB5\u0ABE\u0AA6'  # ભાવાનુવાદ
    r'|\u0AB8\u0ABE\u0AB0\u0ABE\u0A82\u0AB6'                  # સારાંશ
    r'|Literal\s+Translation|Sense\s+Translation|Summary|Meaning.Based\s+Translation'
    r')[\s/\-–|]*(?:\u0AAE\u0ACB\u0AA1|mode|.*?(?:Literal|Sense|Summary)\s+Translation)?\s*$',
    re.IGNORECASE,
)

# Running page headers from the original book, OCR'd and translated.
# Pattern: a SHORT line (≤80 chars) that STARTS with 2–8 roman numeral characters
# followed by a space and non-digit content, e.g. "xlviii Introduction: Part II"
# → translated as "xlviii પ્રિયઃ ભાગ II".  These are physical headers, not content.
_RUNNING_HEADER_RE = re.compile(
    r'^[IVXLCDMivxlcdm]{2,8}\s+\S.{0,70}$'
)

# English term → Gujarati script replacements
_TERM_REPLACEMENTS = [
    (re.compile(r'\bbrahmacharya\b', re.IGNORECASE), 'બ્રહ્મચર્ય'),
    (re.compile(r'\bshloka\b',       re.IGNORECASE), 'શ્લોક'),
    (re.compile(r'\bśloka\b',        re.IGNORECASE), 'શ્લોક'),
    (re.compile(r'\bsloka\b',        re.IGNORECASE), 'શ્લોક'),
]

# Devanagari → Gujarati character map.
# Applied when a line contains BOTH Devanagari and Gujarati — mixed-script LLM artifact.
_DEVA_TO_GUJ = str.maketrans(
    # Devanagari                Gujarati
    '\u0901\u0902\u0903'        # ँ ं ः  → ઁ ં ઃ
    '\u0905\u0906\u0907\u0908'  # अ आ इ ई → અ આ ઇ ઈ
    '\u0909\u090A'              # उ ऊ → ઉ ઊ
    '\u090F\u0910'              # ए ऐ → એ ઐ
    '\u0913\u0914'              # ओ औ → ઓ ઔ
    '\u0915\u0916\u0917\u0918\u0919'  # क ख ग घ ङ → ક ખ ગ ઘ ઙ
    '\u091A\u091B\u091C\u091D\u091E'  # च छ ज झ ञ → ચ છ જ ઝ ઞ
    '\u091F\u0920\u0921\u0922\u0923'  # ट ठ ड ढ ण → ટ ઠ ડ ઢ ણ
    '\u0924\u0925\u0926\u0927\u0928'  # त थ द ध न → ત થ દ ધ ન
    '\u092A\u092B\u092C\u092D\u092E'  # प फ ब भ म → પ ફ બ ભ મ
    '\u092F\u0930\u0932\u0935'        # य र ल व → ય ર લ વ
    '\u0936\u0937\u0938\u0939'        # श ष स ह → શ ષ સ હ
    '\u093C'                           # ़ nukta → ઼
    '\u093E\u093F\u0940'               # ा ि ी → ા િ ી
    '\u0941\u0942\u0943'               # ु ू ृ → ુ ૂ ૃ
    '\u0947\u0948'                     # े ै → ે ૈ
    '\u094B\u094C'                     # ो ौ → ો ૌ
    '\u094D',                          # ् virama → ્
    '\u0A81\u0A82\u0A83'
    '\u0A85\u0A86\u0A87\u0A88'
    '\u0A89\u0A8A'
    '\u0A8F\u0A90'
    '\u0A93\u0A94'
    '\u0A95\u0A96\u0A97\u0A98\u0A99'
    '\u0A9A\u0A9B\u0A9C\u0A9D\u0A9E'
    '\u0A9F\u0AA0\u0AA1\u0AA2\u0AA3'
    '\u0AA4\u0AA5\u0AA6\u0AA7\u0AA8'
    '\u0AAA\u0AAB\u0AAC\u0AAD\u0AAE'
    '\u0AAF\u0AB0\u0AB2\u0AB5'
    '\u0AB6\u0AB7\u0AB8\u0AB9'
    '\u0ABC'
    '\u0ABE\u0ABF\u0AC0'
    '\u0AC1\u0AC2\u0AC3'
    '\u0AC7\u0AC8'
    '\u0ACB\u0ACC'
    '\u0ACD',
)

def _transliterate_devanagari(text: str) -> str:
    """Map any Devanagari characters to their Gujarati equivalents.
    Only applied to lines that contain BOTH scripts (mixed-script LLM artifact)."""
    has_deva = any(0x0900 <= ord(c) <= 0x097F for c in text)
    has_guj  = any(0x0A80 <= ord(c) <= 0x0AFF for c in text)
    if has_deva and has_guj:
        return text.translate(_DEVA_TO_GUJ)
    return text

# ALL-CAPS English labels anywhere in a line: "PLAIN MEANING:", "TRANSLATION:", etc.
_ALLCAPS_LABEL_RE = re.compile(r'[A-Z][A-Z\s\-]{2,}:\s*')

# Parenthetical LLM instructions — applied as GLOBAL substitution BEFORE term replacement
# so catches all variants: (Shloka in Devanagari), (śloka), (Plain meaning in Gujarati)
_PAREN_INSTRUCTION_SUB = re.compile(
    r'\(\s*(?:plain\s+meaning(?:\s+in\s+\w+)?|'
    r'shloka(?:\s+in\s+\w+)?|s(?:h)?loka\s*|śloka\s*|'
    r'[^\s\)]{1,30}\s+in\s+devanagari|in\s+devanagari|in\s+gujarati\s*|'
    r'meaning\s+in\s+\w+|translation\s+below)\s*\)',
    re.IGNORECASE,
)

def _strip_latin_italic(m):
    """Keep *text* only if it contains non-Latin (Sanskrit/Gujarati); strip pure-Latin italic."""
    inner = m.group(1)
    return '' if all(ord(c) < 0x0300 for c in inner) else m.group(0)

def _strip_llm_preamble(text: str) -> str:
    """Remove boilerplate intro/outro and meta-commentary lines the LLM inserts."""

    # ── 0a. Strip parenthetical instructions BEFORE term replacement ──────────
    # Catches (Shloka in Devanagari), (śloka), (Plain meaning in Gujarati) etc.
    text = _PAREN_INSTRUCTION_SUB.sub('', text)

    # ── 0a2. Strip pure-Latin parenthetical scholarly annotations ────────────
    # e.g. "(latter a characteristically brahmanical notion)" — English editorial
    # comments inside parens that have NO Gujarati/Devanagari characters.
    def _drop_latin_paren(m):
        inner = m.group(1)
        has_indic = any(0x0900 <= ord(c) <= 0x0AFF for c in inner)
        return '' if not has_indic and len(inner.split()) >= 3 else m.group(0)
    text = re.sub(r'\(([^)]{10,200})\)', _drop_latin_paren, text)

    # ── 0a3. Strip Latin tails from mixed parens ─────────────────────────────
    # e.g. ("ઘર-પંડિત", latter a characteristically brahmanical notion)
    # → ("ઘર-પંડિત")  — keep Gujarati part, strip the English annotation tail.
    def _drop_latin_paren_tail(m):
        prefix = m.group(1)   # content up to the comma before the Latin tail
        tail   = m.group(2)   # the all-Latin tail
        close  = m.group(3)   # closing )
        has_indic = any(0x0900 <= ord(c) <= 0x0AFF for c in prefix)
        if has_indic:
            return '(' + prefix.rstrip(', ') + close
        return m.group(0)
    text = re.sub(r'\(([^)]{3,}?)(,\s*[a-z][a-zA-Z ,;\-]{8,})(\))', _drop_latin_paren_tail, text)

    # ── 0b. Term replacements (brahmacharya → બ્રહ્મચર્ય, etc.) ──────────────
    for pattern, replacement in _TERM_REPLACEMENTS:
        text = pattern.sub(replacement, text)

    # ── 0b2. Transliterate Devanagari → Gujarati on mixed-script lines ────────
    text = '\n'.join(_transliterate_devanagari(ln) for ln in text.splitlines())

    # ── 0c. Strip italic pure-Latin scholarly terms (*reductio ad absurdum*) ──
    text = re.sub(r'\*([a-z][a-z\s]{3,})\*', _strip_latin_italic, text)

    # ── 0d. Strip LLM-generated footnote markers ─────────────────────────────
    # $^1$, $^{12}$  → stripped (LaTeX superscript footnote references)
    text = re.sub(r'\$\^\{?\d+\}?\$', '', text)
    # [^1]: or [^1]  → strip the marker, keep the following text
    text = re.sub(r'^\[\^\d+\]:\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'\[\^\d+\]', '', text)
    # $V$, $VII$, $29$, $b$ etc. → the LLM wraps §-section refs in LaTeX $ delimiters.
    # Strip the $ wrappers, keeping the inner reference text.
    text = re.sub(r'\$([IVXLCDMivxlcdm]{1,8}[a-zA-Z]?|\d{1,3}[a-zA-Z]?|[a-zA-Z])\$',
                  r'§\1', text)

    lines = text.splitlines()

    # ── 1. Strip leading preamble (lines before first Gujarati/markdown content) ──
    # Bare page-num / label headings do NOT count as "content start" — skip over them.
    start = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            start = i + 1
            continue
        if _SCANNER_WATERMARK_RE.search(stripped):
            start = i + 1
            continue
        if _PAGE_NUM_HEADING_RE.match(stripped) or _LABEL_HEADING_RE.match(stripped):
            start = i + 1
            continue
        if _has_gujarati(stripped) or stripped.startswith(('#', '|', '-', '*')):
            start = i
            break
        start = i + 1

    # ── 2. Strip trailing boilerplate ────────────────────────────────────────
    end = len(lines)
    for i in range(len(lines) - 1, start - 1, -1):
        stripped = lines[i].strip()
        if not stripped:
            end = i
            continue
        if _has_gujarati(stripped):
            break
        if _FILLER_PATTERNS.search(stripped):
            end = i
        else:
            break

    lines = lines[start:end]

    # ── 3. Remove chunk-error lines ──────────────────────────────────────────
    lines = [l for l in lines if not re.match(r'^\[Chunk \d+ error:', l.strip())]

    # ── 4. Per-line cleanup ───────────────────────────────────────────────────
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            cleaned.append(line)
            continue

        # ── Universal artifact removal (language-independent) ─────────────────
        # Drop OKEN / scanner watermark lines regardless of script
        if _SCANNER_WATERMARK_RE.search(stripped):
            continue

        # Drop Gujarati LLM self-commentary (translator's notes about the process)
        if _GUJARATI_FILLER_RE.search(stripped):
            continue

        # Drop bare page-number headings: ## xi / ## 5 / ## ૧
        if _PAGE_NUM_HEADING_RE.match(stripped):
            continue

        # Drop standalone LLM label headings: ## CONTENTS, ## TRANSLATION, ## અનુવાદ
        if _LABEL_HEADING_RE.match(stripped):
            continue

        # Drop plain-line LLM mode labels (without ## prefix)
        # Also handles paren-wrapped variants: (શબ્દ: / ... - Literal Translation)
        _s_bare = stripped.strip('()').strip()
        if _MODE_LABEL_LINE_RE.match(stripped) or _MODE_LABEL_LINE_RE.match(_s_bare):
            continue
        # Catch any short line whose sole purpose is a mode stamp ending in
        # "- Literal Translation", "- Sense Translation", "- Summary" etc.
        # Works regardless of what precedes the dash.
        if len(stripped) <= 120 and re.search(
            r'[-–]\s*(Literal|Sense|Summary|Meaning.Based)\s+Translation\s*\)?$', stripped, re.IGNORECASE
        ):
            continue

        # Drop OCR running page headers: "xlviii Introduction: Part II" → short
        # line starting with roman numerals, clearly a book header not content.
        # Also catches ## xxxii <gujarati> where LLM turned a running header into a heading.
        _stripped_no_hashes = re.sub(r'^#+\s*', '', stripped)
        if _RUNNING_HEADER_RE.match(_stripped_no_hashes) and len(_stripped_no_hashes) <= 80:
            continue

        # Drop LLM prompt-echo lines — the model sometimes regurgitates instructions:
        # • "અનુવાદ કરવો નહીં" = "do not translate"
        # • "અનુવાદ કરેલો નથી" = "not translated"
        # • bare "###" with nothing after it (empty h3 used as a divider artifact)
        # • lines that are only a preserve-terms list "- આત્મા, ધર્મ, ..."
        if re.search(r'અનુવાદ\s+કરવો\s+નહ', stripped):
            continue
        if re.search(r'અનુવાદ\s+કરેલો\s+નથ', stripped):
            continue
        if re.match(r'^#{1,6}\s*$', stripped):   # bare ### / ## / # with no title
            continue
        # A line that is just a comma-separated list of Sanskrit preserve-terms
        # (no verb, no Gujarati sentence structure) — prompt echo artifact.
        if re.match(r'^[-*]?\s*(આત્મા|ધર્મ|કર્મ|સંસ્કાર|ગુરુ|મોક્ષ|બ્રહ્મચર્ય|શ્લોક)',
                    stripped):
            # Only drop if the line contains multiple comma-separated terms and
            # no sentence-ending verb indicator (keeps real content mentioning these)
            term_count = sum(1 for t in ['આત્મા','ધર્મ','કર્મ','સંસ્કાર','ગુરુ','મોક્ષ',
                                          'બ્રહ્મચર્ય','શ્લોક'] if t in stripped)
            if term_count >= 3 and stripped.count(',') >= 2:
                continue

        # Demote LLM footnote-ref headings to plain text.
        # Pattern: ## ૯. ૪, નોંધ ૮  — the LLM marks note references as ## headings.
        # Strip the ## prefix so they render as normal paragraph lines.
        if re.match(r'^#{1,3}\s*[\d\u0ae6-\u0aef]+\.', stripped):
            stripped = re.sub(r'^#+\s*', '', stripped)
            line = stripped

        # Drop spurious short pure-Gujarati headings invented by the LLM.
        # The LLM often lifts a 1-3 word phrase from a sentence and marks it ## .
        # Real section headings are longer or contain ASCII (Part, SR, MR, etc.).
        # Rule: ## / ### heading that is ≤ 30 chars with NO uppercase ASCII letters → drop.
        _heading_m = re.match(r'^(#{1,3})\s+(.+)$', stripped)
        if _heading_m:
            _htext = _heading_m.group(2).strip()
            _has_upper_ascii = any(c.isupper() and ord(c) < 128 for c in _htext)
            if len(_htext) <= 30 and not _has_upper_ascii:
                continue

        # Strip LLM-invented sequential list numbers from line starts.
        # e.g. "35. ૩૩, નોંધ ૫. ..." → "૩૩, નોંધ ૫. ..."
        # These are added by the LLM when it formats footnote prose as a numbered list.
        stripped = re.sub(r'^\d+\.\s+', '', stripped)
        line = stripped

        # Strip ALL-CAPS English labels from ANY line (even those with Gujarati)
        # e.g. "સPLAIN MEANING: " → "સ" (1 char) → drop
        if _ALLCAPS_LABEL_RE.search(stripped):
            remainder = _ALLCAPS_LABEL_RE.sub('', stripped).strip()
            if len(remainder) <= 2:   # fragment left after stripping — drop
                continue
            line = remainder
            stripped = remainder

        # Strip stray lowercase English words leaked by the LLM into Gujarati text.
        # e.g. "... કા deletedવા..." → "...કા વા..."  (word removed)
        # Keep: ALL-CAPS abbreviations (SR, MR, BBA), Title-Case proper nouns,
        #        single lowercase letters, roman numerals (ii, iii, iv, vi, vii…),
        #        words inside HTML tags (e.g. <br/> → don't strip "br")
        if _has_gujarati_letters(stripped):
            _new = re.sub(
                r'(?<![A-Z/<])\b([a-z][a-z]+)\b(?![/>])',   # 2+ lowercase Latin letters
                lambda m: m.group(0) if re.fullmatch(r'[ivxlcdm]+', m.group(0)) else '',
                stripped
            ).strip()
            if _new != stripped:
                line = _new
                stripped = _new

        # Drop parenthetical-only lines that are pure Gujarati (post-term-replacement leftovers)
        # e.g. "(શ્લોક)" — placeholder that survived because term replacement ran first
        paren_m = re.match(r'^\(([^)]{1,40})\)$', stripped)
        if paren_m:
            inner = paren_m.group(1).strip()
            if all((0x0A80 <= ord(c) <= 0x0AFF) or c.isspace() for c in inner):
                continue  # pure Gujarati-only in parens → placeholder, drop

        # Drop lines with no Gujarati LETTERS that are clearly LLM meta-commentary.
        # Note: use _has_gujarati_letters (not _has_gujarati) so lines containing
        # ONLY Gujarati digits (e.g. "Story ૫ was ...") still enter the filter.
        if not _has_gujarati_letters(stripped) and not stripped.startswith(('|',)):
            if _FILLER_PATTERNS.search(stripped):
                continue
            # Drop filler even inside headings: ## Here is the rewritten text...
            if stripped.startswith('#') and _FILLER_PATTERNS.search(re.sub(r'^#+\s*', '', stripped)):
                continue
            if re.match(r'^[-*]\s+', stripped) and _FILLER_PATTERNS.search(stripped):
                continue
            # Drop untranslated English sentences:
            # Use _has_indic_letters so lines containing only Gujarati DIGITS
            # (e.g. "Story ૧ of BR ...") are still treated as untranslated English.
            # Threshold: 3+ words (catches short fragments like "I shall not"),
            # >80% Latin alphabet characters.
            if not _has_indic_letters(stripped):
                words = stripped.split()
                latin_chars = sum(1 for c in stripped if c.isalpha() and ord(c) < 0x0300)
                total_alpha = sum(1 for c in stripped if c.isalpha())
                if total_alpha > 0 and latin_chars / total_alpha > 0.95:
                    # All-Latin line: drop even if just 1 word (e.g. "omissions.", "sound.")
                    continue
                if (len(words) >= 3 and total_alpha > 0
                        and latin_chars / total_alpha > 0.8):
                    continue

        cleaned.append(line)

    # ── 5. Deduplicate repeated lines within a sliding window ────────────────
    # The LLM sometimes emits the same section heading or sentence twice when
    # a chunk boundary falls mid-section.  Drop any non-trivial line that
    # appeared in the previous 20 lines (ignoring blank lines between them).
    deduped = []
    recent: list[str] = []   # last ≤20 non-empty stripped lines
    for line in cleaned:
        s = line.strip()
        if not s:
            deduped.append(line)
            continue
        # Only deduplicate substantial lines (>8 chars) to avoid dropping
        # short repeated structural lines like "---" or list bullets
        if len(s) > 8 and s in recent:
            continue   # exact duplicate within window — drop
        # Also drop short bare lines (≤25 chars) that are a substring of any
        # recent window line — catches LLM echo fragments like "શનિ ગ્રહ"
        # appearing as a standalone line after a paragraph that already contains it.
        if 6 <= len(s) <= 25 and any(s in r for r in recent):
            continue
        deduped.append(line)
        recent.append(s)
        if len(recent) > 20:
            recent.pop(0)

    # ── 6. Drop chunk-boundary sentence fragments ─────────────────────────────
    # A line that is a strict prefix of the very next non-empty line is a
    # truncated duplicate left by LLM chunk overlap — drop the fragment.
    final = []
    non_empty = [l.strip() for l in deduped if l.strip()]
    ne_idx = 0
    for line in deduped:
        s = line.strip()
        if not s:
            final.append(line)
            continue
        # Find next non-empty stripped line
        next_ne = non_empty[ne_idx + 1] if ne_idx + 1 < len(non_empty) else ''
        ne_idx += 1
        # Drop if this line (≥10 chars) is a prefix of the next non-empty line
        if len(s) >= 10 and next_ne.startswith(s) and len(next_ne) > len(s):
            continue
        final.append(line)

    return '\n'.join(final)


def rewrite_chunk_with_llm(client, model, prompt, max_retries=6):
    """Text-only LLM call for Gujarati rewrite after Sarvam OCR (no image)."""
    for attempt in range(max_retries):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4096,
            )
            return _strip_llm_preamble(resp.choices[0].message.content.strip())
        except Exception as e:
            code = getattr(e, 'status_code', None) or getattr(getattr(e, 'response', None), 'status_code', None)
            err_str = str(e).lower()
            is_connection = ('connection' in err_str or 'timeout' in err_str
                             or 'network' in err_str or 'remote' in err_str)
            if code == 429 and attempt < max_retries - 1:
                wait = _parse_retry_delay(e)
                print(f"\n    Rate limited. Waiting {wait:.0f}s before retry {attempt+2}/{max_retries} ...", flush=True)
                time.sleep(wait)
            elif is_connection and attempt < max_retries - 1:
                wait = min(5 * (attempt + 1), 30)   # 5s, 10s, 15s … up to 30s
                print(f"\n    Connection error. Retrying in {wait}s ({attempt+2}/{max_retries}) ...", flush=True)
                time.sleep(wait)
            else:
                raise


def _rewrite_chunks(cfg, chunks, client, model, out_dir, checkpoint_name, style_override=None):
    """Run LLM rewrite over all chunks, checkpointing after each one.

    Returns a list of translated strings (same length as chunks).
    style_override — if provided, passed through to build_rewrite_prompt() for
    Jadanuvaad / Bhavanuvad modes.
    """
    import json
    checkpoint_file = out_dir / checkpoint_name
    if checkpoint_file.exists():
        page_texts_out = json.loads(checkpoint_file.read_text(encoding="utf-8"))
        done = sum(1 for t in page_texts_out if t is not None and not str(t).startswith("[Chunk "))
        print(f"  Resuming from checkpoint ({checkpoint_name}): {done}/{len(chunks)} chunks done")
    else:
        page_texts_out = [None] * len(chunks)

    for i, chunk in enumerate(chunks):
        if page_texts_out[i] is not None and not str(page_texts_out[i]).startswith("[Chunk "):
            print(f"  Chunk {i+1}/{len(chunks)} ... skipped (cached)")
            continue
        if not chunk.strip():
            page_texts_out[i] = ""
            continue
        print(f"  Chunk {i+1}/{len(chunks)} ({len(chunk)} chars) ...", end=" ", flush=True)
        prompt = build_rewrite_prompt(cfg, chunk, i+1, len(chunks), style_override=style_override)
        if client:
            try:
                text = rewrite_chunk_with_llm(client, model, prompt)
                print(f"{len(text)} chars")
            except Exception as e:
                print(f"ERROR: {e}")
                text = f"[Chunk {i+1} error: {e}]"
        else:
            from deep_translator import GoogleTranslator
            print("Google Translate")
            text = GoogleTranslator(source="auto", target="gu").translate(chunk) or ""
        page_texts_out[i] = text
        checkpoint_file.write_text(json.dumps(page_texts_out, ensure_ascii=False), encoding="utf-8")

    return page_texts_out


def _save_mode_output(cfg, out_dir, stem, texts, txt_suffix, pdf_suffix, title, ocr_provider="sarvam", preserve_newlines=False):
    """Check for failures, write the .txt file, and render the PDF for one translation mode.

    Returns the Path of the written PDF.
    """
    import json
    label = "chunk" if ocr_provider == "sarvam" else "page"
    failed = [i + 1 for i, t in enumerate(texts)
              if t is None or (isinstance(t, str) and re.match(r'\[(Page|Chunk) \d', t))]
    if failed:
        print(f"  WARNING: {len(failed)} {label}(s) failed and will appear as placeholders: {failed}")
        print(f"  Re-run to fill them in (checkpoint saved).")
        for i in failed:
            if texts[i - 1] is None:
                texts[i - 1] = f"[વિભાગ {i} પ્રક્રિયા થઈ શકી નહીં - ફરી ચલાવો]"

    full_text = "\n\n".join(t for t in texts if t)
    # Apply the same cleanup to the .txt that build_pdf applies before rendering
    cleaned_text = _strip_llm_preamble(clean_text(full_text))
    guj_file  = out_dir / (stem + txt_suffix + ".txt")
    guj_file.write_text(cleaned_text, encoding="utf-8")
    print(f"  Text saved: {guj_file.name}")

    out_pdf = out_dir / (stem + pdf_suffix + ".pdf")
    build_pdf(cfg, out_pdf, full_text, title=title, preserve_newlines=preserve_newlines)
    return out_pdf


def ocr_pdf_with_sarvam(cfg, pdf_path, out_dir):
    """OCR the whole PDF with Sarvam Vision.

    Sarvam allows max 10 pages per job, so large PDFs are split into
    10-page chunks, each submitted as a separate job, then stitched together.

    Returns (raw_markdown: str, page_texts: list[str] | None).
    Caches the raw markdown to <stem>_sarvam_ocr.md so repeated runs skip the API call.
    """
    from sarvamai import SarvamAI
    import zipfile, json, tempfile

    SARVAM_PAGE_LIMIT = 10   # API hard limit

    ocr_cfg = cfg.get("ocr", {})
    api_key = os.environ.get(ocr_cfg.get("sarvam_token_env", "SARVAM_API_KEY"), "")
    if not api_key:
        print("ERROR: SARVAM_API_KEY not set.")
        print("  1. Sign up (free) at https://dashboard.sarvam.ai")
        print("  2. Copy your API key")
        print("  3. Run: $env:SARVAM_API_KEY = 'your-key-here'")
        sys.exit(1)

    language   = ocr_cfg.get("sarvam_language", "gu-IN")
    output_fmt = ocr_cfg.get("output_format", "md")

    # ── Cache: skip Sarvam API if already OCR'd ──────────────────
    cache_md   = out_dir / (pdf_path.stem + "_sarvam_ocr.md")
    cache_json = out_dir / (pdf_path.stem + "_sarvam_pages.json")

    if cache_md.exists():
        print(f"  Sarvam OCR cache found: {cache_md.name} — skipping API call")
        raw_md = cache_md.read_text(encoding="utf-8")
        page_texts = None
        if cache_json.exists():
            page_texts = json.loads(cache_json.read_text(encoding="utf-8"))
        return raw_md, page_texts

    # ── Split PDF into ≤10-page chunks ────────────────────────────
    src_doc   = fitz.open(str(pdf_path))
    total_pgs = len(src_doc)
    chunks    = []   # list of (start_page_0indexed, temp_pdf_path)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        if total_pgs <= SARVAM_PAGE_LIMIT:
            chunks = [(0, pdf_path)]   # no split needed
        else:
            print(f"  PDF has {total_pgs} pages — splitting into {SARVAM_PAGE_LIMIT}-page chunks ...", flush=True)
            for start in range(0, total_pgs, SARVAM_PAGE_LIMIT):
                end     = min(start + SARVAM_PAGE_LIMIT, total_pgs)
                chunk_p = tmpdir / f"chunk_{start:04d}.pdf"
                chunk_doc = fitz.open()
                chunk_doc.insert_pdf(src_doc, from_page=start, to_page=end - 1)
                chunk_doc.save(str(chunk_p))
                chunk_doc.close()
                chunks.append((start, chunk_p))
            print(f"  Created {len(chunks)} chunks", flush=True)

        src_doc.close()

        # ── Submit each chunk to Sarvam ───────────────────────────
        sv_client  = SarvamAI(api_subscription_key=api_key)
        all_md     = []
        all_pages  = []

        for chunk_idx, (page_offset, chunk_path) in enumerate(chunks):
            label = f"chunk {chunk_idx+1}/{len(chunks)}"
            print(f"  Sarvam OCR {label}: pages {page_offset+1}–{page_offset + SARVAM_PAGE_LIMIT} ...", flush=True)

            # Per-chunk cache to survive partial failures
            chunk_cache = out_dir / (pdf_path.stem + f"_sarvam_chunk{chunk_idx:03d}.md")
            chunk_json_cache = out_dir / (pdf_path.stem + f"_sarvam_chunk{chunk_idx:03d}.json")

            if chunk_cache.exists():
                print(f"    cached — skipping")
                chunk_md   = chunk_cache.read_text(encoding="utf-8")
                chunk_pages = None
                if chunk_json_cache.exists():
                    chunk_pages = json.loads(chunk_json_cache.read_text(encoding="utf-8"))
            else:
                try:
                    job = sv_client.document_intelligence.create_job(
                        language=language,
                        output_format=output_fmt,
                    )
                    job.upload_file(str(chunk_path))
                    job.start()
                    status = job.wait_until_complete()
                    print(f"    done: {status.job_state}", flush=True)
                except Exception as e:
                    status_code = getattr(e, 'status_code', None)
                    body        = getattr(e, 'body', {}) or {}
                    err_code    = (body.get('error') or {}).get('code', '')
                    if status_code == 429 or 'quota' in str(e).lower() or 'credits' in str(e).lower():
                        remaining = len(chunks) - chunk_idx
                        print(f"\n  *** Sarvam quota exhausted after chunk {chunk_idx}/{len(chunks)} ***")
                        print(f"  {remaining} chunk(s) still pending — they will be fetched on the next run.")
                        print(f"  Cached chunks are saved in output/ and will be skipped automatically.")
                        # Return partial results so the LLM rewrite can proceed on what we have
                        break
                    raise   # re-raise unexpected errors

                chunk_md    = ""
                chunk_pages = None
                with tempfile.TemporaryDirectory() as dl_tmp:
                    zip_path = Path(dl_tmp) / "out.zip"
                    job.download_output(str(zip_path))
                    with zipfile.ZipFile(str(zip_path)) as zf:
                        names     = zf.namelist()
                        md_files  = [n for n in names if n.lower().endswith('.md')]
                        json_files = [n for n in names if n.lower().endswith('.json')]
                        if md_files:
                            chunk_md = zf.read(md_files[0]).decode("utf-8")
                        if json_files:
                            try:
                                data  = json.loads(zf.read(json_files[0]).decode("utf-8"))
                                pages = None
                                if isinstance(data, list):
                                    pages = data
                                elif isinstance(data, dict):
                                    pages = (data.get("pages")
                                             or data.get("result", {}).get("pages")
                                             or [])
                                if pages:
                                    chunk_pages = [
                                        p.get("markdown") or p.get("text") or p.get("content") or ""
                                        for p in pages
                                    ]
                            except Exception as ex:
                                print(f"    Note: Could not parse Sarvam page JSON: {ex}")

                # Cache this chunk
                chunk_cache.write_text(chunk_md, encoding="utf-8")
                if chunk_pages is not None:
                    chunk_json_cache.write_text(json.dumps(chunk_pages, ensure_ascii=False), encoding="utf-8")

                # Small pause between jobs to avoid rate limits
                if chunk_idx < len(chunks) - 1:
                    time.sleep(2)

            all_md.append(chunk_md)
            if chunk_pages:
                all_pages.extend(chunk_pages)

    # ── Stitch results ────────────────────────────────────────────
    # Count how many chunks actually completed (have a cache file)
    completed_chunks = sum(
        1 for i in range(len(chunks))
        if (out_dir / (pdf_path.stem + f"_sarvam_chunk{i:03d}.md")).exists()
    )
    raw_md     = "\n\n".join(all_md)
    page_texts = all_pages if all_pages else None

    if completed_chunks == len(chunks):
        # All chunks done — write the final combined cache so next run skips OCR entirely
        cache_md.write_text(raw_md, encoding="utf-8")
        if page_texts is not None:
            cache_json.write_text(json.dumps(page_texts, ensure_ascii=False), encoding="utf-8")
        print(f"  OCR complete: {cache_md.name} ({len(raw_md)} chars, {len(page_texts or [])} pages)")
    else:
        print(f"  OCR partial: {completed_chunks}/{len(chunks)} chunks done — re-run to fetch remaining pages")

    return raw_md, page_texts

def build_pdf(cfg, output_path, gujarati_text, title, preserve_newlines=False):
    """Render PDF via Playwright/Chromium — proper HarfBuzz shaping for Gujarati/Indic scripts."""
    import markdown as md_lib
    from playwright.sync_api import sync_playwright

    gujarati_text = _strip_llm_preamble(clean_text(gujarati_text))
    pcfg       = cfg["pdf"]
    font_path  = BASE_DIR / cfg["paths"]["font"]
    bold_path  = font_path.parent / "NotoSerifGujarati-Bold-static.ttf"
    font_size  = pcfg.get("font_size_body", 12)
    title_size = pcfg.get("font_size_title", 18)
    leading    = pcfg.get("line_spacing", 22)
    marg_mm    = pcfg.get("margin_mm", 25)
    page_size  = pcfg.get("page_size", "A4").upper()

    # ── Convert markdown text to HTML ────────────────────────────
    # Step 0: Reconstruct proper <table> structure from orphaned <th>/<td> lines.
    # The LLM for literal mode outputs individual <td>/<th> lines instead of
    # markdown pipe tables. Convert them to markdown pipe table syntax so the
    # same `tables` extension that renders sense mode correctly handles them.
    _CELL_CONTENT_RE = re.compile(r'<t[hd][^>]*>(.*?)</t[hd]>', re.DOTALL | re.IGNORECASE)

    def _rebuild_tables(text):
        lines = text.split('\n')
        out = []
        i = 0
        while i < len(lines):
            ln = lines[i]
            s = ln.strip()
            if not (s.startswith('<th') or s.startswith('<td')):
                out.append(ln)
                i += 1
                continue

            # ── Collect the full run of consecutive cell lines ───────────
            th_cells = []
            td_cells = []
            j = i
            while j < len(lines) and (lines[j].strip().startswith('<th') or
                                       lines[j].strip().startswith('<td')):
                cell_line = lines[j].strip()
                m = _CELL_CONTENT_RE.search(cell_line)
                content = m.group(1).strip() if m else cell_line
                if cell_line.startswith('<th'):
                    th_cells.append(content)
                else:
                    td_cells.append(content)
                j += 1

            th_count = len(th_cells)
            td_count = len(td_cells)

            # Determine data columns: largest k ≤ th_count that evenly divides
            # td_count. Falls back to th_count when nothing divides evenly.
            if th_count > 0 and td_count > 0:
                data_cols = th_count
                for k in range(th_count, 0, -1):
                    if td_count % k == 0:
                        data_cols = k
                        break
            else:
                data_cols = th_count if th_count > 0 else 4

            # Trim or pad header cells to match data_cols
            header_cells = th_cells[:data_cols]
            while len(header_cells) < data_cols:
                header_cells.append('')

            def _esc(c):
                return c.replace('|', '&#124;')

            # ── Emit as markdown pipe table (same format sense mode uses) ──
            out.append('')  # blank line before table
            out.append('| ' + ' | '.join(_esc(h) for h in header_cells) + ' |')
            out.append('| ' + ' | '.join('---' for _ in header_cells) + ' |')
            for row_start in range(0, td_count, data_cols):
                row = td_cells[row_start:row_start + data_cols]
                while len(row) < data_cols:
                    row.append('')
                out.append('| ' + ' | '.join(_esc(c) for c in row) + ' |')
            out.append('')  # blank line after table

            i = j  # skip past collected cells

        return '\n'.join(out)

    gujarati_text = _rebuild_tables(gujarati_text)

    # Step 1: Convert U+2063-marked ToC lines to raw HTML blocks BEFORE markdown
    # sees them. Markdown passes <div> blocks through untouched, so the \u2063
    # marker never needs to survive markdown's internal processing.
    _TOC_LINE_RE = re.compile(
        r'^(.*?)\u2063([IVXLCDMivxlcdm0-9\u0ae6-\u0aef]{1,8})\s*$'
    )
    pre_lines = gujarati_text.split('\n')
    md_lines = []
    for ln in pre_lines:
        toc_m = _TOC_LINE_RE.match(ln.strip())
        if toc_m:
            text_part = toc_m.group(1).strip()
            page_part = toc_m.group(2)
            # Footnote reference lines (short + contains "નોંધ") must NOT be
            # right-aligned as ToC entries — strip the marker and output as plain text.
            full_visible = text_part + page_part
            if len(full_visible) <= 30 and 'નોંધ' in full_visible:
                md_lines.append(text_part + ' ' + page_part)
            else:
                md_lines.append(
                    f'<div class="toc-entry">'
                    f'<span class="toc-text">{text_part}</span>'
                    f'<span class="toc-page">{page_part}</span>'
                    f'</div>'
                )
        else:
            md_lines.append(ln)
    md_text = '\n'.join(md_lines)

    if preserve_newlines:
        # Convert every single newline to a markdown hard line break (two trailing
        # spaces + newline) so that the renderer keeps each line separate instead
        # of collapsing them into a single paragraph block.
        # Double newlines (paragraph breaks) are left untouched.
        # Skip lines that are raw HTML tags — adding trailing spaces would break them.
        def _add_hard_break(m):
            # Look back at the text before this newline to find the current line
            before = m.string[:m.start()]
            line_start = before.rfind('\n')
            current_line = before[line_start+1:] if line_start >= 0 else before
            stripped = current_line.strip()
            if stripped.startswith('<') and stripped.endswith('>'):
                return '\n'
            return '  \n'
        md_text = re.sub(r'(?<!\n)\n(?!\n)', _add_hard_break, md_text)
    body_html = md_lib.markdown(
        md_text,
        extensions=["tables", "sane_lists"],
    )

    # ── Build font-face declarations ─────────────────────────────
    font_uri      = font_path.resolve().as_uri()
    bold_font_uri = bold_path.resolve().as_uri() if bold_path.exists() else font_uri

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
@font-face {{
  font-family: 'NotoGuj';
  src: url('{font_uri}');
  font-weight: normal;
}}
@font-face {{
  font-family: 'NotoGuj';
  src: url('{bold_font_uri}');
  font-weight: bold;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  font-family: 'NotoGuj', 'Noto Serif', 'Times New Roman', serif;
  font-size: {font_size}pt;
  line-height: {leading / font_size:.2f};
  text-align: justify;
  color: #111;
}}
h1 {{
  font-size: {font_size + 5}pt;
  font-weight: bold;
  margin-top: 18pt;
  margin-bottom: 6pt;
  border-top: 1.2pt solid #555;
  border-bottom: 0.8pt solid #aaa;
  padding: 4pt 0;
}}
h2 {{
  font-size: {font_size + 3}pt;
  font-weight: bold;
  margin-top: 14pt;
  margin-bottom: 5pt;
  border-top: 1.2pt solid #555;
  border-bottom: 0.8pt solid #aaa;
  padding: 4pt 0;
}}
h3 {{
  font-size: {font_size + 1}pt;
  font-weight: bold;
  margin-top: 12pt;
  margin-bottom: 4pt;
  border-bottom: 0.8pt solid #aaa;
  padding-bottom: 3pt;
}}
h4, h5, h6 {{
  font-size: {font_size}pt;
  font-weight: bold;
  margin-top: 10pt;
  margin-bottom: 3pt;
}}
p.toc-entry, div.toc-entry {{
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  text-indent: 0;
  margin-bottom: 1pt;
}}
.toc-text {{
  flex: 1;
  overflow: hidden;
}}
.toc-page {{
  flex-shrink: 0;
  margin-left: 1em;
  min-width: 3em;
  text-align: right;
  font-variant-numeric: tabular-nums;
}}
p {{
  margin-bottom: {leading * 0.4:.1f}pt;
  text-indent: {font_size * 1.2:.1f}pt;
  text-align: justify;
}}
hr {{
  border: none;
  border-top: 0.8pt solid #aaa;
  margin: 6pt 0;
}}
table {{
  width: 100%;
  border-collapse: collapse;
  margin: 8pt 0;
  font-size: {font_size - 1}pt;
}}
th {{
  background: #e8e8e8;
  font-weight: bold;
  border: 0.5pt solid #bbb;
  padding: 4pt;
  text-align: left;
}}
td {{
  border: 0.5pt solid #bbb;
  padding: 4pt;
  text-align: left;
}}
tr:nth-child(even) td {{ background: #f5f5f5; }}
blockquote {{
  margin: 6pt 0 6pt 16pt;
  padding-left: 8pt;
  border-left: 2pt solid #ccc;
  font-style: italic;
}}
h1.doc-title {{
  font-size: {title_size}pt;
  text-align: center;
  border: none;
  margin-bottom: 12pt;
}}
</style>
</head>
<body>
<h1 class="doc-title">{title}</h1>
{body_html}
</body></html>"""

    # ── Render via Playwright/Chromium ────────────────────────────
    margin = f"{marg_mm}mm"
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page    = browser.new_page()
        page.set_content(html, wait_until="networkidle")
        page.pdf(
            path=str(output_path),
            format=page_size,
            margin={"top": margin, "bottom": margin, "left": margin, "right": margin},
            print_background=True,
        )
        browser.close()

    print(f"  PDF saved: {output_path.name}")


def make_client(cfg):
    """Build the OpenAI-compatible client based on provider setting."""
    lcfg     = cfg["llm"]
    provider = lcfg.get("provider", "none")
    if provider == "groq":
        token = os.environ.get(lcfg.get("groq_token_env", "GROQ_API_KEY"), "")
        if not token:
            print("ERROR: GROQ_API_KEY not set.")
            print("  1. Go to https://console.groq.com (free, no billing needed)")
            print("  2. API Keys -> Create API Key -> copy it")
            print("  3. Run: $env:GROQ_API_KEY = 'gsk_...'")
            sys.exit(1)
        endpoint = lcfg.get("groq_endpoint", "https://api.groq.com/openai/v1")
        model    = lcfg.get("groq_model", "meta-llama/llama-4-scout-17b-16e-instruct")
        return OpenAI(base_url=endpoint, api_key=token), model
    elif provider == "gemini":
        token = os.environ.get(lcfg.get("gemini_token_env", "GEMINI_API_KEY"), "")
        if not token:
            print("ERROR: GEMINI_API_KEY not set.")
            print("  1. Go to https://aistudio.google.com/apikey")
            print("  2. Click 'Create API key' (free, no billing needed)")
            print("  3. Run: $env:GEMINI_API_KEY = 'AIza...'")
            sys.exit(1)
        endpoint = lcfg.get("gemini_endpoint", "https://generativelanguage.googleapis.com/v1beta/openai/")
        model    = lcfg.get("gemini_model", "gemini-2.0-flash")
        return OpenAI(base_url=endpoint, api_key=token), model
    elif provider == "github":
        token = os.environ.get(lcfg.get("github_token_env", "GITHUB_TOKEN"), "")
        if not token:
            print("ERROR: GITHUB_TOKEN not set.")
            print("  Needs a fine-grained PAT with Models:Read scope.")
            print("  OR switch provider to 'gemini' in style_config.yaml (easier).")
            sys.exit(1)
        endpoint = lcfg.get("endpoint", "https://models.inference.ai.azure.com")
        model    = lcfg.get("model", "gpt-4o")
        return OpenAI(base_url=endpoint, api_key=token), model
    else:
        return None, None


def process_pdf(cfg, pdf_path):
    print(f"\n{'='*60}\nProcessing: {pdf_path.name}\n{'='*60}")
    provider     = cfg["llm"].get("provider", "none")
    ocr_provider = cfg.get("ocr", {}).get("provider", "none")
    client, model = make_client(cfg)
    dpi    = cfg["ocr"].get("dpi", 200)
    max_p  = cfg["limits"].get("max_pages", 60)
    out_dir = BASE_DIR / cfg["paths"]["output_folder"]
    out_dir.mkdir(parents=True, exist_ok=True)

    checkpoint_file = out_dir / (pdf_path.stem + "_checkpoint.json")
    import json

    # ════════════════════════════════════════════════════════════
    # PATH A — Sarvam Vision OCR + LLM text rewrite (two-step)
    # ════════════════════════════════════════════════════════════
    if ocr_provider == "sarvam":
        print(f"  Mode: Sarvam OCR → {provider} LLM rewrite  |  Model: {model or 'Google Translate'}")

        raw_md, page_texts = ocr_pdf_with_sarvam(cfg, pdf_path, out_dir)

        # Build chunk list: prefer page-level text from Sarvam JSON, else split markdown
        if page_texts and len(page_texts) > 0:
            chunks = page_texts[:max_p]
            print(f"  Using {len(chunks)} page-level chunks from Sarvam JSON")
        else:
            # Split the markdown into ~4000-char chunks on paragraph boundaries
            CHUNK_SIZE = 4000
            paragraphs = re.split(r'\n{2,}', raw_md)
            chunks, current = [], ""
            for para in paragraphs:
                if len(current) + len(para) + 2 > CHUNK_SIZE and current:
                    chunks.append(current.strip())
                    current = para
                else:
                    current += ("\n\n" if current else "") + para
            if current.strip():
                chunks.append(current.strip())
            chunks = chunks[:max_p]
            print(f"  Split markdown into {len(chunks)} chunks (~{CHUNK_SIZE} chars each)")

        # ── Moodboard (existing style) ────────────────────────────────────
        print(f"\n  [Moodboard rewrite]")
        moodboard_texts = _rewrite_chunks(
            cfg, chunks, client, model, out_dir,
            checkpoint_name=pdf_path.stem + "_checkpoint.json",
        )
        out_pdf = _save_mode_output(
            cfg, out_dir, pdf_path.stem, moodboard_texts,
            txt_suffix="_gujarati", pdf_suffix="_GUJARATI_OUTPUT",
            title=pdf_path.stem,
            preserve_newlines=True,
        )

        # ── Additional translation modes (Jadanuvaad, Bhavanuvad, …) ─────
        for mode_key, mode_cfg in cfg.get("translation_modes", {}).items():
            if not mode_cfg.get("enabled", True):
                continue
            mode_label = mode_cfg.get("label", mode_key)
            upper_key  = mode_key.upper()
            print(f"\n  [{mode_label} rewrite]")
            mode_texts = _rewrite_chunks(
                cfg, chunks, client, model, out_dir,
                checkpoint_name=pdf_path.stem + f"_{upper_key}_checkpoint.json",
                style_override=mode_cfg,
            )
            _save_mode_output(
                cfg, out_dir, pdf_path.stem, mode_texts,
                txt_suffix=f"_{upper_key}_gujarati",
                pdf_suffix=f"_{upper_key}_OUTPUT",
                title=f"{pdf_path.stem} — {mode_label}",
            )

        return out_pdf

    # ════════════════════════════════════════════════════════════
    # PATH B — LLM vision: OCR + rewrite in a single call (legacy)
    # ════════════════════════════════════════════════════════════
    else:
        doc   = fitz.open(str(pdf_path))
        total = min(len(doc), max_p)
        print(f"  Mode: LLM Vision (OCR+rewrite)  |  Pages: {total}  |  Provider: {provider}  |  Model: {model or 'Google Translate'}")

        if checkpoint_file.exists():
            page_texts_out = json.loads(checkpoint_file.read_text(encoding="utf-8"))
            print(f"  Resuming from checkpoint: {len(page_texts_out)}/{total} pages already done")
        else:
            page_texts_out = [None] * total

        for i in range(total):
            if page_texts_out[i] is not None and not page_texts_out[i].startswith("[Page "):
                print(f"  Page {i+1}/{total} ... skipped (cached)")
                continue
            print(f"  Page {i+1}/{total} ...", end=" ", flush=True)
            b64    = page_to_b64(doc[i], dpi)
            prompt = build_page_prompt(cfg, i+1, total)
            if client:
                try:
                    text = process_page_with_vision(client, model, prompt, b64)
                    print(f"{len(text)} chars")
                except Exception as e:
                    print(f"ERROR: {e}")
                    text = f"[Page {i+1} error: {e}]"
            else:
                from deep_translator import GoogleTranslator
                print("Google Translate (no vision)")
                text = GoogleTranslator(source="auto", target="gu").translate(prompt) or ""
            page_texts_out[i] = text
            checkpoint_file.write_text(json.dumps(page_texts_out, ensure_ascii=False), encoding="utf-8")
        doc.close()

    # ── Shared: check failures, save text, build PDF ─────────────
    failed = [i+1 for i, t in enumerate(page_texts_out)
              if t is None or (isinstance(t, str) and re.match(r'\[(Page|Chunk) \d', t))]
    if failed:
        label = "chunk" if ocr_provider == "sarvam" else "page"
        print(f"  WARNING: {len(failed)} {label}(s) failed and will appear as placeholders: {failed}")
        print(f"  Re-run to fill them in (checkpoint saved).")
        for i in failed:
            if page_texts_out[i-1] is None:
                page_texts_out[i-1] = f"[વિભાગ {i} પ્રક્રિયા થઈ શકી નહીં - ફરી ચલાવો]"

    full_text = "\n\n".join(t for t in page_texts_out if t)
    guj_file  = out_dir / (pdf_path.stem + "_gujarati.txt")
    guj_file.write_text(full_text, encoding="utf-8")
    print(f"  Gujarati text saved: {guj_file.name}")

    out_pdf = out_dir / (pdf_path.stem + "_GUJARATI_OUTPUT.pdf")
    build_pdf(cfg, out_pdf, full_text, title=pdf_path.stem, preserve_newlines=True)
    return out_pdf

def main():
    cfg      = load_config()
    font_chk = BASE_DIR / cfg["paths"]["font"]
    if not font_chk.exists():
        print(f"ERROR: Font not found: {font_chk}")
        sys.exit(1)
    in_dir = BASE_DIR / cfg["paths"]["input_folder"]
    pdfs   = [Path(p) for p in sys.argv[1:]]
    if not pdfs:
        in_dir.mkdir(parents=True, exist_ok=True)
        pdfs = [p for p in in_dir.glob("*.pdf") if "_GUJARATI_OUTPUT" not in p.name]
    if not pdfs:
        print(f"No PDFs in: {in_dir}")
        sys.exit(1)
    print(f"PDFs to process ({len(pdfs)}):")
    for p in pdfs:
        print(f"  - {p.name}")
    for pdf in pdfs:
        if not pdf.exists():
            print(f"SKIP: {pdf} not found")
            continue
        out = process_pdf(cfg, pdf)
        print(f"\nDone -> {out.name}")
    print("\nAll done! Check the output/ folder.")

if __name__ == "__main__":
    main()