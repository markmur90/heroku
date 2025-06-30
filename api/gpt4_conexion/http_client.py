import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

class HTTPClient:
    def __init__(self, verify: bool, timeout: int, retries: int):
        self._session = requests.Session()
        retry = Retry(total=retries, backoff_factor=int(0.5), status_forcelist=[500,502,504])
        adapter = HTTPAdapter(max_retries=retry)
        self._session.mount('https://', adapter)
        self._session.mount('http://', adapter)
        self.verify = verify
        self.timeout = timeout

    def request(self, method: str, url: str, **kwargs) -> requests.Response:
        resp = self._session.request(method, url, timeout=self.timeout, verify=self.verify, **kwargs)
        resp.raise_for_status()
        return resp