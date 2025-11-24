# parse_eml.py
import os
from email import message_from_bytes
from email.policy import default
from bs4 import BeautifulSoup
import eml_parser


def _extract_realm_from_html(html: str) -> dict | None:
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


def extract_realm_config_from_eml(eml_path: str) -> dict:
    """
    Читает .eml файл, ищет вложения типа message/rfc822,
    извлекает HTML из каждого, ищет таблицу с 'Название realm'.
    Возвращает словарь с параметрами.
    """
    if not os.path.isfile(eml_path):
        raise FileNotFoundError(f"Файл не найден: {eml_path}")

    with open(eml_path, "rb") as f:
        raw = f.read()

    # ВАЖНО: include_attachment_data=True — чтобы получить тело вложений
    parser = eml_parser.EmlParser(include_attachment_data=True)
    parsed = parser.decode_email_bytes(raw)

    attachments = parsed.get("attachment", [])
    if not attachments:
        raise ValueError("В .eml нет вложений")

    for att in attachments:
        ct = att.get("content_header", {}).get("content-type", [""])[0]
        if "message/rfc822" in ct:
            try:
                raw_inner = att["raw"]  # bytes вложенного письма
                inner_msg = message_from_bytes(raw_inner, policy=default)

                # Ищем HTML-тело во вложенном письме
                html_content = None
                for part in inner_msg.walk():
                    if part.get_content_type() == "text/html":
                        html_content = part.get_content()
                        break

                if not html_content:
                    continue

                config = _extract_realm_from_html(html_content)
                if config:
                    print(f"✅ Найдена конфигурация realm в вложении (hash: {att['hash']['sha256'][:12]})")
                    return config

            except Exception as e:
                print(f"⚠️ Ошибка при обработке вложения: {e}")
                continue

    raise ValueError("Таблица с 'Название realm' не найдена ни в одном вложении")
