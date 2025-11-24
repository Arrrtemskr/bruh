# parse_eml.py
import os
from email import message_from_bytes, message_from_string
from email.policy import default
from bs4 import BeautifulSoup
import eml_parser
from typing import Optional, Dict


def _extract_realm_from_html(html: str) -> Optional[Dict]:
    """Ищет таблицу с заголовком 'Название realm' и возвращает первую строку как dict."""
    if not html:
        return None
    soup = BeautifulSoup(html, "html.parser")
    for table in soup.find_all("table"):
        header_row = table.find("tr")
        if not header_row:
            continue
        headers = [cell.get_text(strip=True) for cell in header_row.find_all(["th", "td"])]
        if "Название realm" not in headers:
            continue
        data_rows = table.find_all("tr")[1:]
        if not data_rows:
            continue
        first_row = data_rows[0]
        cells = first_row.find_all(["td", "th"])
        if len(cells) != len(headers):
            continue
        result = {}
        for h, c in zip(headers, cells):
            val = c.get_text(strip=True)
            if val.lower() == "true":
                val = True
            elif val.lower() == "false":
                val = False
            result[h] = val
        return result
    return None


def _parse_multipart_fragment(fragment: str) -> Optional[str]:
    """
    Пытается распарсить строку вида:
        Content-Type: text/html; ...
        Content-Transfer-Encoding: base64
        ...
        <base64 data>
    и вернуть декодированное тело.
    """
    try:
        # Добавляем обязательный заголовок MIME-Version
        fake_msg_str = "MIME-Version: 1.0\n" + fragment
        msg = message_from_string(fake_msg_str, policy=default)
        payload = msg.get_payload(decode=True)
        if payload is None:
            return None
        if isinstance(payload, bytes):
            return payload.decode("utf-8", errors="replace")
        return str(payload)
    except Exception:
        return None


def extract_realm_config_from_eml(eml_path: str) -> Dict:
    """
    Читает .eml файл, ищет вложения типа message/rfc822,
    извлекает HTML (даже если он вложен как MIME-фрагмент с base64),
    ищет таблицу с 'Название realm', возвращает конфигурацию.
    """
    if not os.path.isfile(eml_path):
        raise FileNotFoundError(f"Файл не найден: {eml_path}")

    with open(eml_path, "rb") as f:
        raw = f.read()

    parser = eml_parser.EmlParser(include_attachment_data=True)
    parsed = parser.decode_email_bytes(raw)

    attachments = parsed.get("attachment", [])
    if not attachments:
        raise ValueError("В .eml нет вложений")

    for att in attachments:
        ct = att.get("content_header", {}).get("content-type", [""])[0]
        if "message/rfc822" in ct:
            try:
                raw_inner = att["raw"]
                inner_msg = message_from_bytes(raw_inner, policy=default)

                # Обходим все части вложенного письма
                for part in inner_msg.walk():
                    if not part.get_content_type().startswith("text/"):
                        continue

                    payload = part.get_content()
                    if not isinstance(payload, str):
                        continue

                    html_content = None

                    # Сценарий 1: payload — это уже чистый HTML
                    if "<html" in payload.lower() or "<table" in payload.lower():
                        html_content = payload

                    # Сценарий 2: payload содержит MIME-заголовки (Content-Type, base64 и т.д.)
                    elif "Content-Type:" in payload and "Content-Transfer-Encoding:" in payload:
                        decoded = _parse_multipart_fragment(payload)
                        if decoded and ("<html" in decoded.lower() or "<table" in decoded.lower()):
                            html_content = decoded

                    if html_content:
                        config = _extract_realm_from_html(html_content)
                        if config is not None:
                            print(f"✅ Найдена конфигурация realm в вложении (hash: {att['hash']['sha256'][:12]})")
                            return config

            except Exception as e:
                print(f"⚠️ Ошибка при обработке вложения: {e}")
                continue

    raise ValueError("Таблица с 'Название realm' не найдена ни в одном вложении")
