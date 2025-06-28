import os
import re
import socket
import logging
from urllib.parse import urljoin
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from typing import Optional, Union

from api.gpt4.utils import generar_archivo_aml, generar_xml_pain001, validar_aml_con_xsd, validar_xml_pain001

# Constants for default behavior
DEFAULT_TIMEOUT: int = 10  # seconds
DEFAULT_RETRIES: int = 3
BACKOFF_FACTOR: float = 0.3
STATUS_FORCELIST = (500, 502, 504)

class ConfigError(Exception):
    '''Raised when a required configuration is missing or invalid.'''
    pass

class ConfigLoader:
    '''Loads and validates configuration from environment variables.'''
    def __init__(self, prefix: str = "") -> None:
        self.env = os.environ
        self.prefix = prefix

    def get(self, key: str, default=None, required: bool = False) -> Optional[str]:
        '''Returns the raw env var value or default; raises if required and missing.'''
        name = f"{self.prefix}{key}" if self.prefix else key
        value = self.env.get(name, default)
        if required and value is None:
            raise ConfigError(f"Missing required config: {name}")
        return value

class SensitiveFilter(logging.Filter):
    '''Logging filter to mask sensitive data such as account numbers or tokens.'''
    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        masked = re.sub(r"(?<=\d{0,})(\d{4,})(?=\d{0,})", lambda m: '*' * len(m.group(1)), msg)
        record.msg = masked
        return True

class DNSResolver:
    @staticmethod
    def resolve(domain: str) -> str:
        try:
            return socket.gethostbyname(domain)
        except socket.gaierror as e:
            raise ConnectionError(f"DNS resolution failed for {domain}: {e}")

