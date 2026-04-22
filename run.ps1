# ============================================================
#  run.ps1  —  One-click Gujarati PDF generator
#  Usage: just double-click OR  .\run.ps1  in PowerShell
# ============================================================

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# ── Force UTF-8 console so Gujarati filenames render correctly ──
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding  = [System.Text.Encoding]::UTF8
$env:PYTHONUTF8 = "1"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Gujarati PDF Generator" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ── 1. Check API keys based on style_config.yaml ───────────
$configPath = Join-Path $ScriptDir "style_config.yaml"
$configContent = Get-Content $configPath -Raw

# Detect OCR provider
$ocrProvider = "none"
if ($configContent -match 'provider:\s*"sarvam"') { $ocrProvider = "sarvam" }

# Detect LLM provider
$llmProvider = "none"
if ($configContent -match 'provider:\s*"groq"')   { $llmProvider = "groq" }
if ($configContent -match 'provider:\s*"gemini"') { $llmProvider = "gemini" }
if ($configContent -match 'provider:\s*"github"') { $llmProvider = "github" }

if ($ocrProvider -eq "sarvam" -and -not $env:SARVAM_API_KEY) {
    Write-Host "SARVAM_API_KEY is not set." -ForegroundColor Yellow
    Write-Host "  Sarvam Vision gives the BEST Indian-language OCR (Gujarati/Sanskrit)." -ForegroundColor Yellow
    Write-Host "  1. Sign up FREE at: https://dashboard.sarvam.ai" -ForegroundColor White
    Write-Host '  2. Run: $env:SARVAM_API_KEY = "your-key-here"' -ForegroundColor White
    Write-Host ""
    Read-Host "Press Enter to exit (set SARVAM_API_KEY first)"
    exit 1
} elseif ($ocrProvider -eq "sarvam") {
    Write-Host "Sarvam API key found. Indian-language OCR enabled." -ForegroundColor Green
}

if ($llmProvider -eq "groq" -and -not $env:GROQ_API_KEY) {
    Write-Host "GROQ_API_KEY is not set." -ForegroundColor Yellow
    Write-Host "  1. Go to https://console.groq.com (free, no billing needed)" -ForegroundColor White
    Write-Host "  2. API Keys -> Create API Key -> copy it" -ForegroundColor White
    Write-Host '  3. Run: $env:GROQ_API_KEY = "gsk_..."' -ForegroundColor White
    Write-Host ""
    Read-Host "Press Enter to exit (set GROQ_API_KEY first)"
    exit 1
} elseif ($llmProvider -eq "groq") {
    Write-Host "Groq API key found. LLM rewrite enabled." -ForegroundColor Green
}

# ── 3. Check input folder ───────────────────────────────────
$inputDir = Join-Path $ScriptDir "input"
if (-not (Test-Path $inputDir)) {
    New-Item -ItemType Directory -Path $inputDir | Out-Null
}
$pdfs = Get-ChildItem -Path $inputDir -Filter "*.pdf" |
        Where-Object { $_.Name -notlike "*_GUJARATI_OUTPUT*" }

if ($pdfs.Count -eq 0) {
    Write-Host "No PDFs found in the input/ folder." -ForegroundColor Red
    Write-Host "  Drop your scanned PDF(s) into:" -ForegroundColor Red
    Write-Host "  $inputDir" -ForegroundColor White
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Found $($pdfs.Count) PDF(s) to process:" -ForegroundColor Green
$pdfs | ForEach-Object { Write-Host "  - $($_.Name)" }
Write-Host ""

# ── 4. Run the Python script ────────────────────────────────
Write-Host "Starting conversion ..." -ForegroundColor Cyan
Write-Host ""

$pdfPaths = $pdfs | ForEach-Object { "`"$($_.FullName)`"" }
$cmd = "python `"$ScriptDir\convert_to_gujarati.py`" $($pdfPaths -join ' ')"
Invoke-Expression $cmd

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  All done! Check the output/ folder." -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "Something went wrong (exit code $LASTEXITCODE)." -ForegroundColor Red
}

Write-Host ""
Read-Host "Press Enter to close"
