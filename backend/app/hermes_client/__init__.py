import time
import requests
from app.hermes_client.retry import with_retry, CircuitBreaker, CircuitBreakerOpen


class HermesException(Exception):
    """Raised when Hermes Agent or DeepSeek API fails."""
    pass


class HermesClient:
    def __init__(self, base_url, timeout=30, max_retries=3,
                 circuit_threshold=5, circuit_cooldown=60):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.circuit_breaker = CircuitBreaker(
            threshold=circuit_threshold,
            cooldown=circuit_cooldown
        )

    def _post(self, endpoint, payload):
        if self.circuit_breaker.is_open():
            remaining = self.circuit_breaker.remaining_cooldown()
            raise CircuitBreakerOpen(
                f"Circuit breaker open. Try again in {int(remaining)} seconds."
            )

        url = f"{self.base_url}{endpoint}"

        def _request():
            resp = requests.post(url, json=payload, timeout=self.timeout)
            if not resp.ok:
                raise HermesException(
                    f"Hermes returned {resp.status_code}: {resp.text}"
                )
            return resp.json()

        try:
            result = with_retry(_request, max_retries=self.max_retries)
            self.circuit_breaker.record_success()
            return result
        except CircuitBreakerOpen:
            raise
        except Exception as e:
            self.circuit_breaker.record_failure()
            raise HermesException(
                f"AI service temporarily unavailable, please try again "
                f"or enter prompts manually. Details: {str(e)}"
            ) from e

    def generate_prompt(self, creature_name, juan=None, style_tag=None,
                        baseline_id=None):
        payload = {
            "creature_name": creature_name,
            "juan": juan,
            "style_tag": style_tag,
            "baseline_id": baseline_id,
        }
        payload = {k: v for k, v in payload.items() if v is not None}
        return self._post("/api/v1/skills/generate-prompt", payload)

    def review_style(self, generated_prompt, baseline_id):
        payload = {
            "generated_prompt": generated_prompt,
            "baseline_id": baseline_id,
        }
        return self._post("/api/v1/skills/review-style", payload)

    def health_check(self):
        try:
            resp = requests.get(f"{self.base_url}/health", timeout=5)
            return resp.ok
        except Exception:
            return False
