import requests


class ReturnEnvClient:
    """
    Safe client for interacting with the Return Environment.

    NOTE:
    - Uses HTTP (stateless), so full RL session behavior is not guaranteed.
    - Designed for basic testing and demonstration only.
    - Environment is intended to be used with OpenEnv runtime for full functionality.
    """

    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.session = requests.Session()

    def reset(self):
        try:
            response = self.session.post(f"{self.base_url}/reset")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {
                "error": "Reset request failed",
                "details": str(e)
            }

    def step(self, decision: str):
        try:
            payload = {
                "action": {
                    "decision": decision
                }
            }

            response = self.session.post(
                f"{self.base_url}/step",
                json=payload
            )

            response.raise_for_status()
            return response.json()

        except Exception as e:
            return {
                "error": "Step request failed",
                "details": str(e),
                "note": "This may occur due to stateless HTTP. Use OpenEnv runtime for proper session handling."
            }