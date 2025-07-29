import difflib
import html
import logging
from datetime import datetime

from aiohttp import ClientSession

from config import API_KEY

logger = logging.getLogger(__name__)


def validate_text_field(text: str, max_len: int):
    # Обрізаємо пробіли з обох боків
    text = text.strip()
    # Перевіряємо, чи поле не порожнє
    if not text:
        return False, "Field cannot be empty."
    # Перевіряємо, чи не перевищує максимальну довжину
    if len(text) > max_len:
        return False, f"Too long (max {max_len} characters)."
    return True, text


def format_film_info(name, info):
    text = (
        f"🎬 <b>{html.escape(name)}</b> ({info['year']})\n"
        f"🎭 Genre: {html.escape(str(info['genre']))}\n"
        f"⭐ Rating: {info['rating']}/10\n"
        f"📝 Description: {html.escape(str(info['description']))}\n"
        f"🏷️ Tag: {html.escape(str(info.get('tag', 'Not set')))}"
    )
    review = info.get("review")
    if review:
        review_lower = review.lower()
        if review_lower == "like":
            text += f"\n🗒️ Review: 👍"
        elif review_lower == "dislike":
            text += f"\n🗒️ Review: 👎"

    if info.get("poster_url"):
        text += f"\n<a href=\"{html.escape(info['poster_url'])}\">Poster</a>"
    if info.get("trailer"):
        text += f"\n<a href=\"{html.escape(info['trailer'])}\">Trailer</a>"
    return text


def is_valid_year(year: int, min_year=1888, max_year=None):
    if max_year is None:
        max_year = datetime.now().year + 5
    return min_year <= year <= max_year


def is_valid_rating(rating: float):
    return 1 <= rating <= 10


def find_similar_films_by_description(user_input, films, threshold=0.2, top_n=5):
    user_input = user_input.strip().lower()
    matched = []
    for name, info in films.items():
        description = str(info.get("description", "")).lower()
        similarity = difflib.SequenceMatcher(None, user_input, description).ratio()
        if similarity >= threshold:
            matched.append((similarity, name, info))
    matched.sort(reverse=True)
    return matched[:top_n]


async def search_tmdb_film(name, user_language):
    try:
        # Відповідність мов користувача форматам TMDB
        lang_map = {"ru": "ru-RU", "en": "en-US", "uk": "uk-UA"}
        tmdb_lang = lang_map.get(user_language[:2], "en-US")  # Вибір мови або дефолт

        # Відкриваємо асинхронну сесію HTTP клієнта
        async with ClientSession() as session:
            # Формуємо URL для пошуку фільму
            search_url = "https://api.themoviedb.org/3/search/movie"
            params = {"api_key": API_KEY, "query": name, "language": tmdb_lang}
            # Виконуємо запит на пошук фільму
            async with session.get(search_url, params=params) as resp:
                if resp.status != 200:
                    # Логування помилки отримання результатів пошуку
                    logging.error(
                        f"Помилка пошуку фільму '{name}': статус {resp.status}"
                    )
                    return None, None, "Помилка: не вдалося отримати дані з TMDB."
                data = await resp.json()

            results = data.get("results", [])
            if not results:
                return None, None, "Фільм не знайдено."

            film = results[0]
            film_id = film["id"]

            # Отримання детальної інформації про фільм
            details_url = f"https://api.themoviedb.org/3/movie/{film_id}"
            async with session.get(
                details_url, params={"api_key": API_KEY, "language": tmdb_lang}
            ) as resp:
                if resp.status != 200:
                    logging.error(
                        f"Помилка отримання деталей фільму ID {film_id}: статус {resp.status}"
                    )
                    return None, None, "Помилка: не вдалося отримати деталі фільму."
                details = await resp.json()

            trailer = None
            # Отримання відео (трейлерів)
            videos_url = f"https://api.themoviedb.org/3/movie/{film_id}/videos"
            async with session.get(
                videos_url, params={"api_key": API_KEY, "language": "en-US"}
            ) as resp:
                if resp.status != 200:
                    # Якщо відео не вдалося отримати — логувати, але не припиняти
                    logging.error(
                        f"Помилка отримання відео для фільму ID {film_id}: статус {resp.status}"
                    )
                    trailer = None
                else:
                    videos_data = await resp.json()
                    for video in videos_data.get("results", []):
                        if video["type"] == "Trailer" and video["site"] == "YouTube":
                            trailer = f"https://www.youtube.com/watch?v={video['key']}"
                            break

            # Витягуємо основні дані про фільм
            title = details.get("title", "No name")
            year = details.get("release_date", "")[:4]
            genres = ", ".join([g["name"] for g in details.get("genres", [])])
            rating = round(float(details.get("vote_average", 0)), 1)
            overview = details.get("overview", "No description.")
            poster_url = (
                f"https://image.tmdb.org/t/p/w500{details['poster_path']}"
                if details.get("poster_path")
                else None
            )

            film_data = {
                "year": year,
                "genre": genres,
                "rating": rating,
                "description": overview,
                "poster_url": poster_url,
                "trailer": trailer,
            }

            # Повертаємо назву, словник з даними та форматований текст
            return title, film_data, format_film_info(title, film_data)

    except Exception as e:
        # Логування серйозної помилки з трасуванням стека
        logging.exception(f"Критична помилка під час пошуку фільму '{name}': {e}")
        return None, None, f"Сталася помилка під час пошуку фільму: {e}"
