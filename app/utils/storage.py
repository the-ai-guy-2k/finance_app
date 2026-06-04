import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATA_DIR = os.path.join(ROOT, 'data')
os.makedirs(DATA_DIR, exist_ok=True)
TX_FILE = os.path.join(DATA_DIR, 'transactions.json')
GOALS_FILE = os.path.join(DATA_DIR, 'goals.json')
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
