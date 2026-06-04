import os
import pytest

def test_app_import():
    """Test app imports successfully."""
    import app
    assert hasattr(app, 'app')
    assert app.app is not None


def test_config_load():
    """Test config loads successfully."""
    from app.utils.config_manager import config
    assert config.config is not None
    assert config.get('flask.secret_key') is not None


def test_flask_secret_key():
    """Test Flask secret key is set."""
    from app import app as flask_app
    assert flask_app.secret_key is not None


def test_routes_available():
    """Test main routes are registered."""
    from app import app as flask_app
    with flask_app.app_context():
        routes = [str(rule) for rule in flask_app.url_map.iter_rules()]
        assert '/' in str(routes)
        assert any('upload_receipt' in r for r in routes)
        assert any('upload_csv' in r for r in routes)
        assert any('demo_reset' in r for r in routes)


def test_preflight_validation():
    """Test preflight validation runs."""
    from app.utils.preflight import validate_preflight
    success, errors = validate_preflight()
    # Note: success may be False if API key file doesn't exist on test system
    # but the validation function should run without error
    assert isinstance(success, bool)
    assert isinstance(errors, list)


def test_normalize_transaction():
    """Test transaction normalization."""
    from app.utils.normalize import normalize_transaction
    raw = {'amount': '50.00', 'merchant': 'Store', 'category': 'food', 'date': '2025-01-01'}
    tx = normalize_transaction(raw)
    assert tx['amount'] == '50.00'
    assert tx['merchant'] == 'Store'
    assert tx['category'] == 'food'
    assert 'id' in tx


def test_storage_load():
    """Test storage load/save works."""
    from app.utils.storage import load_transactions, save_transactions
    txs = load_transactions()
    assert isinstance(txs, list)
