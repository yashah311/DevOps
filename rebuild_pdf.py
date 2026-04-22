

import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from convert_to_gujarati import load_config, build_pdf, clean_text, _strip_llm_preamble

cfg = load_config()
out = Path(__file__).parent / "output"

# Build a lookup of known mode suffixes from config → human label
# e.g. {"JADANUVAAD": "Jadanuvaad", "BHAVANUVAD": "Bhavanuvad"}
mode_labels = {
    k.upper(): v.get("label", k)
    for k, v in cfg.get("translation_modes", {}).items()
}

files = list(out.glob("*_gujarati.txt"))
print(f"Found {len(files)} text file(s)")

for txt in sorted(files):
    stem = txt.stem          # e.g. "MyDoc_JADANUVAAD_gujarati"  or  "MyDoc_gujarati"

    # Detect if this is a mode-specific file (e.g. *_JADANUVAAD_gujarati.txt)
    matched = None
    for upper_key, label in mode_labels.items():
        suffix = f"_{upper_key}_gujarati"
        if stem.endswith(suffix):
            base = stem[: -len(suffix)]
            matched = (upper_key, label, base)
            break

    if matched:
        upper_key, label, base = matched
        pdf   = out / f"{base}_{upper_key}_OUTPUT.pdf"
        title = f"{base} — {label}"
    else:
        # Plain moodboard file: stem = "MyDoc_gujarati"
        base  = stem.replace("_gujarati", "")
        pdf   = out / (base + "_GUJARATI_OUTPUT.pdf")
        title = base

    raw = txt.read_text(encoding="utf-8")

    # Rewrite the .txt with the same cleanup that build_pdf applies
    cleaned = _strip_llm_preamble(clean_text(raw))
    if cleaned != raw:
        txt.write_text(cleaned, encoding="utf-8")
        print(f"  Cleaned: {txt.name}")

    try:
        is_literal = not bool(matched)  # no mode suffix = literal (default) output
        try:
            build_pdf(cfg, pdf, raw, title=title, preserve_newlines=is_literal)
        except Exception as e:
            if "TargetClosedError" in type(e).__name__ or "TargetClosedError" in str(e):
                print(f"  Chromium crash on first attempt — retrying in 4s...")
                time.sleep(4)
                build_pdf(cfg, pdf, raw, title=title, preserve_newlines=is_literal)
            else:
                raise
    except PermissionError:
        print(f"  SKIP: {pdf.name} is open in a PDF viewer — close it and re-run.")

    time.sleep(1)  # brief pause so Chromium temp dirs are fully cleaned up
