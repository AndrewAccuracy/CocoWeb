"""Example integration for a Flask CNN image-classification endpoint.

Copy the route pattern into the existing Flask app and connect `model_predict`
to the current model inference function. This file is intentionally small so
the security boundary remains in `secure_image_input.py`.
"""

from __future__ import annotations

from typing import Callable

from flask import Blueprint, jsonify, request
from PIL import Image

from .secure_image_input import flask_json_response, predict_image_safely


def create_secure_predict_blueprint(model_predict: Callable[[Image.Image], object]) -> Blueprint:
    blueprint = Blueprint("secure_predict", __name__)

    @blueprint.post("/predict-secure")
    def predict_secure():
        uploaded = request.files.get("file")
        if uploaded is None:
            return jsonify({"ok": False, "error": "请上传图片文件。"}), 400

        declared_size = request.content_length
        payload = predict_image_safely(
            uploaded.stream,
            uploaded.filename or "",
            model_predict,
            declared_size=declared_size,
        )
        body, status_code = flask_json_response(payload)
        return jsonify(body), status_code

    return blueprint

