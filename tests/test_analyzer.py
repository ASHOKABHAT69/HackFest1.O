from __future__ import annotations

import math
import wave
from pathlib import Path

from audio_forensic_toolkit.analyzer import analyze_biological_signature, analyze_digital_integrity, analyze_hybrid


def _write_sine(path: Path, freq: float = 180.0, rate: int = 16000, seconds: float = 2.0, amp: int = 12000) -> None:
    samples = []
    for n in range(int(rate * seconds)):
        value = int(amp * math.sin(2 * math.pi * freq * (n / rate)))
        samples.append(value)

    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(b"".join(int(s).to_bytes(2, "little", signed=True) for s in samples))


def test_digital_integrity_basics(tmp_path: Path) -> None:
    audio = tmp_path / "tone.wav"
    _write_sine(audio)

    report = analyze_digital_integrity(str(audio))

    assert report.sample_rate == 16000
    assert report.duration_seconds > 1.9
    assert len(report.sha256) == 64


def test_biological_signature_returns_scores(tmp_path: Path) -> None:
    audio = tmp_path / "tone.wav"
    _write_sine(audio)

    report = analyze_biological_signature(str(audio))

    assert 0.0 <= report.human_likeness <= 1.0
    assert report.zero_crossing_rate > 0


def test_hybrid_contains_combined_risk(tmp_path: Path) -> None:
    audio = tmp_path / "tone.wav"
    _write_sine(audio)

    report = analyze_hybrid(str(audio))

    assert 0.0 <= report.overall_fraud_risk <= 1.0
    assert report.digital.file_path.endswith("tone.wav")
