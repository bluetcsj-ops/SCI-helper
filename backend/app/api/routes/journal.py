from __future__ import annotations

import ipaddress
import re
import socket
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field


MAX_GUIDELINE_BYTES = 1_000_000
MAX_GUIDELINE_TEXT_LENGTH = 24_000


router = APIRouter()


class JournalGuidelineFetchRequest(BaseModel):
    url: str = Field(min_length=8, max_length=2048)


class JournalGuidelineFetchResponse(BaseModel):
    source_url: str
    title: str | None = None
    text: str
    character_count: int
    truncated: bool


class _GuidelineHtmlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._ignored_depth = 0
        self._title_depth = 0
        self.title_parts: list[str] = []
        self.text_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript", "svg"}:
            self._ignored_depth += 1
        if tag == "title":
            self._title_depth += 1
        if tag in {"p", "br", "li", "div", "section", "article", "h1", "h2", "h3", "tr"}:
            self.text_parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "svg"} and self._ignored_depth:
            self._ignored_depth -= 1
        if tag == "title" and self._title_depth:
            self._title_depth -= 1
        if tag in {"p", "li", "div", "section", "article", "h1", "h2", "h3", "tr"}:
            self.text_parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._ignored_depth:
            return
        cleaned = re.sub(r"\s+", " ", data).strip()
        if not cleaned:
            return
        if self._title_depth:
            self.title_parts.append(cleaned)
        self.text_parts.append(cleaned)


def _assert_public_http_url(url: str) -> str:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"}:
        raise HTTPException(status_code=400, detail="仅支持 http/https Author Guidelines URL。")
    if not parsed.hostname:
        raise HTTPException(status_code=400, detail="URL 缺少有效域名。")

    hostname = parsed.hostname.lower()
    if hostname in {"localhost", "127.0.0.1", "::1"}:
        raise HTTPException(status_code=400, detail="不允许抓取 localhost 或本机地址。")

    try:
        addresses = socket.getaddrinfo(hostname, parsed.port or (443 if parsed.scheme == "https" else 80))
    except socket.gaierror as error:
        raise HTTPException(status_code=400, detail=f"域名解析失败：{error}") from error

    for address in addresses:
        ip_text = address[4][0]
        try:
            ip_address = ipaddress.ip_address(ip_text)
        except ValueError:
            continue
        if (
            ip_address.is_private
            or ip_address.is_loopback
            or ip_address.is_link_local
            or ip_address.is_multicast
            or ip_address.is_reserved
            or ip_address.is_unspecified
        ):
            raise HTTPException(status_code=400, detail="不允许抓取内网、保留或本机地址。")

    return parsed.geturl()


def _extract_guideline_text(html: bytes, content_type: str | None) -> tuple[str | None, str, bool]:
    encoding = "utf-8"
    if content_type:
        match = re.search(r"charset=([\w.-]+)", content_type, flags=re.I)
        if match:
            encoding = match.group(1)

    decoded = html.decode(encoding, errors="replace")
    parser = _GuidelineHtmlParser()
    parser.feed(decoded)

    title = " ".join(parser.title_parts).strip() or None
    raw_text = " ".join(parser.text_parts)
    text = re.sub(r"[ \t]+", " ", raw_text)
    text = re.sub(r"\n\s+", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    truncated = len(text) > MAX_GUIDELINE_TEXT_LENGTH
    return title, text[:MAX_GUIDELINE_TEXT_LENGTH], truncated


@router.post("/guidelines/fetch", response_model=JournalGuidelineFetchResponse)
def fetch_journal_guidelines(payload: JournalGuidelineFetchRequest) -> JournalGuidelineFetchResponse:
    source_url = _assert_public_http_url(payload.url)
    request = Request(
        source_url,
        headers={
            "User-Agent": "SCI-helper-author-guideline-fetcher/0.1",
            "Accept": "text/html,application/xhtml+xml,text/plain;q=0.8,*/*;q=0.5",
        },
    )

    try:
        with urlopen(request, timeout=12) as response:
            content_type = response.headers.get("content-type")
            if content_type and "pdf" in content_type.lower():
                raise HTTPException(status_code=415, detail="当前第一版只支持 HTML/text 页面，PDF 请先手动粘贴关键文本。")
            html = response.read(MAX_GUIDELINE_BYTES + 1)
    except HTTPException:
        raise
    except HTTPError as error:
        raise HTTPException(status_code=502, detail=f"目标网站返回错误：HTTP {error.code}") from error
    except URLError as error:
        raise HTTPException(status_code=502, detail=f"抓取目标网站失败：{error.reason}") from error
    except TimeoutError as error:
        raise HTTPException(status_code=504, detail="抓取目标网站超时，请手动粘贴 Author Guidelines 文本。") from error

    if len(html) > MAX_GUIDELINE_BYTES:
        html = html[:MAX_GUIDELINE_BYTES]
    title, text, truncated = _extract_guideline_text(html, content_type)
    if len(text) < 200:
        raise HTTPException(status_code=422, detail="未能从页面提取足够的 Author Guidelines 文本，请手动粘贴关键内容。")

    return JournalGuidelineFetchResponse(
        source_url=source_url,
        title=title,
        text=text,
        character_count=len(text),
        truncated=truncated,
    )
