import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATA_DIR = os.path.join(ROOT, 'data')
os.makedirs(DATA_DIR, exist_ok=True)
TX_FILE = os.path.join(DATA_DIR, 'transactions.json')
GOALS_FILE = os.path.join(DATA_DIR, 'goals.json')
RECEIPTS_FILE = os.path.join(DATA_DIR, 'receipts.json')
PENDING_RECEIPTS_FILE = os.path.join(DATA_DIR, 'receipts_pending.json')
LOG_FILE = os.path.join(ROOT, 'logs', 'app.log')


def load_transactions():
    if not os.path.exists(TX_FILE):
        return []
    try:
        with open(TX_FILE, 'r', encoding='utf-8') as fh:
            return json.load(fh)
    except Exception:
        return []


def save_transactions(txs):
    try:
        with open(TX_FILE, 'w', encoding='utf-8') as fh:
            json.dump(txs, fh, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def get_default_goals():
    """Return default goals for MVP testing."""
    return [
        {
            'id': 'goal_emergency_fund',
            'name': 'Emergency Fund Goal',
            'target': 5000.0,
            'description': 'Build emergency fund'
        }
    ]


def _load_json_list(path):
    if not os.path.exists(path):
        return []
    try:
        with open(path, 'r', encoding='utf-8') as fh:
            data = json.load(fh)
            return data if isinstance(data, list) else []
    except Exception:
        return []


def _save_json_list(path, items):
    try:
        with open(path, 'w', encoding='utf-8') as fh:
            json.dump(items, fh, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def load_pending_receipts():
    return _load_json_list(PENDING_RECEIPTS_FILE)


def save_pending_receipts(items):
    return _save_json_list(PENDING_RECEIPTS_FILE, items)


def get_pending_receipt(receipt_id):
    for item in load_pending_receipts():
        if item.get('receipt_id') == receipt_id:
            return item
    return None


def save_pending_receipt(bundle):
    items = [b for b in load_pending_receipts() if b.get('receipt_id') != bundle.get('receipt_id')]
    items.append(bundle)
    return save_pending_receipts(items)


def remove_pending_receipt(receipt_id):
    items = [b for b in load_pending_receipts() if b.get('receipt_id') != receipt_id]
    return save_pending_receipts(items)


def load_receipts_archive():
    return _load_json_list(RECEIPTS_FILE)


def save_receipt_archive(header):
    items = [h for h in load_receipts_archive() if h.get('receipt_id') != header.get('receipt_id')]
    items.append(header)
    return _save_json_list(RECEIPTS_FILE, items)


def reset_demo_data(upload_folder='uploads'):
    """Clear demo runtime data. Does not modify config, code, or deployment files."""
    uploads_path = os.path.join(ROOT, upload_folder)
    summary = {
        'transactions_cleared': False,
        'uploads_removed': 0,
        'log_cleared': False,
    }

    if save_transactions([]):
        summary['transactions_cleared'] = True

    summary['pending_receipts_cleared'] = save_pending_receipts([])
    summary['receipts_archive_cleared'] = _save_json_list(RECEIPTS_FILE, [])

    if os.path.isdir(uploads_path):
        for name in os.listdir(uploads_path):
            path = os.path.join(uploads_path, name)
            if os.path.isfile(path):
                try:
                    os.remove(path)
                    summary['uploads_removed'] += 1
                except OSError:
                    pass

    if os.path.exists(GOALS_FILE):
        try:
            os.remove(GOALS_FILE)
            summary['goals_file_removed'] = True
        except OSError:
            summary['goals_file_removed'] = False
    else:
        summary['goals_file_removed'] = False

    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    try:
        with open(LOG_FILE, 'w', encoding='utf-8') as fh:
            fh.write('')
        summary['log_cleared'] = True
    except OSError:
        summary['log_cleared'] = False

    return summary
