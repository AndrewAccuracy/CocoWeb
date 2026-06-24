from __future__ import annotations

import unittest
from io import BytesIO

from PIL import Image

from security.secure_image_input import (
    SecurityValidationError,
    predict_image_safely,
    validate_and_open_image,
)


def make_png(width: int = 16, height: int = 16) -> BytesIO:
    buffer = BytesIO()
    Image.new("RGB", (width, height), color=(80, 120, 160)).save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


class SecureImageInputTests(unittest.TestCase):
    def test_accepts_valid_png_and_normalizes_rgb(self) -> None:
        safe = validate_and_open_image(make_png(), "sample.png")

        self.assertEqual(safe.detected_type, "png")
        self.assertEqual(safe.image.mode, "RGB")

    def test_rejects_path_traversal_filename(self) -> None:
        with self.assertRaises(SecurityValidationError):
            validate_and_open_image(make_png(), "../sample.png")

    def test_rejects_disallowed_extension(self) -> None:
        with self.assertRaises(SecurityValidationError):
            validate_and_open_image(make_png(), "sample.php")

    def test_rejects_fake_image_content(self) -> None:
        with self.assertRaises(SecurityValidationError):
            validate_and_open_image(BytesIO(b"<?php echo 1; ?>"), "sample.png")

    def test_rejects_oversized_declared_body(self) -> None:
        with self.assertRaises(SecurityValidationError):
            validate_and_open_image(
                make_png(),
                "sample.png",
                declared_size=6 * 1024 * 1024,
            )

    def test_prediction_hides_internal_errors(self) -> None:
        def broken_predict(_image):
            raise RuntimeError("internal model path: D:/secret/model.h5")

        response = predict_image_safely(make_png(), "sample.png", broken_predict)

        self.assertFalse(response["ok"])
        self.assertEqual(response["error"], "预测失败，请稍后重试。")


if __name__ == "__main__":
    unittest.main()

