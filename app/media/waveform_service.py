"""Small amplitude envelope from the PCM WAV produced by mock providers."""

import array
import sys
import wave
from pathlib import Path


def read_waveform(path: Path, points: int = 80) -> list[float]:
    with wave.open(str(path), "rb") as source:
        if source.getsampwidth() != 2:
            return []
        samples = array.array("h", source.readframes(source.getnframes()))
    if sys.byteorder != "little":
        samples.byteswap()
    step = max(1, len(samples) // points)
    return [
        max((abs(value) for value in samples[index : index + step]), default=0) / 32768
        for index in range(0, len(samples), step)
    ][:points]
