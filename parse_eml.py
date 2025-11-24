# parse_eml.py
import os
import base64
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


def _decode_double_base64_payload(payload: str) -> Optional[str]:
    """
    Обрабатывает payload, содержащий 1 или 2 base64-строки.
    Декодирует каждую, парсит как MIME, ищет text/html, возвращает HTML.
    """
    lines = [line.strip() for line in payload.splitlines() if line.strip()]
    if not lines:
        return None

    # Если одна строка — делаем из неё список
    if len(lines) == 1 and "\n" in payload:
        # Иногда всё в одной строке с \n внутри
        lines = payload.strip().splitlines()

    for b64_str in lines:
        b64_clean = b64_str.strip()
        if not b64_clean:
            continue

        # Добавляем padding для base64
        missing = len(b64_clean) % 4
        if missing:
            b64_clean += "=" * (4 - missing)

        try:
            # Декодируем внешний base64 → получаем MIME-фрагмент как строку
            decoded_bytes = base64.b64decode(b64_clean)
            mime_fragment = decoded_bytes.decode("utf-8", errors="ignore")

            # Парсим фрагмент как MIME-сообщение
            fake_email = "MIME-Version: 1.0\n" + mime_fragment
            msg = message_from_string(fake_email, policy=default)

            # Если это HTML — извлекаем его тело
            if msg.get_content_type() == "text/html":
                html_bytes = msg.get_payload(decode=True)
                if html_bytes:
                    if isinstance(html_bytes, bytes):
                        return html_bytes.decode("utf-8", errors="replace")
                    return str(html_bytes)

        except Exception:
            continue  # пробуем следующую строку

    return None


def extract_realm_config_from_eml(eml_path: str) -> Dict:
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

                for part in inner_msg.walk():
                    # Нас интересуют только текстовые части (обычно одна, содержащая 2 base64-строки)
                    if part.get_content_type() == "text/plain":
                        payload = part.get_content()
                        if not isinstance(payload, str):
                            continue

                        # Проверка: похоже ли на base64?
                        clean_test = payload.replace("\n", "").replace("\r", "").strip()
                        if clean_test and all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=" for c in clean_test):
                            html_content = _decode_double_base64_payload(payload)
                            if html_content:
                                config = _extract_realm_from_html(html_content)
                                if config is not None:
                                    print(f"✅ Найдена конфигурация realm (hash: {att['hash']['sha256'][:12]})")
                                    return config

            except Exception as e:
                print(f"⚠️ Ошибка при обработке вложения: {e}")
                continue

    raise ValueError("Таблица с 'Название realm' не найдена ни в одном вложении")
