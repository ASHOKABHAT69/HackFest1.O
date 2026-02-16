# HackFest1.O — Audio Forensic Toolkit

The **Audio Forensic Toolkit** is a hybrid analysis engine for modern audio threats:

- AI-generated voice deepfakes
- Vishing (voice phishing) calls
- Tampered or low-integrity audio evidence

It combines:

1. **Digital Integrity** checks (file-level and waveform integrity)
2. **Biological Signature** checks (speech-like human acoustic behavior)

Then outputs a unified fraud-risk score for fast triage.

## ✨ New: Drag-and-Drop UI

You can now use the toolkit through a visual web interface:

- Drag and drop a `.wav` file
- Click **Analyze Audio**
- View an at-a-glance risk meter and detailed report sections
- Expand to inspect raw JSON output

This gives non-technical users a practical workflow without command-line usage.

## Features

### Digital Integrity Checks

- SHA-256 hashing for chain-of-custody workflows
- Sample-rate and container sanity checks
- Clipping ratio analysis
- Dynamic range profiling
- Metadata-style warning flags with risk weighting

### Biological Signature Checks

- Zero-crossing rate profile
- Frame energy variability (speech dynamics)
- Voiced segment ratio estimation
- Coarse pitch estimate from frame-level periodicity proxies
- Human-likeness scoring + anomaly flags

### Hybrid Output

- Unified JSON forensic report
- Overall fraud-risk score in `[0.0, 1.0]`

## Project Structure

```text
src/audio_forensic_toolkit/
  analyzer.py    # Hybrid + sub-analyzers
  cli.py         # Command-line entrypoint
  webapp.py      # Built-in stdlib HTTP UI backend
  templates/
    index.html   # Drag-and-drop UI
  static/
    styles.css
    app.js
tests/
  test_analyzer.py
  test_webapp.py
```

## Quick Start

### 1) Install

```bash
python -m pip install -e .
```

### 2) Launch visual UI (recommended)

```bash
audio-forensics-ui
```

Open: `http://localhost:8000`

> Current version supports **16-bit PCM WAV** files.

### 3) CLI mode (optional)

```bash
audio-forensics path/to/sample.wav --pretty
```

## Testing

```bash
PYTHONPATH=src python -m pytest -q
```

## Roadmap

- Add support for compressed codecs (MP3/AAC/Opus) via decoding pipeline
- Integrate spectro-temporal embeddings for speaker consistency and spoof detection
- Add metadata provenance adapters for telephony and messaging platforms
- Add report signing for forensic evidentiary workflows

## Disclaimer

This is a screening and triage tool, not a final legal authenticity verdict.
