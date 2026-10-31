# /// script
# requires-python = ">=3.10"
# dependencies = ["ddddocr==1.6.1", "Pillow>=10,<13"]
# ///
"""Local OCR candidates only; the caller must verify the server response.

Run: uv run --python 3.12 ocr_candidates.py captcha.png --beta --preprocess light
Reuse one OcrCandidates instance per serial worker. No challenge downloads,
network submissions, prompt input, model confidence scores or answer repair.
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

MAX_BYTES = 8 * 1024 * 1024
MAX_SIDE = 4096


def error_report(phase: str, exc: Exception) -> dict:
    return {
        "status": "environment_or_image_error",
        "candidates": [],
        "rejected": [],
        "server_verified": False,
        "diagnostics": [{"phase": phase, "error_type": type(exc).__name__,
                         "message": str(exc)[:400]}],
    }


def image_variants(image_bytes: bytes, light: bool) -> list[tuple[str, bytes]]:
    """Keep original bytes first; generate at most three mild offline variants."""
    from PIL import Image, ImageOps

    if not image_bytes or len(image_bytes) > MAX_BYTES:
        raise ValueError("Image must contain 1 to 8388608 bytes")
    with Image.open(io.BytesIO(image_bytes)) as opened:
        if max(opened.size) > MAX_SIDE:
            raise ValueError("Image side exceeds 4096 pixels")
        opened.load()
        if getattr(opened, "n_frames", 1) != 1:
            raise ValueError("Animated image needs explicit frame analysis")
        image = opened.copy()
    variants = [("original", image_bytes)]
    if not light:
        return variants

    def add(name: str, value) -> None:
        buf = io.BytesIO()
        value.save(buf, format="PNG")
        payload = buf.getvalue()
        if len(payload) <= MAX_BYTES and all(payload != b for _, b in variants):
            variants.append((name, payload))

    if "A" in image.getbands() or "transparency" in image.info:
        rgba = image.convert("RGBA")
        image = Image.alpha_composite(Image.new("RGBA", rgba.size, "white"), rgba)
        image = image.convert("RGB")
        add("alpha_white", image)
    gray = ImageOps.autocontrast(image.convert("L"))
    add("gray_contrast", gray)
    if max(gray.size) <= MAX_SIDE // 2:
        add("gray_2x", gray.resize((gray.width * 2, gray.height * 2),
                                   Image.Resampling.BICUBIC))
    return variants


class OcrCandidates:
    """Reuse CPU model instances; validate literal output without changing it."""

    def __init__(self) -> None:
        self._engines: dict[bool, object] = {}

    def _engine(self, beta: bool):
        if beta not in self._engines:
            import ddddocr
            self._engines[beta] = ddddocr.DdddOcr(
                show_ad=False, use_gpu=False, beta=beta
            )
        return self._engines[beta]

    def recognize(self, image_bytes: bytes, *, charset: str | None = None,
                  length: int | None = None, beta: bool = False,
                  preprocess: str = "none") -> dict:
        try:
            if charset is not None and not charset:
                raise ValueError("An explicit charset must not be empty")
            if length is not None and length < 1:
                raise ValueError("Length must be a positive integer")
            if preprocess not in {"none", "light"}:
                raise ValueError("Preprocess must be none or light")
            variants = image_variants(image_bytes, preprocess == "light")
        except Exception as exc:
            return error_report("image_or_configuration", exc)

        candidates: dict[str, dict] = {}
        rejected, diagnostics = [], []
        successful_calls = 0
        for model_beta in ((False, True) if beta else (False,)):
            model = "beta" if model_beta else "default"
            try:
                engine = self._engine(model_beta)
            except Exception as exc:
                diagnostics.extend(error_report("model_load:" + model, exc)["diagnostics"])
                continue
            for variant, data in variants:
                source = f"ddddocr/{model}:{variant}"
                try:
                    value = engine.classification(data)
                    if not isinstance(value, str):
                        raise TypeError("classification returned non-text; check package API")
                    successful_calls += 1
                except Exception as exc:
                    diagnostics.extend(error_report("recognition:" + source, exc)["diagnostics"])
                    continue

                reasons = []
                if not value:
                    reasons.append("empty")
                if length is not None and len(value) != length:
                    reasons.append("length_mismatch")
                if charset is not None and any(char not in charset for char in value):
                    reasons.append("charset_mismatch")
                if reasons:
                    rejected.append({"text": value, "source": source, "reasons": reasons})
                    continue
                # Do not strip, change case, replace lookalikes or remove characters.
                # set_ranges(int) differs across releases; literal post-validation also
                # avoids silently deleting unsupported symbols from a recognition result.
                item = candidates.setdefault(value, {"text": value, "sources": []})
                item["sources"].append(source)

        status = ("candidates_ready" if candidates else
                  "no_candidate" if successful_calls else "environment_or_image_error")
        return {"status": status, "candidates": list(candidates.values()),
                "rejected": rejected, "diagnostics": diagnostics,
                "successful_recognition_calls": successful_calls,
                "server_verified": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path, help="Local image file")
    parser.add_argument("--charset", help="Known allowed characters; no inferred default")
    parser.add_argument("--length", type=int, help="Known exact response length")
    parser.add_argument("--beta", action="store_true", help="Also try the second OCR model")
    parser.add_argument("--preprocess", choices=("none", "light"), default="none")
    args = parser.parse_args()
    try:
        if args.image.stat().st_size > MAX_BYTES:
            raise ValueError("Image exceeds 8388608 bytes")
        report = OcrCandidates().recognize(
            args.image.read_bytes(), charset=args.charset, length=args.length,
            beta=args.beta, preprocess=args.preprocess,
        )
    except Exception as exc:
        report = error_report("file_read", exc)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return {"candidates_ready": 0, "no_candidate": 2,
            "environment_or_image_error": 3}[report["status"]]


if __name__ == "__main__":
    sys.exit(main())
