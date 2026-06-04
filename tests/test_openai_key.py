import os
import pytest
from unittest.mock import patch
from app.utils.openai_key import load_openai_api_key


def test_load_prefers_environment_variable(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'sk-test-env-key')
    with patch('app.utils.openai_key.config') as mock_config:
        mock_config.get.return_value = '/some/file.txt'
        assert load_openai_api_key() == 'sk-test-env-key'


def test_load_falls_back_to_file(monkeypatch, tmp_path):
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    key_file = tmp_path / 'key.txt'
    key_file.write_text('sk-file-key\n', encoding='utf-8')
    with patch('app.utils.openai_key.config') as mock_config:
        mock_config.get.return_value = str(key_file)
        assert load_openai_api_key() == 'sk-file-key'


def test_load_returns_none_when_unavailable(monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    with patch('app.utils.openai_key.config') as mock_config:
        mock_config.get.return_value = None
        assert load_openai_api_key() is None
