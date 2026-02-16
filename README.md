# HackFest1.O — Audio Forensic Toolkit

The **Audio Forensic Toolkit** is a hybrid analysis engine for modern audio threats:

- AI-generated voice deepfakes
- Vishing (voice phishing) calls
- Tampered or low-integrity audio evidence

It combines:

1. **Digital Integrity** checks (file-level and waveform integrity)
2. **Biological Signature** checks (speech-like human acoustic behavior)

Then outputs a unified fraud-risk score for fast triage.

## ✨ Drag-and-Drop UI

You can use the toolkit through a visual web interface:

- Drag and drop a `.wav` file
- Click **Analyze Audio**
- View an at-a-glance risk meter and detailed report sections
- Expand to inspect raw JSON output

This gives non-technical users a practical workflow without command-line usage.

## GitHub Pages Hosting (Supported)

Yes — this project is now hostable on **GitHub Pages** without removing current features.

How it works:
- GitHub Pages hosts the static UI from `docs/`.
- Analysis still runs on the existing Python backend (`audio-forensics-ui`) hosted elsewhere (Render, Fly.io, Railway, VM, etc.).
- In the UI, set **API Base URL** to your hosted backend (for example: `https://your-api.example.com`).

> Note: GitHub Pages cannot run Python server code directly, so the backend must be deployed separately.

### Deploy UI to GitHub Pages

1. Push repository to GitHub.
2. In **Settings → Pages**, choose **Deploy from branch**.
3. Select your branch and `/docs` folder.
4. Open your Pages URL.
5. Enter your backend URL into **API Base URL** and click **Save**.

The setting is stored in browser local storage. You can also set it using query params:

```text
https://<user>.github.io/<repo>/?api=https://your-api.example.com
```

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
    index.html   # Local server UI template
  static/
    styles.css
    app.js
docs/
  index.html     # GitHub Pages static UI
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

### 2) Launch local visual UI (recommended for local/dev)

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
