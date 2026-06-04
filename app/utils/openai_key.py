import os
from app.utils.config_manager import config
from app.utils.logging_service import ErrorCategory, log_error, log_info


def _load_from_ssm(parameter_name):
    """Load OpenAI API key from AWS SSM Parameter Store (SecureString)."""
    if not parameter_name or not parameter_name.strip():
        return None
    try:
        import boto3
        from botocore.exceptions import BotoCoreError, ClientError

        region = (
            os.getenv('AWS_REGION')
            or os.getenv('AWS_DEFAULT_REGION')
            or 'us-east-1'
        )
        client = boto3.client('ssm', region_name=region)
        response = client.get_parameter(Name=parameter_name.strip(), WithDecryption=True)
        key = response.get('Parameter', {}).get('Value', '').strip()
        if key:
            log_info("OpenAI API key loaded from AWS SSM Parameter Store")
            return key
        log_error(ErrorCategory.API_KEY_ERROR, f"SSM parameter empty: {parameter_name}")
    except (BotoCoreError, ClientError, ImportError) as e:
        log_error(ErrorCategory.API_KEY_ERROR, "Failed to load OpenAI API key from SSM", e)
    return None


def load_openai_api_key():
    """Load OpenAI API key: env, SSM (when configured), then config file path."""
    env_key = os.getenv('OPENAI_API_KEY')
    if env_key and env_key.strip():
        log_info("OpenAI API key loaded from OPENAI_API_KEY environment variable")
        return env_key.strip()

    ssm_name = os.getenv('OPENAI_SSM_PARAMETER_NAME') or config.get('openai.ssm_parameter_name')
    if ssm_name:
        key = _load_from_ssm(ssm_name)
        if key:
            return key

    api_key_file = config.get('openai.api_key_file')
    if not api_key_file:
        log_error(
            ErrorCategory.API_KEY_ERROR,
            "OpenAI API key not set: no OPENAI_API_KEY, SSM name, or api_key_file in config",
        )
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
