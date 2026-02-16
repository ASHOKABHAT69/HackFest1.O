from __future__ import annotations

import math
import wave
from pathlib import Path

from audio_forensic_toolkit.webapp import _allowed_file, _analyze_upload_bytes, _build_index_html


def _write_sine(path: Path, freq: float = 180.0, rate: int = 16000, seconds: float = 1.2, amp: int = 12000) -> None:
    samples = []
    for n in range(int(rate * seconds)):
        value = int(amp * math.sin(2 * math.pi * freq * (n / rate)))
        samples.append(value)

    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(b"".join(int(s).to_bytes(2, "little", signed=True) for s in samples))


def test_index_template_contains_dropzone_text() -> None:
    html = _build_index_html().decode("utf-8")
    assert "Drop WAV file here" in html
    assert "/static/styles.css" in html


def test_allowed_file_validation() -> None:
    assert _allowed_file("sample.wav")
    assert not _allowed_file("sample.mp3")


def test_analyze_upload_returns_hybrid_report(tmp_path: Path) -> None:
    audio_file = tmp_path / "sample.wav"
    _write_sine(audio_file)

    payload = _analyze_upload_bytes(audio_file.read_bytes(), "sample.wav")

    assert "digital" in payload
    assert "biological" in payload
    assert 0.0 <= payload["overall_fraud_risk"] <= 1.0


def test_analyze_upload_rejects_non_wav() -> None:
    try:
        _analyze_upload_bytes(b"not-audio", "sample.mp3")
    except ValueError as err:
        assert "Unsupported format" in str(err)
    else:
        raise AssertionError("Expected ValueError for non-wav upload")