class HTTPClient:
    '''Configured HTTP client with retry, timeout, and TLS verification.'''
    def __init__(
        self,
        verify_ca: Union[str, bool],
        timeout: int = DEFAULT_TIMEOUT,
        retries: int = DEFAULT_RETRIES
    ) -> None:
        self.session = requests.Session()
        retry_strategy = Retry(
            total=retries,
            backoff_factor=int(BACKOFF_FACTOR),
            status_forcelist=STATUS_FORCELIST,
            allowed_methods=["HEAD", "GET", "POST"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount('https://', adapter)
        self.session.mount('http://', adapter)
        self.verify = verify_ca
        self.timeout = timeout

    def post(
        self,
        url: str,
        headers: Optional[dict] = None,
        data: Optional[str] = None
    ) -> requests.Response:
        try:
            response = self.session.post(
                url,
                headers=headers,
                data=data,
                timeout=self.timeout,
                verify=self.verify
            )
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            raise ConnectionError(f"HTTP request failed: {e}")

class BankConnector:
    '''Orchestrates secure transfer requests to the bank.'''
    def __init__(
        self,
        config: ConfigLoader,
        logger: Optional[logging.Logger] = None
    ) -> None:
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self._init_client()

    def _init_client(self) -> None:
        # Fetch raw values
        ca_bundle_raw = self.config.get('CA_BUNDLE_PATH', default='/etc/ssl/certs/ca-certificates.crt')
        timeout_raw = self.config.get('TIMEOUT', default=str(DEFAULT_TIMEOUT))
        allow_fake_raw = self.config.get('ALLOW_FAKE_BANK', default='false')
        prefix_raw = self.config.get('RED_SEGURA_PREFIX', default='')
        dns_bank_raw = self.config.get('DNS_BANCO', required=True)
        bank_domain_raw = self.config.get('DOMINIO_BANCO', required=True)
        mock_port_raw = self.config.get('MOCK_PORT', default='0')

        # Cast to proper types with defaults
        ca_bundle: Union[str, bool] = ca_bundle_raw if isinstance(ca_bundle_raw, (str, bool)) else str(ca_bundle_raw)
        timeout: int = int(timeout_raw or DEFAULT_TIMEOUT)
        allow_fake: bool = str(allow_fake_raw).lower() in ("1", "true", "yes")
        prefix: str = str(prefix_raw or '')
        dns_bank: str = str(dns_bank_raw)
        bank_domain: str = str(bank_domain_raw)
        mock_port: int = int(mock_port_raw or 0)

        self.allow_fake_bank = allow_fake
        self.validator_prefix = prefix
        self.dns_bank = dns_bank
        self.bank_domain = bank_domain
        self.mock_port = mock_port

        self.http_client = HTTPClient(
            verify_ca=ca_bundle,
            timeout=timeout
        )

    def _in_secure_network(self) -> bool:
        try:
            ip = socket.gethostbyname(socket.gethostname())
            return self.validator_prefix != '' and ip.startswith(self.validator_prefix)
        except Exception as e:
            self.logger.warning(f"Unable to determine secure network: {e}")
            return False

    def perform_transfer(
        self,
        endpoint: str,
        headers: dict,
        body: str
    ) -> str:
        '''Performs a transfer request to the bank endpoint.'''
        if self._in_secure_network():
            ip = DNSResolver.resolve(self.bank_domain)
            base_url = f"https://{ip}"
        elif self.allow_fake_bank:
            base_url = f"http://{self.dns_bank}:{self.mock_port}"
        else:
            raise ConnectionError("Not in secure network and fake bank is not allowed.")

        url = urljoin(base_url, endpoint)
        self.logger.info(f"Sending transfer request to {url}")
        self.logger.debug(f"Headers: {self._mask_sensitive(headers)} | Body: {self._mask_sensitive(body)}")

        response = self.http_client.post(url, headers=headers, data=body)

        self.logger.debug(
            f"Response status: {response.status_code} | Body: {self._mask_sensitive(response.text)}"
        )
        return response.text

    @staticmethod
    def _mask_sensitive(data):
        '''Helper to mask sensitive info in logs.'''
        if isinstance(data, dict):
            masked = {k: ('****' if any(token in k.upper() for token in ('ACCOUNT', 'TOKEN', 'KEY', 'OTP')) else v) for k, v in data.items()}
            return masked
        if isinstance(data, str):
            return re.sub(r"(?<=\d{0,})(\d{4,})(?=\d{0,})", lambda m: '*' * len(m.group(1)), data)
        return data

# Configure logger with sensitive filter
logger = logging.getLogger('bank_connector')
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
handler.addFilter(SensitiveFilter())
logger.addHandler(handler)
logger.setLevel(logging.INFO)


"""
Módulo de integración de peticiones bancarias usando BankConnector.
"""
import logging
import socket
import json
from typing import Optional, Any, Dict

from django.conf import settings



# Inicialización de configuración y conector
config = ConfigLoader(prefix='BANK_')
logger = logging.getLogger('bank_connector')
connector = BankConnector(config=config, logger=logger)


def hacer_request_seguro(
    path: str = "/api",
    metodo: str = "GET",
    datos: Optional[Any] = None,
    headers: Optional[Dict[str, str]] = None
) -> Optional[str]:
    """
    Realiza una petición segura al banco usando BankConnector.
    - path: endpoint relativo, p.ej. '/transferencia'
    - metodo: 'GET' o 'POST'
    - datos: objeto JSON serializable para POST
    - headers: cabeceras HTTP adicionales
    Devuelve el cuerpo de la respuesta como texto o None en caso de error.
    """
    headers = headers or {}
    # Serializar datos si es POST
    body = None
    if metodo.upper() != 'GET' and datos is not None:
        try:
            body = json.dumps(datos)
        except (TypeError, ValueError) as e:
            logger.error(f"Error serializando datos JSON: {e}")
            return None

    try:
        response_text = connector.perform_transfer(endpoint=path, headers=headers, body=body)
        return response_text
    except Exception as e:
        logger.error(f"Error en hacer_request_seguro: {e}")
        return None


def puerto_activo(host: str, puerto: int, timeout: int = 2) -> bool:
    """
    Comprueba si un puerto está escuchando en un host.
    """
    try:
        with socket.create_connection((host, puerto), timeout=timeout):
            return True
    except Exception:
        return False


def obtener_token_desde_simulador(
    username: str,
    password: str
) -> Optional[str]:
    """
    Solicita token JWT al simulador bancario.
    """
    headers = {'Content-Type': 'application/json'}
    datos = {"username": username, "password": password}
    # Siempre usamos POST al endpoint '/token/'
    raw = hacer_request_seguro(path='/api/token/', metodo='POST', datos=datos, headers=headers)
    if not raw:
        logger.error("No se recibió respuesta del simulador para token")
        return None
    try:
        payload = json.loads(raw)
        return payload.get('token')
    except json.JSONDecodeError as e:
        logger.error(f"JSON inválido al leer token: {e}")
        return None


def hacer_request_banco_autenticado(
    request,
    path: str = "/api",
    metodo: str = "GET",
    datos: Optional[Any] = None,
    username: str = "",
    password: str = ""
) -> Any:
    """
    Realiza petición autenticada al banco obteniendo antes JWT.
    """
    token = obtener_token_desde_simulador(username, password)
    if not token:
        return {"error": "No se pudo obtener token del simulador"}
    headers = {"Authorization": f"Bearer {token}"}
    return hacer_request_seguro(path=path, metodo=metodo, datos=datos, headers=headers)


def hacer_request_banco(
    request,
    path: str = "/api",
    metodo: str = "GET",
    datos: Optional[Any] = None,
    headers: Optional[Dict[str, str]] = None
) -> Any:
    """
    Determina modo de conexión (oficial vs mock) y hace la petición.
    """
    usar = request.session.get("usar_conexion_banco")
    headers = headers or {}

    # Si modo oficial, se autentica
    if usar == "oficial":
        token = obtener_token_desde_simulador(
            settings.BANK_SIM_USER,
            settings.BANK_SIM_PASS
        )
        if token:
            headers["Authorization"] = f"Bearer {token}"
        else:
            return {"error": "Fallo autenticación oficial"}

    # Si se debe usar conexión bancaria (oficial o sandbox)
    if usar:
        resultado = hacer_request_seguro(path=path, metodo=metodo, datos=datos, headers=headers)
        # Intentamos parseo JSON
        try:
            return json.loads(resultado) if resultado else None
        except (TypeError, json.JSONDecodeError):
            return resultado

    # Modo local mock
    dns = config.get('DNS_BANCO', default=settings.BANK_DNS)
    puerto = int(config.get('MOCK_PORT', default=str(settings.BANK_MOCK_PORT)))
    url = f"https://{dns}:{puerto}{path}"
    try:
        resp = connector.http_client.session.request(
            metodo, url, json=datos, headers=headers, timeout=connector.http_client.timeout
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Error al conectar al VPS mock: {e}")
        return None


def enviar_transferencia_conexion(
    request,
    transfer,
    token: str,
    otp: str
) -> Any:
    """
    Envía transferencia y gestiona logs, respuesta y validaciones.
    """
    body = transfer.to_schema_data()
    pid = transfer.payment_id
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
        "Idempotency-Id": pid,
        "Correlation-Id": pid,
        "Otp": otp,
    }

    logger.info(f"[TRANSFER] Enviando transferencia {pid}")
    respuesta = hacer_request_banco(request, path='/api/transferencia', metodo='POST', datos=body, headers=headers)
    if not respuesta:
        logger.error(f"[TRANSFER] Sin respuesta de conexión bancaria para {pid}")
        raise Exception("Sin respuesta de la conexión bancaria")

    # Si es dict, asumimos JSON; si string, lo devolvemos bruto
    if isinstance(respuesta, dict):
        auth_id = respuesta.get('authId')
        status = respuesta.get('transactionStatus')
        transfer.auth_id = auth_id
        transfer.status = status or transfer.status
        transfer.save()
    else:
        logger.warning(f"[TRANSFER] Respuesta no JSON para {pid}: {respuesta}")

    # Validaciones posteriores
    try:
        xml_path = generar_xml_pain001(transfer, pid)
        aml_path = generar_archivo_aml(transfer, pid)
        validar_xml_pain001(xml_path)
        validar_aml_con_xsd(aml_path)
        logger.info(f"[TRANSFER] Validación XML/AML completada para {pid}")
    except Exception as e:
        logger.error(f"[ERROR] Validación XML/AML para {pid}: {e}")

    return respuesta
