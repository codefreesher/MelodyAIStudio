"""Deterministic local demo outputs, explicitly not real AI generation."""

import math
import struct
import threading
import wave
import zlib
from pathlib import Path

from app.models.generation import Generation


def png(path: Path, width: int, height: int, variant: int) -> None:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack("!I", len(data)) + kind + data + struct.pack("!I", zlib.crc32(kind + data))

    rows = bytearray()
    for y in range(height):
        rows.append(0)
        for x in range(width):
            rows.extend((255, int(140 + 95 * y / height), int(170 + 60 * x / width) - variant * 5))
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack("!2I5B", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(bytes(rows)))
        + chunk(b"IEND", b"")
    )


class MockCreativeProvider:
    kind = "lyric"

    def generate(self, prompt: str, options: dict, folder: Path, cancel: threading.Event) -> Generation:
        for _ in range(20):
            if cancel.wait(0.1):
                raise ValueError("Đã hủy tác vụ.")
        folder.mkdir(parents=True, exist_ok=True)
        result = Generation(
            folder.name,
            self.kind,
            prompt.strip()[:60],
            prompt,
            [],
            metadata={"options": options, "demo": True},
        )
        if self.kind == "lyric":
            for index in range(int(options.get("count", 1))):
                path = folder / f"lyric-{index + 1}.txt"
                path.write_text(
                    f"[Bản demo {index + 1}]\nChủ đề: {prompt}\n\n[Verse]\nNgày mới mang theo một giấc mơ\nGiai điệu nhẹ ru những mong chờ\n\n[Chorus]\nCùng hát lên câu chuyện của ta\nĐể yêu thương bay thật xa\n",
                    encoding="utf-8",
                )
                result.paths.append(path)
        elif self.kind == "image":
            ratio = options.get("ratio", "1:1").split(":")
            w, h = map(int, ratio)
            width, height = (768, int(768 * h / w)) if w >= h else (int(768 * w / h), 768)
            for index in range(int(options.get("count", 1))):
                if cancel.is_set():
                    raise ValueError("Đã hủy tác vụ.")
                path = folder / f"image-{index + 1}.png"
                png(path, width, height, index)
                result.paths.append(path)
        else:
            path = folder / "demo.wav"
            duration = min(30, max(2, int(options.get("duration", 6))))
            rate = 22050
            with wave.open(str(path), "wb") as output:
                output.setnchannels(1)
                output.setsampwidth(2)
                output.setframerate(rate)
                for second in range(duration):
                    if cancel.is_set():
                        raise ValueError("Đã hủy tác vụ.")
                    frequency = [261.63, 329.63, 392, 523.25][second % 4]
                    samples = bytearray()
                    for sample in range(rate):
                        fade = min(1, sample / 1100, (rate - sample) / 1100)
                        value = int(5500 * fade * math.sin(2 * math.pi * frequency * sample / rate))
                        samples.extend(struct.pack("<h", value))
                    output.writeframes(samples)
            result.paths.append(path)
            if self.kind == "music" and options.get("extra"):
                lyric = folder / "accompanying-lyric.txt"
                lyric.write_text(
                    f"[Demo lyric]\n{prompt}\nMột giai điệu mới, một ngày bình yên.\n", encoding="utf-8"
                )
                result.paths.append(lyric)
            result.metadata["duration"] = duration
            result.metadata["notice"] = "Audio demo dạng giai điệu, không phải giọng nói AI."
        return result


class MockMusicProvider(MockCreativeProvider):
    kind = "music"


class MockTextProvider(MockCreativeProvider):
    kind = "lyric"


class MockTTSProvider(MockCreativeProvider):
    kind = "audio"


class MockImageProvider(MockCreativeProvider):
    kind = "image"
