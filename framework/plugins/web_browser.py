import requests
from bs4 import BeautifulSoup

def fetch_website_title(url: str) -> str:
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.title.string if soup.title else "Нет заголовка"
        return title.strip()
    except Exception as e:
        return f"Ошибка при посещении сайта: {e}"