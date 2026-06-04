import json
import pytest
from unittest.mock import patch, MagicMock
from app.utils.storage import (
    PENDING_RECEIPTS_FILE,
    TX_FILE,
    save_pending_receipts,
)


def _csrf_from_page(client, path):
    page = client.get(path)
    html = page.data.decode('utf-8')
    for line in html.splitlines():
        if 'csrf_token' in line and 'value=' in line:
            start = line.find('value="') + len('value="')
            end = line.find('"', start)
            return line[start:end]
    return None


@pytest.fixture
def receipt_storage_paths(tmp_path, monkeypatch):
    data_dir = tmp_path / 'data'
    data_dir.mkdir()
    monkeypatch.setattr('app.utils.storage.DATA_DIR', str(data_dir))
    monkeypatch.setattr('app.utils.storage.TX_FILE', str(data_dir / 'transactions.json'))
    monkeypatch.setattr('app.utils.storage.PENDING_RECEIPTS_FILE', str(data_dir / 'receipts_pending.json'))
    monkeypatch.setattr('app.utils.storage.RECEIPTS_FILE', str(data_dir / 'receipts.json'))
    save_pending_receipts([])
    with open(data_dir / 'transactions.json', 'w', encoding='utf-8') as fh:
        json.dump([], fh)
    return data_dir


def test_receipt_review_get_requires_pending(client, app, receipt_storage_paths):
    app.config['TESTING'] = False
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['PREFLIGHT_SUCCESS'] = True
    r = client.get('/receipt_review/nonexistent-id')
    assert r.status_code == 302


def test_receipt_review_confirm_flow(client, app, receipt_storage_paths):
    app.config['TESTING'] = False
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['PREFLIGHT_SUCCESS'] = True
    bundle = {
        'receipt_id': 'review-1',
        'source_image': 'uploads/test.png',
        'header': {
            'receipt_id': 'review-1',
            'merchant': 'Review Store',
            'date': '2026-06-01',
            'subtotal': '',
            'tax': '',
            'tip': '',
            'total': '25.00',
            'payment_method': 'credit',
            'currency': 'USD',
            'confidence': 'low',
            'parse_status': 'review_pending',
            'source_image': 'uploads/test.png',
            'raw_summary': '',
        },
        'line_items': [
            {
                'line_id': 'line-1',
                'receipt_id': 'review-1',
                'name': 'Item A',
                'quantity': 1,
                'unit_price': '',
                'line_total': '25.00',
                'category': 'shopping',
                'category_confidence': 'low',
                'is_discount': False,
            }
        ],
        'transaction_draft': {'id': 'tx-review-1'},
    }
    save_pending_receipts([bundle])
    page = client.get('/receipt_review/review-1')
    assert page.status_code == 200
    assert b'Review Store' in page.data
    token = _csrf_from_page(client, '/receipt_review/review-1')
    r = client.post(
        '/receipt_review/review-1',
        data={
            'csrf_token': token,
            'action': 'confirm',
            'merchant': 'Review Store',
            'date': '2026-06-01',
            'total': '25.00',
            'line_id': 'line-1',
            'line_name': 'Item A',
            'line_total': '25.00',
            'line_category': 'shopping',
        },
        follow_redirects=False,
    )
    assert r.status_code == 302
    with open(receipt_storage_paths / 'transactions.json', encoding='utf-8') as fh:
        txs = json.load(fh)
    assert len(txs) == 1
    assert txs[0]['source'] == 'receipt'
    assert txs[0]['line_items'][0]['name'] == 'Item A'


@patch('app.routes.main.receipt_intelligence')
def test_upload_receipt_redirects_to_review(mock_ri, client, app, receipt_storage_paths, tmp_path):
    app.config['TESTING'] = False
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['PREFLIGHT_SUCCESS'] = True
    mock_ri.process_upload.return_value = {
        'auto_commit': False,
        'receipt_id': 'pending-99',
        'transaction': None,
        'pending': {
            'receipt_id': 'pending-99',
            'source_image': 'uploads/r.png',
            'header': {'receipt_id': 'pending-99', 'merchant': 'X', 'total': '1.00', 'confidence': 'low',
                       'parse_status': 'review_pending', 'source_image': 'uploads/r.png',
                       'date': '', 'subtotal': '', 'tax': '', 'tip': '', 'payment_method': 'unknown',
                       'currency': 'USD', 'raw_summary': ''},
            'line_items': [],
            'transaction_draft': {'id': 't1'},
        },
        'header': {},
        'line_items': [],
    }
    from io import BytesIO

    token = _csrf_from_page(client, '/upload_receipt')
    png = (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01'
        b'\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    )
    r = client.post(
        '/upload_receipt',
        data={'csrf_token': token, 'receipt': (BytesIO(png), 'r.png')},
        content_type='multipart/form-data',
        follow_redirects=False,
    )
    assert r.status_code == 302
    assert '/receipt_review/pending-99' in r.headers.get('Location', '')
