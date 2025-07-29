import logging

import aiosqlite

from config import DB_PATH

logger = logging.getLogger(__name__)


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS films (
                user_id INTEGER,
                name TEXT,
                rating REAL,
                year INTEGER,
                genre TEXT,
                description TEXT,
                tag TEXT,
                review TEXT,
                poster_url TEXT,
                trailer TEXT,
                PRIMARY KEY (user_id, name)
            )
        """
        )
        await db.commit()


async def load_films(user_id: int):
    try:
        # Відкриваємо підключення до бази даних
        async with aiosqlite.connect(DB_PATH) as db:
            # Вибираємо всі фільми для поточного користувача
            cursor = await db.execute(
                "SELECT name, rating, year, genre, description, tag, review, poster_url, trailer FROM films WHERE user_id = ?",
                (user_id,),
            )
            rows = await cursor.fetchall()
            films = {}
            for row in rows:
                # Формуємо словник фільмів
                (
                    name,
                    rating,
                    year,
                    genre,
                    description,
                    tag,
                    review,
                    poster_url,
                    trailer,
                ) = row
                films[name] = {
                    "rating": rating,
                    "year": year,
                    "genre": genre,
                    "description": description,
                    "tag": tag,
                    "review": review,
                    "poster_url": poster_url,
                    "trailer": trailer,
                }
            return films
    except Exception as e:
        logger.error(f"Error loading films for user {user_id}: {e}")
        return {}


async def save_film(user_id: int, film_data: dict):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                """
                INSERT INTO films (user_id, name, rating, year, genre, description, tag, review, poster_url, trailer)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id, name) DO UPDATE SET
                    rating=excluded.rating,
                    year=excluded.year,
                    genre=excluded.genre,
                    description=excluded.description,
                    tag=excluded.tag,
                    review=excluded.review,
                    poster_url=excluded.poster_url,
                    trailer=excluded.trailer
                """,
                (
                    user_id,
                    film_data.get("name"),
                    film_data.get("rating"),
                    film_data.get("year"),
                    film_data.get("genre"),
                    film_data.get("description"),
                    film_data.get("tag"),
                    film_data.get("review"),
                    film_data.get("poster_url"),
                    film_data.get("trailer"),
                ),
            )
            await db.commit()
            return True
    except Exception as e:
        logger.error(
            f"Error saving film '{film_data.get('name')}' for user {user_id}: {e}"
        )
        return False
