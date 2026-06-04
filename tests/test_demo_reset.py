import os
import json
import pytest
from app.utils.storage import (
    TX_FILE,
    save_transactions,
    load_transactions,
    reset_demo_data,
    ROOT,
)


@pytest.fixture
def demo_setup(tmp_path, monkeypatch):
    uploads = tmp_path / 'uploads'
    uploads.mkdir()
    (uploads / 'receipt.png').write_bytes(b'fake')
    data_dir = tmp_path / 'data'
    data_dir.mkdir()
    monkeypatch.setattr('app.utils.storage.ROOT', str(tmp_path))
    monkeypatch.setattr('app.utils.storage.DATA_DIR', str(data_dir))
    monkeypatch.setattr('app.utils.storage.TX_FILE', str(data_dir / 'transactions.json'))
    monkeypatch.setattr('app.utils.storage.LOG_FILE', str(tmp_path / 'logs' / 'app.log'))
    save_transactions([{'amount': '10', 'merchant': 'Test', 'category': 'food', 'date': '2026-01-01'}])
    return str(uploads)


def test_reset_demo_data_clears_transactions_and_uploads(demo_setup):
    summary = reset_demo_data('uploads')
    assert summary['transactions_cleared'] is True
    assert load_transactions() == []
    assert summary['uploads_removed'] == 1
    assert not os.path.exists(os.path.join(demo_setup, 'receipt.png'))


def test_demo_reset_route_requires_confirmation(client):
    response = client.post('/demo_reset', data={})
    assert response.status_code == 302
    assert '/demo_reset' in response.headers.get('Location', '')


def test_demo_reset_route_clears_data(client, tmp_path, monkeypatch):
    data_dir = tmp_path / 'data'
    data_dir.mkdir()
    uploads = tmp_path / 'uploads'
    uploads.mkdir()
    tx_file = data_dir / 'transactions.json'
    monkeypatch.setattr('app.utils.storage.ROOT', str(tmp_path))
    monkeypatch.setattr('app.utils.storage.DATA_DIR', str(data_dir))
    monkeypatch.setattr('app.utils.storage.TX_FILE', str(tx_file))
    monkeypatch.setattr('app.utils.storage.LOG_FILE', str(tmp_path / 'logs' / 'app.log'))
    with open(tx_file, 'w', encoding='utf-8') as fh:
        json.dump([{'amount': '5', 'merchant': 'A', 'category': 'x', 'date': '2026-01-01'}], fh)

    response = client.post('/demo_reset', data={'confirm': 'yes'}, follow_redirects=False)
    assert response.status_code == 302
    assert response.headers.get('Location', '').endswith('/')
    with open(tx_file, 'r', encoding='utf-8') as fh:
        assert json.load(fh) == []
