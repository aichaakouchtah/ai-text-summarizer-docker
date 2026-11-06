import os
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

os.environ["BART_SKIP_MODEL_LOAD"] = "1"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app  # noqa: E402


class FakeTokenizer:
    def __call__(self, text, **_kwargs):
        return {"input_ids": list(range(len(text.split()) + 2))}


@pytest.fixture
def mock_summarizer():
    model = Mock(return_value=[{"summary_text": "This is a mocked summary."}])
    model.tokenizer = FakeTokenizer()
    return model


@pytest.fixture
def client(mock_summarizer):
    application = create_app(mock_summarizer)
    application.config.update(TESTING=True)
    return application.test_client()


@pytest.fixture
def valid_payload():
    text = " ".join(f"word{i}" for i in range(40))
    return {"text": text, "max_length": 50, "min_length": 10}
