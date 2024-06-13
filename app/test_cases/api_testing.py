import json
from app import app_bckp
import pytest

@pytest.fixture
def test_app():
    return app_bckp.test_client()

def test_get_chat_history_request(test_app):
    response = test_app.get('/v1/chatbot/history/1/1')
    assert response.status_code in (200, 404)
    if response.status_code == 200:
        data = json.loads(response.get_data(as_text=True))
        assert isinstance(data, list)

def test_invalid_get_chat_history_request(test_app):
    response = test_app.get('/v1/chatbot/history/1/1000')
    assert response.status_code == 404
    if response.status_code == 200:
        data = json.loads(response.get_data(as_text=True))
        assert 'error' in data

def test_get_chat_list_request(test_app):
    response = test_app.get('/v1/chatbot/chat_list/1')
    assert response.status_code in (200, 404)
    if response.status_code == 200:
        data = json.loads(response.get_data(as_text=True))
        assert 'chat_sessions' in data

def test_invalid_get_chat_list_request(test_app):
    response = test_app.get('/v1/chatbot/chat_list/1000')
    assert response.status_code == 404
    if response.status_code == 200:
        data = json.loads(response.get_data(as_text=True))
        assert 'error' in data

def test_post_request(test_app):
    payload = {
        "user_id": 1,
        "chat_session_id": 1,
        "question": "What is the meaning of life?"
    }
    response = test_app.post('/v1/chatbot', json=payload)
    assert response.status_code in (200, 404)
    if response.status_code == 200:
        data = json.loads(response.get_data(as_text=True))
        assert 'answer' in data
        assert 'chat_session_id' in data
