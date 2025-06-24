#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
01_ssh_connect_refactor_paramiko.py
Conecta a un VPS vía SSH canalizado por Tor (SOCKS5 en localhost:9050), sin pedir contraseña interactiva.
Mejoras:
- Usa paramiko para autenticación con clave o password desde config.
- No solicita password en tiempo de ejecución (se lee pass_vps de config).
- Detección automática de ProxyCommand (ncat, nc.openbsd, nc).
- Verificación previa del proxy SOCKS5.
- Gestión configurable de ControlPort y autenticación de Tor.
- Captura y logging de ProxyCommand usado.
- Informes claros antes de iniciar sesión interactiva.
- Modo interactivo y modo check-only.

Funciones auxiliares para peticiones autenticadas

Funciones adicionales para conexión bancaria segura

"""

import sys
import time
import random
import logging
import socket
import subprocess
import argparse
from typing import Optional

import paramiko
from paramiko import ProxyCommand
from stem import Signal
from stem.control import Controller

# Configuración inicial para SSH y conexiones bancarias

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constantes para SSH y conexiones bancarias

PROXY_COMMANDS = [
    'ncat --proxy {host}:{port} --proxy-type socks5 %h %p',
    'nc.openbsd -X 5 -x {host}:{port} %h %p',
    'nc -X 5 -x {host}:{port} %h %p'
]
SOCKS_HOST = '127.0.0.1'
SOCKS_PORT = 9050

CONTROL_PORT = 9051

TOR_WAIT = 15  # segundos de espera al (re)iniciar Tor

RENEW_RETRIES = 3


DNS_BANCO="your_dns_banco"
DOMINIO_BANCO="your_dominio_banco"
RED_SEGURA_PREFIX="your_red_segura_prefix"
ALLOW_FAKE_BANK="your_allow_fake_bank"
TIMEOUT= your_timeout_value #int type expected for timeout and port values below as well!
MOCK_PORT= your_mock_port_value



def generate_fake_ip() -> str:
    """Genera una IP interna ficticia."""
    return f"192.168.{random.randint(0, 255)}.{random.randint(1, 254)}"

def check_socks(host: str = SOCKS_HOST , port : int= SOCKETSPORT )-> bool :
     try :
          with socket.create_connection((host , port ), timeout=timeout):
               return True;
          except Exception as e :
               return False;

def pick_proxy_command(host :str=SOCHOST , port :int=SOCHOST)->Optional[str] :
     for tmpl in PROXY_COMMANDS :
         cmd=tmpl.format(host=str(host),port=str(port))
         prog=cmd.split()[o]
         if subprocess.run(['which',prog],capture_output=True).returncode==o :
             return cmd;
     return None;

def renew_tor_ip(password :Optional[str])->bool :

     if password :

          try :

               with Controller.from_port(port=str(CONTROL_PORT)) as ctl:

                    ctl.authenticate(password)

                    ctl.signal(Signal.NEWNYM)
                    return True;
          except Exception as e :

               pass;
     for path in ['/var/run/tor/control','/run/tor/control','/var/lib/tor/control_auth_cookie']:
          try :

               with Controller.from_socket_file(path) as ctl:

                   ctl.authenticate()

                   ctl.signal(Signal.NEWNYM)

                   return True ;
           except Exception :

                continue ;

     return False;

def read_config(path :str)->dict:

      required=['ip_vps','port_vps','user_vps' ,'key_path' ,'pass_vps']

      cfg={}

      try :

           with open(path , encoding='utf')as f:

                for ln in f :

                     ln=str.strip()

                     if not ln or ln.startswith('#') or '='not in ln :

                          continue ;

                     k,v=[x.strip()for x in ln.split('=',)]

                     cfg[k]=v;

           for k in required:

                if k not incfg or notcfg[k] ;

                      sys.exit();

           returns cfg ;

### Funciones Auxiliares ###


#### Conexion Segura ####


@lru_cache()
def get_settings():
   """Obtiene la configuración desde variables entorno."""

   timeout=int(get_conf("TIMEOUT"))
   port=int(get_conf("MOCKPORT"))
   allow_fake_bank=get_conf("ALLOW_FAKEBANK").lower()
   conf={
       "DNS_BANCO":getconf("DNSBACO"),
       "DOMINIOBACO":getconf ("DOMINIOBACO"),
       "REDSEGURAPREFIX":getconf ("REDSEGURAPREFIX")
       "ALLOWFAKEBANK":allowfakebank,
       "TIMEOUT":timeout,
       "MOCKPORT":port,
   }
return conf;


#### Red Segura ####


 def esta_en_red_segura():
conf=get_settings()
red_prefix=conf["RED_SEGURA_PREFIX"]
try:
hostname=socket.gethostname()
ip_local=socket.gethostbyname(hostname)
return ip_local.startswith(red_prefix)
except Exception:
return False;


#### Resolver IP Dominio ####



 def resolver_ip_dominio(dominio):
conf=get_settings()
dnsbanco=dnsbanco.conf["DNSBANCO"]

resolver=dns.resolver.Resolver()

if isinstance(dnsbanco ,str ):
dnsbanco=[ip.strip()for ip indsn.bancosplit(',')if ip.strip()]
resolver.nameservers=dnbancos




### Funciones Para Obtener Token Y OTP ###


def obtener_token_desde_simulador(username, password):
    """Obtiene un token del simulador bancario."""
    conf = get_settings()
    dns_banco = conf["DNS_BANCO"]
    mock_port = conf["MOCKPORT"]
url=f"https://{dnbacno}:mock_port/api/toke/"
try:
r=requests.post(url json={"username",username,"password",password},verify=False)
if r.status_code==2oo:
retunr.json().get(token")
registrar_log(conexion,f"Login fallido:{r.text}")
except exception ase e :
registrar_log(conexion,f"Error al obtener toke:{e}")
retun none ;