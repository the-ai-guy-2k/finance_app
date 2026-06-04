import os
from flask import Flask
from flask_wtf.csrf import CSRFProtect
from app.utils.config_manager import config
from app.utils.preflight import validate_preflight
from app.utils.logging_service import setup_logger, log_info, log_error, ErrorCategory

HERE = os.path.dirname(__file__)

def _template_path():
    return os.path.join(HERE, "templates")

def _static_path():
    return os.path.join(HERE, "static")

# Initialize logger early
logger = setup_logger()

# Validate preflight
success, preflight_errors = validate_preflight()
if not success:
    log_error(ErrorCategory.CONFIG_ERROR, f"Preflight validation failed. Errors: {preflight_errors}")

app = Flask(
    __name__,
    template_folder=_template_path(),
    static_folder=_static_path(),
)
CSRFProtect(app)

# Set Flask secret key from config
secret = config.get('flask.secret_key', 'theaiguyfreakout')
app.secret_key = secret
log_info("Flask secret key configured")

# Store config in app context for routes to access
app.config['PREFLIGHT_SUCCESS'] = success
app.config['PREFLIGHT_ERRORS'] = preflight_errors

from app.routes.main import bp as main_bp  # noqa: E402
app.register_blueprint(main_bp)
