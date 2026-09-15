"""Miniatura automática de un enlace: la imagen Open Graph de la página.

Booking, Agoda, Hostelworld… publican `og:image` con la foto del alojamiento,
pero a un navegador "normal" le sirven una página anti-bot (Booking responde
202 con un reto de JS). A los crawlers sociales (Facebook, WhatsApp) les dan
el HTML completo con los metadatos, porque de ahí salen las previsualizaciones
al compartir: por eso el User-Agent es el de facebookexternalhit. Airbnb y
Expedia bloquean igualmente; ahí no hay miniatura y ya está.

La imagen se DESCARGA y se guarda en uploads/{trip_id} (como las portadas):
sin hotlinking (los CDNs de hoteles lo cortan o rotan las URLs firmadas) y
sin filtrar la IP del usuario a terceros al abrir la pestaña.

Todo es best-effort: cualquier fallo devuelve None y el enlace se guarda sin
imagen.
"""

from __future__ import annotations

import html
import ipaddress
import logging
import re
import socket
import ssl
from urllib.parse import urljoin, urlsplit

import certifi
import httpx

log = logging.getLogger("tt.links")

USER_AGENT = "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)"
PAGE_TIMEOUT = 8.0
MAX_PAGE_BYTES = 3 * 1024 * 1024  # las fichas de Booking pesan ~1,7 MB
MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_REDIRECTS = 5

IMAGE_SUFFIX = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}

# <meta property="og:image" content="…"> en cualquier orden de atributos;
# se acepta también name= (Hostelworld lo duplica así) y twitter:image
_META_RE = re.compile(r"<meta\b[^>]*>", re.IGNORECASE)
_ATTR_RE = re.compile(r"""([a-zA-Z:-]+)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'>]+))""")
_LINK_IMAGE_SRC_RE = re.compile(
    r"""<link\b[^>]*rel\s*=\s*["']?image_src["']?[^>]*href\s*=\s*["']([^"']+)["']""",
    re.IGNORECASE,
)
_PREFERRED = ("og:image:secure_url", "og:image", "twitter:image", "twitter:image:src")


def _attrs(tag: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for key, v1, v2, v3 in _ATTR_RE.findall(tag):
        out[key.lower()] = v1 or v2 or v3
    return out


def extract_image_url(page: str, base_url: str) -> str | None:
    """URL absoluta de la imagen de previsualización de una página, o None."""
    candidates: dict[str, str] = {}
    for tag in _META_RE.findall(page):
        attrs = _attrs(tag)
        key = (attrs.get("property") or attrs.get("name") or "").lower()
        content = attrs.get("content")
        if key in _PREFERRED and content and key not in candidates:
            candidates[key] = content
    for key in _PREFERRED:
        if key in candidates:
            return urljoin(base_url, html.unescape(candidates[key]).strip())
    match = _LINK_IMAGE_SRC_RE.search(page)
    if match:
        return urljoin(base_url, html.unescape(match.group(1)).strip())
    return None


def is_public_host(host: str) -> bool:
    """False si el host resuelve a una IP privada/loopback/link-local: el
    servidor no debe usarse para husmear la red interna (SSRF)."""
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return False
    if not infos:
        return False
    for info in infos:
        try:
            ip = ipaddress.ip_address(info[4][0])
        except ValueError:
            return False
        if not ip.is_global:
            return False
    return True


def _check_url(url: str) -> bool:
    parts = urlsplit(url)
    return parts.scheme in ("http", "https") and bool(parts.hostname) and is_public_host(
        parts.hostname
    )


def _get(client: httpx.Client, url: str, limit: int) -> tuple[str, bytes, str] | None:
    """GET siguiendo hasta MAX_REDIRECTS saltos, comprobando cada destino, y
    leyendo como mucho `limit` bytes. Devuelve (url final, cuerpo, content-type)."""
    for _ in range(MAX_REDIRECTS + 1):
        if not _check_url(url):
            return None
        with client.stream("GET", url) as resp:
            if resp.is_redirect:
                target = resp.headers.get("location")
                if not target:
                    return None
                url = urljoin(url, target)
                continue
            if resp.status_code != 200:
                return None
            content_type = resp.headers.get("content-type", "").split(";")[0].strip().lower()
            chunks: list[bytes] = []
            size = 0
            for chunk in resp.iter_bytes():
                size += len(chunk)
                if size > limit:
                    return None
                chunks.append(chunk)
            return url, b"".join(chunks), content_type
    return None


def _ssl_context() -> ssl.SSLContext:
    """Contexto TLS con lista de cifrados explícita.

    ⚠️ No es cosmético: el WAF de Booking (AWS WAF en CloudFront) clasifica
    por huella TLS y al ClientHello por defecto de Python/OpenSSL 3.5 en la
    imagen le devuelve un reto (202 vacío) sea cual sea el User-Agent; con
    cualquier contexto propio (otra lista de cifrados, sin tickets, TLS 1.2)
    sirve la ficha entera. Verificado desde el pod: mismo código, misma IP,
    202 con el contexto por defecto y 200 con este.
    """
    ctx = ssl.create_default_context(cafile=certifi.where())
    ctx.set_ciphers("ECDHE+AESGCM:ECDHE+CHACHA20:!aNULL")
    ctx.options |= ssl.OP_NO_TICKET
    return ctx


def fetch_preview_image(url: str) -> tuple[bytes, str] | None:
    """Descarga la imagen OG de `url`; devuelve (bytes, sufijo) o None."""
    try:
        with httpx.Client(
            timeout=PAGE_TIMEOUT,
            follow_redirects=False,
            headers={"User-Agent": USER_AGENT, "Accept-Language": "es,en;q=0.8"},
            verify=_ssl_context(),
        ) as client:
            page = _get(client, url, MAX_PAGE_BYTES)
            if page is None or not page[2].startswith("text/html"):
                return None
            final_url, body, _ = page
            image_url = extract_image_url(body.decode("utf-8", errors="replace"), final_url)
            if not image_url:
                return None
            image = _get(client, image_url, MAX_IMAGE_BYTES)
            if image is None:
                return None
            _, content, content_type = image
            suffix = IMAGE_SUFFIX.get(content_type)
            if suffix is None or not content:
                return None
            return content, suffix
    except (httpx.HTTPError, ValueError, OSError) as exc:
        log.info("sin miniatura para %s: %s", url, exc)
        return None
