#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Utilities to perform HTTP requests to the bank via an SSH tunnel.
This module uses :mod:`paramiko` and :mod:`sshtunnel` to establish a
forwarding tunnel for secure bank communication.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator, Optional

import requests
from sshtunnel import SSHTunnelForwarder


SSH_HOST = os.getenv("SSH_HOST")
SSH_PORT = int(os.getenv("SSH_PORT", "22"))
SSH_USER = os.getenv("SSH_USER")
SSH_KEY_PATH = os.getenv("SSH_KEY_PATH")
SSH_PASSWORD = os.getenv("SSH_PASSWORD")


@contextmanager
def ssh_tunnel(remote_host: str, remote_port: int) -> Generator[SSHTunnelForwarder, None, None]:
    """Create an SSH tunnel forwarding *remote_host:remote_port* to a local port."""
    if not SSH_HOST or not SSH_USER:
        raise RuntimeError("SSH credentials are not configured")

    server = SSHTunnelForwarder(
        (SSH_HOST, SSH_PORT),
        ssh_username=SSH_USER,
        ssh_password=SSH_PASSWORD,
        ssh_pkey=SSH_KEY_PATH,
        remote_bind_address=(remote_host, remote_port),
        local_bind_address=("127.0.0.1", 0),
    )
    server.start()
    try:
        yield server
    finally:
        server.stop()


def ssh_request(
    method: str,
    remote_host: str,
    path: str,
    *,
    remote_port: int = 443,
    headers: Optional[dict] = None,
    json: Optional[dict] = None,
    timeout: int = 10,
) -> requests.Response:
    """Perform an HTTP request over an SSH tunnel."""
    headers = headers or {}
    with ssh_tunnel(remote_host, remote_port) as tunnel:
        url = f"https://127.0.0.1:{tunnel.local_bind_port}{path}"
        response = requests.request(method, url, headers=headers, json=json, timeout=timeout, verify=False)
        return response