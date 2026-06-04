import os
import base64
import json
from app.utils.config_manager import config
from app.utils.logging_service import ErrorCategory, log_error, log_info
from app.utils.openai_key import load_openai_api_key


class OpenAIReceiptParsingService:
    """Dedicated service for OpenAI-powered receipt parsing.
    
    Workflow:
    1. Load image from file
    2. Encode to base64
    3. Send to OpenAI vision API
    4. Parse structured response
    5. Return normalized transaction dict
    """

    def __init__(self):
        self.api_key = load_openai_api_key()
        self.model = config.get('openai.model', 'gpt-4o-mini')
        self._client = None

    def _get_client(self):
        """Lazy-load modern OpenAI client (SDK v1.0+)."""
        if self._client is not None:
            return self._client
        
        if not self.api_key:
            log_error(ErrorCategory.API_KEY_ERROR, "Cannot initialize OpenAI client: API key not available")
            return None
        
        try:
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key)
            log_info("OpenAI client initialized (SDK v1.0+)")
            return self._client
        except Exception as e:
            log_error(ErrorCategory.OPENAI_API_ERROR, "Failed to initialize OpenAI client", e)
            return None

    def _strip_json_code_fence(self, text):
        """Remove markdown code fences or backtick wrappers from model output."""
        cleaned = text.strip()
        if cleaned.startswith("```") and cleaned.endswith("```"):
            lines = cleaned.splitlines()
            if len(lines) >= 3:
                return "\n".join(lines[1:-1]).strip()
        if cleaned.startswith("`") and cleaned.endswith("`"):
            return cleaned.strip("`").strip()
        return cleaned

    def _safe_parse_json(self, raw_text):
        """Safely parse JSON from raw OpenAI response text."""
        response_text = raw_text.strip()
        raw_length = len(response_text)
        preview = response_text[:500]

        if not response_text:
            log_error(
                ErrorCategory.VALIDATION_ERROR,
                "OpenAI response empty after stripping whitespace"
            )
            return None

        cleaned_text = self._strip_json_code_fence(response_text)
        if not cleaned_text:
            log_error(
                ErrorCategory.VALIDATION_ERROR,
                f"OpenAI response empty after removing code fences | raw length: {raw_length}"
            )
            return None

        try:
            return json.loads(cleaned_text)
        except json.JSONDecodeError as e:
            log_error(
                ErrorCategory.VALIDATION_ERROR,
                f"Failed to parse OpenAI response as JSON | raw length: {raw_length} | preview: {preview}",
                e
            )
            return None

    def parse_receipt_image(self, file_path):
        """Parse receipt image using OpenAI vision API (modern SDK).
        
        Args:
            file_path: Path to receipt image file
            
        Returns:
            dict with parsed transaction fields:
            {
                'merchant': str,
                'amount': str (float as string),
                'date': str (ISO format or empty),
                'category': str,
                'note': str
            }
        """
        if not os.path.exists(file_path):
            msg = log_error(ErrorCategory.FILE_UPLOAD_ERROR, f"Receipt file not found: {file_path}")
            return self._fallback_transaction(file_path, msg)
        
        # Check file size
        try:
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            max_size = config.get('upload.max_size_mb', 10)
            if file_size_mb > max_size:
                msg = log_error(ErrorCategory.FILE_UPLOAD_ERROR, f"Receipt file too large: {file_size_mb:.1f}MB")
                return self._fallback_transaction(file_path, msg)
        except Exception as e:
            log_error(ErrorCategory.FILE_UPLOAD_ERROR, "Failed to check file size", e)
        
        # Read and encode image
        try:
            with open(file_path, 'rb') as fh:
                image_data = base64.standard_b64encode(fh.read()).decode('utf-8')
        except Exception as e:
            msg = log_error(ErrorCategory.FILE_UPLOAD_ERROR, "Failed to read receipt image", e)
            return self._fallback_transaction(file_path, msg)
        
        # Call OpenAI API
        client = self._get_client()
        if not client:
            msg = "OpenAI API key not configured. Using fallback parsing."
            log_error(ErrorCategory.API_KEY_ERROR, msg)
            return self._fallback_transaction(file_path, msg)
        
        try:
            # Determine image type from filename
            _, ext = os.path.splitext(file_path)
            ext = ext.lower().lstrip('.')
            media_type_map = {
                'png': 'image/png',
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'webp': 'image/webp',
                'gif': 'image/gif'
            }
            media_type = media_type_map.get(ext, 'image/jpeg')
            
            # Call OpenAI ChatCompletion with vision using modern SDK
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """Analyze this receipt image and extract the following information in JSON format:
{
  "merchant": "",
  "date": "",
  "total": 0.0,
  "category": "",
  "items": [],
  "confidence": "",
  "raw_summary": ""
}

Return ONLY valid JSON.
Do not include markdown.
Do not include code fences.
Do not include explanation outside JSON.
If a field is unknown, use an empty string, 0.0, empty list, or \"low\"."""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{media_type};base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )
            
            # Parse response using modern SDK response object
            response_text = response.choices[0].message.content
            parsed = self._safe_parse_json(response_text)
            if not isinstance(parsed, dict):
                msg = "OpenAI response did not contain valid JSON object"
                log_error(ErrorCategory.VALIDATION_ERROR, msg)
                return self._fallback_transaction(file_path, msg)

            log_info(f"Receipt parsed successfully via OpenAI: {parsed.get('merchant', 'unknown')}")
            
            # Normalize parsed data
            raw_amount = parsed.get('total', parsed.get('amount', '0.00'))
            amount_str = str(raw_amount).strip() if raw_amount is not None else '0.00'
            if not amount_str:
                amount_str = '0.00'

            return {
                'merchant': str(parsed.get('merchant', '')).strip(),
                'amount': amount_str,
                'date': str(parsed.get('date', '')).strip(),
                'category': str(parsed.get('category', 'other')).strip().lower() or 'other',
                'note': str(parsed.get('raw_summary', f"OpenAI parsed: {os.path.basename(file_path)}")).strip()
            }
        
        except json.JSONDecodeError as e:
            msg = log_error(ErrorCategory.VALIDATION_ERROR, "Failed to parse OpenAI response as JSON", e)
            return self._fallback_transaction(file_path, msg)
        
        except Exception as e:
            msg = log_error(ErrorCategory.OPENAI_API_ERROR, "OpenAI API call failed", e)
            return self._fallback_transaction(file_path, msg)

    def _fallback_transaction(self, file_path, error_msg=''):
        """Return minimal fallback transaction when parsing fails."""
        return {
            'merchant': os.path.basename(file_path),
            'amount': '0.00',
            'date': '',
            'category': 'uncategorized',
            'note': f'Fallback: {error_msg}' if error_msg else 'Fallback parsing (API unavailable)'
        }
