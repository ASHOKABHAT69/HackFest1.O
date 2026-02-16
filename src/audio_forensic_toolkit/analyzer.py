from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import math
import struct
import wave
from typing import Iterable


@dataclass
class DigitalIntegrityReport:
    file_path: str
    sha256: str
    sample_rate: int
    channels: int
    sample_width_bytes: int
    duration_seconds: float
    clipping_ratio: float
    dynamic_range_db: float
    metadata_flags: list[str]
    integrity_risk: float


@dataclass
class BiologicalSignatureReport:
    zero_crossing_rate: float
    energy_variation: float
    voiced_segment_ratio: float
    estimated_pitch_hz: float
    human_likeness: float
    biometric_flags: list[str]


@dataclass
class HybridForensicReport:
    digital: DigitalIntegrityReport
    biological: BiologicalSignatureReport
    overall_fraud_risk: float


def _chunks(seq: list[int], size: int) -> Iterable[list[int]]:
    for i in range(0, len(seq), size):
        chunk = seq[i : i + size]
        if len(chunk) == size:
            yield chunk


def _read_pcm_samples(path: Path) -> tuple[list[int], int, int, int]:
    with wave.open(str(path), "rb") as wf:
        n_channels = wf.getnchannels()
        sample_width = wf.getsampwidth()
        sample_rate = wf.getframerate()
        n_frames = wf.getnframes()
        frames = wf.readframes(n_frames)

    if sample_width != 2:
        raise ValueError("Only 16-bit PCM WAV files are currently supported.")

    fmt = "<" + "h" * (len(frames) // sample_width)
    interleaved = list(struct.unpack(fmt, frames))

    if n_channels > 1:
        mono = []
        for frame_idx in range(0, len(interleaved), n_channels):
            frame = interleaved[frame_idx : frame_idx + n_channels]
            mono.append(sum(frame) // len(frame))
    else:
        mono = interleaved

    return mono, sample_rate, n_channels, sample_width


def analyze_digital_integrity(path: str) -> DigitalIntegrityReport:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(path)

    raw = file_path.read_bytes()
    digest = sha256(raw).hexdigest()

    samples, sample_rate, channels, sample_width = _read_pcm_samples(file_path)
    duration = len(samples) / sample_rate if sample_rate else 0.0

    max_amp = 32767
    clipping = sum(1 for s in samples if abs(s) >= max_amp - 1)
    clipping_ratio = clipping / len(samples) if samples else 0.0

    peak = max((abs(s) for s in samples), default=1)
    rms = math.sqrt(sum(s * s for s in samples) / len(samples)) if samples else 1
    dynamic_range_db = 20 * math.log10(peak / max(rms, 1e-9))

    flags: list[str] = []
    risk = 0.0

    if clipping_ratio > 0.01:
        flags.append("High clipping ratio (>1%).")
        risk += 0.2
    if dynamic_range_db < 6.0:
        flags.append("Low dynamic range; may indicate generation artifacts.")
        risk += 0.25
    if sample_rate not in {8000, 16000, 22050, 32000, 44100, 48000}:
        flags.append("Uncommon sample rate.")
        risk += 0.15
    if duration < 1.0:
        flags.append("Very short utterance; difficult to authenticate.")
        risk += 0.1

    risk = min(risk, 1.0)

    return DigitalIntegrityReport(
        file_path=str(file_path),
        sha256=digest,
        sample_rate=sample_rate,
        channels=channels,
        sample_width_bytes=sample_width,
        duration_seconds=duration,
        clipping_ratio=clipping_ratio,
        dynamic_range_db=dynamic_range_db,
        metadata_flags=flags,
        integrity_risk=risk,
    )


def analyze_biological_signature(path: str, frame_ms: int = 20) -> BiologicalSignatureReport:
    samples, sample_rate, _, _ = _read_pcm_samples(Path(path))
    frame_len = max(1, int(sample_rate * frame_ms / 1000))

    energies: list[float] = []
    zcr_values: list[float] = []
    pitch_estimates: list[float] = []

    for frame in _chunks(samples, frame_len):
        energy = sum(s * s for s in frame) / len(frame)
        energies.append(energy)

        zero_crossings = 0
        for a, b in zip(frame, frame[1:]):
            if (a >= 0 > b) or (a < 0 <= b):
                zero_crossings += 1
        zcr = zero_crossings / max(len(frame) - 1, 1)
        zcr_values.append(zcr)

        if zero_crossings > 0:
            pitch = sample_rate / (2 * zero_crossings)
            pitch_estimates.append(pitch)

    if not energies:
        raise ValueError("Audio has no analyzable frames.")

    mean_energy = sum(energies) / len(energies)
    energy_var = sum((e - mean_energy) ** 2 for e in energies) / len(energies)
    energy_variation = math.sqrt(energy_var) / (mean_energy + 1e-9)

    mean_zcr = sum(zcr_values) / len(zcr_values)
    voiced_threshold = mean_energy * 0.4
    voiced_frames = sum(1 for e in energies if e > voiced_threshold)
    voiced_ratio = voiced_frames / len(energies)

    pitch_values = [p for p in pitch_estimates if 70 <= p <= 350]
    estimated_pitch = sum(pitch_values) / len(pitch_values) if pitch_values else 0.0

    flags: list[str] = []
    risk = 0.0

    if not (0.05 <= mean_zcr <= 0.25):
        flags.append("Atypical zero crossing profile for speech.")
        risk += 0.2
    if energy_variation < 0.15:
        flags.append("Overly uniform energy envelope.")
        risk += 0.25
    if voiced_ratio < 0.2:
        flags.append("Low voiced segment ratio.")
        risk += 0.2
    if estimated_pitch and not (80 <= estimated_pitch <= 300):
        flags.append("Pitch estimate outside common human speaking range.")
        risk += 0.2

    human_likeness = max(0.0, 1.0 - min(risk, 1.0))

    return BiologicalSignatureReport(
        zero_crossing_rate=mean_zcr,
        energy_variation=energy_variation,
        voiced_segment_ratio=voiced_ratio,
        estimated_pitch_hz=estimated_pitch,
        human_likeness=human_likeness,
        biometric_flags=flags,
    )


def analyze_hybrid(path: str) -> HybridForensicReport:
    digital = analyze_digital_integrity(path)
    biological = analyze_biological_signature(path)

    bio_risk = 1.0 - biological.human_likeness
    overall = min(1.0, 0.55 * digital.integrity_risk + 0.45 * bio_risk)

    return HybridForensicReport(
        digital=digital,
        biological=biological,
        overall_fraud_risk=overall,
    )
