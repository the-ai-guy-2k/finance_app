from app.utils.config_manager import config
from app.utils.logging_service import ErrorCategory, log_error, log_info
from app.utils.openai_key import load_openai_api_key
import os


def validate_preflight():
    """Validate startup requirements. Returns (success, errors_list)."""
    errors = []
    
    # Check config loaded successfully
    if config.get_errors():
        errors.extend(config.get_errors())
    
    # Check Flask secret exists
    secret = config.get('flask.secret_key')
    if not secret:
        msg = log_error(ErrorCategory.CONFIG_ERROR, "Flask secret_key missing from config.json")
        errors.append(msg)
    
    if not load_openai_api_key():
        msg = log_error(
            ErrorCategory.API_KEY_ERROR,
            "OpenAI API key unavailable: set OPENAI_API_KEY, OPENAI_SSM_PARAMETER_NAME, or openai.api_key_file in config.json",
        )
        errors.append(msg)
    
    # Check data folder exists
    data_folder = config.get('data.folder', 'data')
    data_path = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')), data_folder)
    if not os.path.exists(data_path):
        try:
            os.makedirs(data_path, exist_ok=True)
            log_info(f"Data folder created: {data_path}")
        except Exception as e:
            msg = log_error(ErrorCategory.STORAGE_ERROR, f"Failed to create data folder", e)
            errors.append(msg)
    
    # Check uploads folder exists
    uploads_folder = config.get('upload.folder', 'uploads')
    uploads_path = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')), uploads_folder)
    if not os.path.exists(uploads_path):
        try:
            os.makedirs(uploads_path, exist_ok=True)
            log_info(f"Uploads folder created: {uploads_path}")
        except Exception as e:
            msg = log_error(ErrorCategory.STORAGE_ERROR, f"Failed to create uploads folder", e)
            errors.append(msg)
    
    # Check logs folder exists
    logs_path = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')), 'logs')
    if not os.path.exists(logs_path):
        try:
            os.makedirs(logs_path, exist_ok=True)
            log_info(f"Logs folder created: {logs_path}")
        except Exception as e:
            msg = log_error(ErrorCategory.STORAGE_ERROR, f"Failed to create logs folder", e)
            errors.append(msg)
    
    success = len(errors) == 0
    if success:
        log_info("Preflight validation passed")
    else:
        log_error(ErrorCategory.CONFIG_ERROR, f"Preflight validation failed with {len(errors)} error(s)")
    
    return success, errors
