def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok", "message": "Backend is running"}


def test_valid_summary(client, mock_summarizer, valid_payload):
    response = client.post("/summarize", json=valid_payload)
    assert response.status_code == 200
    assert response.get_json() == {
        "original_length": 40,
        "summary": "This is a mocked summary.",
        "summary_length": 5,
    }
    mock_summarizer.assert_called_once()


def test_empty_text(client):
    response = client.post("/summarize", json={"text": ""})
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_text_shorter_than_30_words(client):
    response = client.post("/summarize", json={"text": "too short"})
    assert response.status_code == 400
    assert "Minimum 30 mots" in response.get_json()["error"]


def test_invalid_length_parameter(client, valid_payload):
    valid_payload["max_length"] = "50"
    response = client.post("/summarize", json=valid_payload)
    assert response.status_code == 400
    assert response.get_json()["error"] == "max_length must be an integer"


def test_min_length_greater_than_max_length(client, valid_payload):
    valid_payload.update({"min_length": 50, "max_length": 20})
    response = client.post("/summarize", json=valid_payload)
    assert response.status_code == 400
    assert "less than or equal" in response.get_json()["error"]


def test_malformed_json(client):
    response = client.post("/summarize", data='{"text":', content_type="application/json")
    assert response.status_code == 400
    assert response.get_json() == {"error": "Malformed JSON request"}


def test_model_exception_returns_generic_error(client, mock_summarizer, valid_payload):
    mock_summarizer.side_effect = RuntimeError("sensitive internal detail")
    response = client.post("/summarize", json=valid_payload)
    assert response.status_code == 500
    assert response.get_json() == {"error": "An internal error occurred during summarization"}
    assert "sensitive internal detail" not in response.get_data(as_text=True)


def test_text_exceeding_bart_limit(client, valid_payload, mock_summarizer):
    mock_summarizer.tokenizer = lambda *_args, **_kwargs: {"input_ids": list(range(1025))}
    response = client.post("/summarize", json=valid_payload)
    assert response.status_code == 400
    assert "1024 tokens" in response.get_json()["error"]


def test_missing_json_body(client):
    response = client.post("/summarize")
    assert response.status_code == 400
    assert "error" in response.get_json()
