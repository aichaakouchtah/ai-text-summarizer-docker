"""Flask API for BART-based text summarization."""

import logging
import os
from numbers import Integral

from flask import Flask, jsonify, request
from werkzeug.exceptions import BadRequest, RequestEntityTooLarge

MODEL_NAME = "facebook/bart-large-cnn"
MIN_WORDS = 30
MIN_SUMMARY_LENGTH = 10
MAX_SUMMARY_LENGTH = 500
MAX_INPUT_TOKENS = 1024
MAX_REQUEST_BYTES = 1 * 1024 * 1024

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)


def load_summarizer():
    """Load BART and expose the callable contract used by the API."""
    import torch
    from transformers import AutoTokenizer, BartForConditionalGeneration

    class BartSummarizer:
        """Compatibility wrapper for the pipeline removed in Transformers 5."""

        def __init__(self, model_name):
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.model = BartForConditionalGeneration.from_pretrained(model_name)
            self.model.to(self.device)
            self.model.eval()

        def __call__(self, text, max_length, min_length, do_sample=False):
            inputs = self.tokenizer(text, return_tensors="pt", truncation=False)
            inputs = {name: tensor.to(self.device) for name, tensor in inputs.items()}
            with torch.inference_mode():
                summary_ids = self.model.generate(
                    **inputs,
                    max_length=max_length,
                    min_length=min_length,
                    do_sample=do_sample,
                )
            summary_text = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
            return [{"summary_text": summary_text}]

    logger.info("Loading summarization model %s", MODEL_NAME)
    model = BartSummarizer(MODEL_NAME)
    logger.info("Summarization model loaded")
    return model


# Unit tests set this variable and inject a lightweight mock.
summarizer = None if os.getenv("BART_SKIP_MODEL_LOAD") == "1" else load_summarizer()


def _json_error(message, status_code):
    return jsonify({"error": message}), status_code


def _parse_length(value, default, field_name):
    value = default if value is None else value
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise ValueError(f"{field_name} must be an integer")
    if not MIN_SUMMARY_LENGTH <= value <= MAX_SUMMARY_LENGTH:
        raise ValueError(
            f"{field_name} must be between {MIN_SUMMARY_LENGTH} and {MAX_SUMMARY_LENGTH}"
        )
    return int(value)


def _input_token_count(text):
    encoded = summarizer.tokenizer(text, add_special_tokens=True, truncation=False)
    return len(encoded["input_ids"])


def create_app(model=None):
    """Create the Flask app; model injection keeps unit tests offline."""
    global summarizer
    if model is not None:
        summarizer = model

    application = Flask(__name__)
    application.config["MAX_CONTENT_LENGTH"] = MAX_REQUEST_BYTES

    @application.errorhandler(RequestEntityTooLarge)
    def request_too_large(_error):
        return _json_error("Request body is too large", 413)

    @application.errorhandler(BadRequest)
    def malformed_request(_error):
        return _json_error("Malformed JSON request", 400)

    @application.route("/health", methods=["GET"])
    def health():
        if summarizer is None:
            return jsonify({"status": "unavailable", "message": "Model is not loaded"}), 503
        return jsonify({"status": "ok", "message": "Backend is running"})

    @application.route("/summarize", methods=["POST"])
    def summarize():
        try:
            if not request.is_json:
                return _json_error("No text provided", 400)
            data = request.get_json(force=False, silent=False)
            if not isinstance(data, dict) or "text" not in data:
                return _json_error("No text provided", 400)

            text = data["text"]
            if not isinstance(text, str) or not text.strip():
                return _json_error("No text provided", 400)

            word_count = len(text.split())
            if word_count < MIN_WORDS:
                return _json_error(
                    f"Le texte est trop court. Minimum 30 mots requis. (Vous avez {word_count} mots)",
                    400,
                )

            try:
                max_length = _parse_length(data.get("max_length"), 130, "max_length")
                min_length = _parse_length(data.get("min_length"), 30, "min_length")
            except ValueError as error:
                return _json_error(str(error), 400)

            if min_length > max_length:
                return _json_error("min_length must be less than or equal to max_length", 400)

            if summarizer is None:
                logger.error("Summarization requested while model is unavailable")
                return _json_error("Summarization service is unavailable", 503)

            token_count = _input_token_count(text)
            if token_count > MAX_INPUT_TOKENS:
                return _json_error(
                    f"Le texte est trop long. Maximum {MAX_INPUT_TOKENS} tokens BART autorisés. (Vous avez {token_count} tokens)",
                    400,
                )

            logger.info("Generating summary for %d words", word_count)
            result = summarizer(
                text,
                max_length=max_length,
                min_length=min_length,
                do_sample=False,
            )
            summary_text = result[0]["summary_text"]
            return jsonify(
                {
                    "original_length": word_count,
                    "summary": summary_text,
                    "summary_length": len(summary_text.split()),
                }
            )
        except BadRequest:
            raise
        except Exception:
            logger.exception("Unexpected summarization failure")
            return _json_error("An internal error occurred during summarization", 500)

    return application


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
