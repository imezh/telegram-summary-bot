import trafilatura


def fetch_article(url: str) -> str:
    downloaded = trafilatura.fetch_url(url)
    text = trafilatura.extract(downloaded)
    if not text:
        raise ValueError("Не удалось извлечь текст со страницы.")
    return text
