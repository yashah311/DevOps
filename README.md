# Gujarati PDF Generator

Converts scanned Sanskrit/Gujarati PDFs into clean translated PDFs using vision-LLM OCR + Groq/Gemini rewrite.

Produces up to 3 output modes per document:
- **Literal** — word-for-word translation
- **Sense** (ભાવાનુવાદ) — meaning-based translation
- **Summary** — condensed summary in Gujarati

---

## Quick Start

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Set API keys

**Windows PowerShell:**
```powershell
$env:GROQ_API_KEY = "gsk_..."          # Required — get free at console.groq.com
$env:SARVAM_API_KEY = "..."            # Optional — best Indian-language OCR
```

Or create a `.env` file (never commit this):
```
GROQ_API_KEY=gsk_...
SARVAM_API_KEY=...
```

### 3. Add your PDF

Drop scanned PDF(s) into the `input/` folder.

### 4. Run

**Windows (double-click or PowerShell):**
```powershell
.\run.ps1
```

**Direct Python:**
```bash
python convert_to_gujarati.py "input/my_document.pdf"
```

Output PDFs appear in `output/`.

---

## Project Structure

```
gujarati-pdf-generator/
├── convert_to_gujarati.py   # Main pipeline (OCR → LLM → PDF)
├── rebuild_pdf.py           # Re-render existing .txt files to PDF without re-running OCR/LLM
├── run.ps1                  # Windows one-click launcher
├── style_config.yaml        # All settings: fonts, margins, LLM model, translation modes
├── fonts/                   # Bundled Noto Gujarati fonts
├── requirements.txt
├── input/                   # Drop your PDFs here (gitignored)
└── output/                  # Generated PDFs appear here (gitignored)
```

---

## Configuration (`style_config.yaml`)

Key settings:

| Setting | Description |
|---|---|
| `ocr.provider` | `sarvam` (best) or `groq` (vision fallback) |
| `llm.provider` | `groq`, `gemini`, or `github` |
| `llm.model` | e.g. `meta-llama/llama-4-scout-17b-16e-instruct` |
| `pdf.font_size` | Body font size in pt |
| `pdf.margin_mm` | Page margin in mm |
| `translation_modes` | Define literal / sense / summary modes |

---

## Requirements

- Python 3.10+
- Windows / macOS / Linux
- Groq API key (free tier sufficient): https://console.groq.com
- Sarvam API key (optional, improves OCR): https://dashboard.sarvam.ai

---

## Rebuilding PDFs without re-translating

If you only want to adjust styling (fonts, margins, layout) without calling the LLM again:

```bash
python rebuild_pdf.py
```

This reads the cached `output/*_gujarati.txt` files and re-renders PDFs instantly.
