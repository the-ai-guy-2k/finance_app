import os
from app.utils.config_manager import config
from app.utils.logging_service import ErrorCategory, log_error, log_info


def load_openai_api_key():
    """Load OpenAI API key: OPENAI_API_KEY env first, then config file path."""
    env_key = os.getenv('OPENAI_API_KEY')
    if env_key and env_key.strip():
        log_info("OpenAI API key loaded from OPENAI_API_KEY environment variable")
        return env_key.strip()

    api_key_file = config.get('openai.api_key_file')
    if not api_key_file:
        log_error(ErrorCategory.API_KEY_ERROR, "OpenAI API key not set: no OPENAI_API_KEY and no api_key_file in config")
        return None

    if not os.path.exists(api_key_file):
        log_error(ErrorCategory.API_KEY_ERROR, f"OpenAI API key file not found: {api_key_file}")
        return None

    try:
        with open(api_key_file, 'r', encoding='utf-8') as fh:
            key = fh.read().strip()
        if not key:
            log_error(ErrorCategory.API_KEY_ERROR, f"OpenAI API key file is empty: {api_key_file}")
            return None
        log_info("OpenAI API key loaded from configured file path")
        return key
    except Exception as e:
        log_error(ErrorCategory.API_KEY_ERROR, "Failed to read OpenAI API key file", e)
        return None
