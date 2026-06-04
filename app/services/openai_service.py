import json
from app.utils.config_manager import config
from app.utils.logging_service import ErrorCategory, log_error, log_info
from app.utils.openai_key import load_openai_api_key


class OpenAIService:
    """OpenAI service for behavioral insights."""

    def __init__(self):
        self.api_key = load_openai_api_key()
        self.model = config.get('openai.model', 'gpt-4o-mini')
        self._client = None

    def _get_client(self):
        if self._client is not None:
            return self._client
        if not self.api_key:
            return None
        try:
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key)
            return self._client
        except Exception as e:
            log_error(ErrorCategory.OPENAI_API_ERROR, "Failed to initialize OpenAI client", e)
            return None

    def parse_receipt(self, file_path_or_bytes):
        """Legacy placeholder; receipt parsing uses OpenAIReceiptParsingService."""
        return {
            'amount': '0.00',
            'merchant': 'Receipt',
            'category': 'unknown',
            'date': '',
            'note': 'Use upload receipt flow for AI parsing',
        }

    def generate_insights(self, transactions):
        """Generate behavioral insights from transactions using OpenAI or heuristics."""
        client = self._get_client()
        if client and self.api_key:
            try:
                prompt = f"""Generate brief behavioral financial insights from these transactions (max 200 words):
{json.dumps(transactions)[:4000]}

Focus on:
- spending patterns
- behavioral observations
- actionable insights"""

                response = client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=300,
                )
                insight = response.choices[0].message.content.strip()
                log_info("Behavioral insights generated via OpenAI")
                return insight
            except Exception as e:
                log_error(ErrorCategory.OPENAI_API_ERROR, "Insight generation failed", e)

        total = 0.0
        count = 0
        categories = {}
        for t in transactions:
            try:
                amt = float(t.get('amount') or 0)
                total += amt
                count += 1
                cat = t.get('category', 'uncategorized')
                categories[cat] = categories.get(cat, 0) + 1
            except Exception:
                continue

        avg = (total / count) if count else 0
        top_cat = max(categories, key=categories.get) if categories else 'none'

        return f"""Financial Overview (heuristic):
- Transactions: {count}
- Total: ${total:.2f}
- Average: ${avg:.2f}
- Top category: {top_cat}

Note: Full insights require OpenAI API access."""
