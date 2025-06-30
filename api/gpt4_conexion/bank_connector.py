# bank_connector.py
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from .config import settings

class BankConnector:
    def __init__(self):
        self.session = self._init_session()
        self.base_url = f"{'https' if settings.BANK_VERIFY_SSL else 'http'}://" \
                        f"{settings.BANK_HOST}:{settings.BANK_PORT}"

    def _init_session(self):
        session = requests.Session()
        retries = Retry(
            total=settings.BANK_RETRIES,
            backoff_factor=0.3,
            status_forcelist=[500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retries)
        session.mount('https://', adapter)
        session.mount('http://', adapter)
        session.verify = settings.BANK_VERIFY_SSL
        return session

    def send(self, endpoint: str, json: dict) -> dict:
        url = f"{self.base_url}{endpoint}"
        try:
            resp = self.session.post(url, json=json, timeout=settings.BANK_TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            # Log sin datos sensibles
            logger.error(f"BankConnector error: {e}")
            raise