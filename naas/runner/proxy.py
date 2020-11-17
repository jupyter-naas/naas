from base64 import b64encode
import escapism
import string
import os
import requests

_docker_safe_chars = set(string.ascii_letters + string.digits)
_docker_escape_char_kubernet = "-"
_docker_escape_char_docker = "_"


def escape_kubernet(s):
    """Escape a string to kubernet-safe characters"""
    return escapism.escape(
        s,
        safe=_docker_safe_chars,
        escape_char=_docker_escape_char_kubernet,
    )


def escape_docker(s):
    """Escape a string to docker-safe characters"""
    return escapism.escape(
        s,
        safe=_docker_safe_chars,
        escape_char=_docker_escape_char_docker,
    )


def encode_proxy_url(token=""):
    client = os.environ.get("JUPYTERHUB_USER", "")
    base_public_url = os.environ.get("PUBLIC_PROXY_API", "")
    client_encoded = escape_kubernet(client)
    message_bytes = client_encoded.encode("ascii")
    base64_bytes = b64encode(message_bytes)
    username_base64 = base64_bytes.decode("ascii")
    return f"{base_public_url}/{username_base64}/{token}"


class Domain:

    base_notif_url = os.environ.get("PUBLIC_PROXY_API", None)
    headers = None

    def __init__(self):
        self.headers = {
            "Authorization": f'token {os.environ.get("JUPYTERHUB_API_TOKEN", None)}'
        }

    def status(self):
        req = requests.get(url=f"{self.base_notif_url}/status")
        req.raise_for_status()
        jsn = req.json()
        return jsn

    def add(self, domain, url=None):
        token = None
        endpoint = None
        if url:
            list_url = url.split("/")
            token = list_url.pop()
            endpoint = list_url.pop()
        if "://" in domain:
            clean_domain = domain.split("://")[1]
        else:
            clean_domain = domain
        data = {"domain": clean_domain, "endpoint": endpoint, "token": token}
        req = requests.post(
            url=f"{self.base_notif_url}/proxy", headers=self.headers, json=data
        )
        req.raise_for_status()
        new_url = f"https://{clean_domain}"
        if token:
            new_url = f"{new_url}/{endpoint}/{token}"
        return new_url

    def get(self, domain):
        req = requests.get(
            url=f"{self.base_notif_url}/proxy",
            headers=self.headers,
            json={"domain": domain},
        )
        req.raise_for_status()
        jsn = req.json()
        return jsn

    def delete(self, domain):
        req = requests.delete(
            url=f"{self.base_notif_url}/proxy",
            headers=self.headers,
            json={"domain": domain},
        )
        req.raise_for_status()
        jsn = req.json()
        return jsn
