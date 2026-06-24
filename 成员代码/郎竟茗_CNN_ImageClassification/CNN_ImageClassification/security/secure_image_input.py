"""Security helpers for CNN image-classification upload and inference.

This module hardens the image upload path before an uploaded file reaches the
model. It deliberately avoids saving user-controlled filenames to disk.
"""

from __future__ import annotations

import imghdr
import logging
import os
from dataclasses import dataclass
from io import BytesIO
from typing import BinaryIO, Callable, Iterable, Mapping, MutableMapping

from PIL import Image, UnidentifiedImageError


LOGGER = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}
ALLOWED_IMAGE_TYPES = {"jpeg", "png"}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_IMAGE_PIXELS = 10_000_000
MAX_WIDTH = 4096
MAX_HEIGHT = 4096

Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS


@dataclass(frozen=True)
class SafeImage:
    image: Image.Image
    detected_type: str
    original_filename: str
    size_bytes: int


class SecurityValidationError(ValueError):
    """Raised when an uploaded image violates the security policy."""

    def __init__(self, public_message: str, *, reason: str | None = None) -> None:
        super().__init__(public_message)
        self.public_message = public_message
        self.reason = reason or public_message


def _extension(filename: str) -> str:
    return os.path.splitext(filename or "")[1].lower().lstrip(".")


def _read_limited(file_obj: BinaryIO, max_bytes: int = MAX_UPLOAD_BYTES) -> bytes:
    data = file_obj.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise SecurityValidationError(
            "上传图片过大，请上传不超过 5MB 的图片。",
            reason="upload_size_exceeded",
        )
    if not data:
        raise SecurityValidationError("未接收到有效图片文件。", reason="empty_file")
    return data


def validate_and_open_image(
    file_obj: BinaryIO,
    filename: str,
    *,
    declared_size: int | None = None,
    allowed_extensions: Iterable[str] = ALLOWED_EXTENSIONS,
) -> SafeImage:
    """Validate an uploaded image and return a normalized RGB image.

    Args:
        file_obj: Binary stream from the upload framework.
        filename: Original client filename, used only for validation and logs.
        declared_size: Optional size from request headers. The stream is still
            read with a hard limit because headers are user-controlled.
        allowed_extensions: Extension allowlist.

    Raises:
        SecurityValidationError: if the upload violates the security policy.
    """

    if declared_size is not None and declared_size > MAX_UPLOAD_BYTES:
        raise SecurityValidationError(
            "上传图片过大，请上传不超过 5MB 的图片。",
            reason="declared_size_exceeded",
        )

    if any(part in (filename or "") for part in ("/", "\\", "..")):
        raise SecurityValidationError("文件名不合法。", reason="unsafe_filename")

    ext = _extension(filename)
    normalized_extensions = {item.lower().lstrip(".") for item in allowed_extensions}
    if ext not in normalized_extensions:
        raise SecurityValidationError(
            "仅支持 jpg、jpeg、png 格式图片。",
            reason="extension_not_allowed",
        )

    data = _read_limited(file_obj)
    detected_type = imghdr.what(None, data)
    if detected_type not in ALLOWED_IMAGE_TYPES:
        raise SecurityValidationError(
            "文件内容不是受支持的真实图片。",
            reason="content_type_not_allowed",
        )

    try:
        with Image.open(BytesIO(data)) as candidate:
            candidate.verify()
        with Image.open(BytesIO(data)) as verified:
            width, height = verified.size
            if width <= 0 or height <= 0 or width > MAX_WIDTH or height > MAX_HEIGHT:
                raise SecurityValidationError(
                    "图片尺寸超出允许范围。",
                    reason="image_dimensions_not_allowed",
                )
            normalized = verified.convert("RGB")
            normalized.load()
    except SecurityValidationError:
        raise
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise SecurityValidationError(
            "图片解析失败，请上传有效图片。",
            reason="image_decode_failed",
        ) from exc

    return SafeImage(
        image=normalized,
        detected_type=detected_type,
        original_filename=filename,
        size_bytes=len(data),
    )


def predict_image_safely(
    file_obj: BinaryIO,
    filename: str,
    model_predict: Callable[[Image.Image], object],
    *,
    declared_size: int | None = None,
) -> Mapping[str, object]:
    """Validate an upload, run model prediction, and return a safe response."""

    try:
        safe_image = validate_and_open_image(
            file_obj,
            filename,
            declared_size=declared_size,
        )
        prediction = model_predict(safe_image.image)
        return {
            "ok": True,
            "prediction": prediction,
            "image": {
                "type": safe_image.detected_type,
                "size_bytes": safe_image.size_bytes,
            },
        }
    except SecurityValidationError as exc:
        LOGGER.info("Rejected uploaded image: %s", exc.reason)
        return {"ok": False, "error": exc.public_message}
    except Exception:
        LOGGER.debug("Image prediction failed after validation")
        return {"ok": False, "error": "预测失败，请稍后重试。"}


def flask_json_response(payload: Mapping[str, object]) -> tuple[MutableMapping[str, object], int]:
    """Return a framework-neutral Flask-style JSON payload and status code."""

    status_code = 200 if payload.get("ok") is True else 400
    return dict(payload), status_code
