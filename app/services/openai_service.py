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
        from app.utils.dashboard_stats import build_insights_context

        context = build_insights_context(transactions)
        client = self._get_client()
        if client and self.api_key:
            try:
                prompt = f"""Generate brief behavioral financial insights from these transactions (max 200 words).

Transactions sample:
{json.dumps(context.get('transactions', [])[:20])[:3000]}

Category totals (parent transactions):
{json.dumps(context.get('category_totals', {}))}

Line-item category totals (from receipts):
{json.dumps(context.get('line_category_totals', {}))}

Receipt summaries:
{json.dumps(context.get('receipt_summaries', []))[:1500]}

Total spend: {context.get('total_spend', 0)}
Receipt count: {context.get('receipt_count', 0)}

Focus on:
- spending patterns by category
- receipt vs manual entry patterns
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

        total = context.get('total_spend', 0.0)
        count = len(transactions or [])
        categories = context.get('category_totals', {})
        line_cats = context.get('line_category_totals', {})
        receipt_count = context.get('receipt_count', 0)

        avg = (total / count) if count else 0
        top_cat = max(categories, key=categories.get) if categories else 'none'
        top_line = max(line_cats, key=line_cats.get) if line_cats else 'none'

        return f"""Financial Overview (heuristic):
- Transactions: {count}
- Total: ${total:.2f}
- Average: ${avg:.2f}
- Top category: {top_cat}
- Receipt-derived transactions: {receipt_count}
- Top line-item category: {top_line}

Note: Full insights require OpenAI API access."""
