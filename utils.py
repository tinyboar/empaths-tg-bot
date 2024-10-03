# utils.py

def escape_html(text):
    """
    Экранирует HTML-символы в строке, чтобы избежать ошибок парсинга в Telegram.
    """
    if not isinstance(text, str):
        return text
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

