import difflib
import html
import random

from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove
from aiohttp import ClientSession
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException

from config import API_KEY
from db import load_films, save_film
from keyboards import add_or_no_kb, inspect_kb, main_kb, random_kb, viewed_or_not_kb
from states import InspectFilmState
from utils import format_film_info, search_tmdb_film

router = Router(name=__name__)


@router.message(lambda m: m.text == "Inspect films")
async def inspect_handler(message: types.Message):
    await message.answer("Select an option:", reply_markup=inspect_kb)


@router.message(lambda m: m.text == "Inspect all films")
async def inspect_all_films(message: types.Message):
    films = await load_films(message.from_user.id)
    if not films:
        await message.answer("No movies.", reply_markup=main_kb)
        return
    sorted_films = sorted(
        films.items(), key=lambda item: float(item[1]["rating"]), reverse=True
    )
    result = "\n\n".join([format_film_info(name, info) for name, info in sorted_films])
    await message.answer(
        f"<b>Movie rating:</b>\n\n{result}",
        parse_mode="HTML",
        reply_markup=main_kb,
        disable_web_page_preview=(len(sorted_films) > 1),
    )


@router.message(lambda m: m.text == "Inspect by name")
async def inspect_by_name_handler(message: types.Message, state: FSMContext):
    await message.answer("Enter the movie title:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(InspectFilmState.waiting_for_name)


@router.message(lambda m: m.text == "Inspect by rating")
async def inspect_by_rating_handler(message: types.Message, state: FSMContext):
    await message.answer("Enter the movie rating:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(InspectFilmState.waiting_for_rating)


@router.message(lambda m: m.text == "Inspect by year")
async def inspect_by_year_handler(message: types.Message, state: FSMContext):
    await message.answer("Enter the movie year:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(InspectFilmState.waiting_for_year)


@router.message(lambda m: m.text == "Inspect by genre")
async def inspect_by_genre_handler(message: types.Message, state: FSMContext):
    await message.answer("Enter the movie genre:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(InspectFilmState.waiting_for_genre)


@router.message(lambda m: m.text == "Inspect by description")
async def inspect_by_description_handler(message: types.Message, state: FSMContext):
    await message.answer(
        "Enter the movie description:", reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(InspectFilmState.waiting_for_description)


@router.message(lambda m: m.text == "Inspect random film")
async def inspect_random_film(message: types.Message, state: FSMContext):
    await message.answer("Select an option:", reply_markup=random_kb)
    await state.set_state(InspectFilmState.waiting_for_random)


@router.message(lambda m: m.text == "Inspect by tag")
async def inpect_by_tag_start(message: types.Message, state: FSMContext):
    await message.answer("Enter the movie tag:", reply_markup=viewed_or_not_kb)
    await state.set_state(InspectFilmState.waiting_for_tag)


@router.message(InspectFilmState.waiting_for_name)
async def film_by_name(message: types.Message, state: FSMContext):
    films = await load_films(message.from_user.id)
    name = message.text.strip()
    try:
        user_lang = detect(name)
    except LangDetectException:
        user_lang = "en"

    if not films:
        title, film_data, result = await search_tmdb_film(name, user_lang)
        if result:
            await message.answer(
                f"Films not found. Film from TMDb:\n{result}\n\nWould you like to add this movie to the database? (y/n):",
                parse_mode="HTML",
                reply_markup=add_or_no_kb,
            )
            await state.update_data(last_tmdb_film={**film_data, "name": title})
            await state.set_state(InspectFilmState.waiting_for_answer)
        else:
            await message.answer("Film not found.", reply_markup=main_kb)
        return

    if name in films:
        info = films[name]
        await message.answer(
            format_film_info(name, info), parse_mode="HTML", reply_markup=main_kb
        )
    else:
        title, film_data, result = await search_tmdb_film(name, user_lang)
        if result:
            await message.answer(
                f"Film not found. Film from TMDb:\n{result}\n\nWould you like to add this movie to the database? (y/n):",
                parse_mode="HTML",
                reply_markup=add_or_no_kb,
            )
            await state.update_data(last_tmdb_film={**film_data, "name": title})
            await state.set_state(InspectFilmState.waiting_for_answer)
            return
        else:
            await message.answer("Film not found.", reply_markup=main_kb)

    await state.clear()


@router.message(InspectFilmState.waiting_for_rating)
async def film_by_rating(message: types.Message, state: FSMContext):
    films = await load_films(message.from_user.id)

    if not films:
        await message.answer("No films added.")
        await state.clear()
        return

    rating = message.text.strip()

    matched_films = [
        (name, info)
        for name, info in films.items()
        if float(rating) == float(info["rating"])
    ]

    if not matched_films:
        await message.answer("No movies found in this rating", reply_markup=main_kb)
    else:
        result = "\n\n".join(
            [format_film_info(name, info) for name, info in matched_films]
        )
        await message.answer(
            f"<b>Movies in rating '{html.escape(message.text)}':</b> \n\n{result}",
            parse_mode="HTML",
            reply_markup=main_kb,
            disable_web_page_preview=(len(matched_films) > 1),
        )

    await state.clear()


@router.message(InspectFilmState.waiting_for_year)
async def film_by_year(message: types.Message, state: FSMContext):
    print(f"[User input] {message.text}")
    films = await load_films(message.from_user.id)

    if not films:
        await message.answer("No films added.")
        await state.clear()
        return

    year = message.text.strip()

    matched_films = [
        (name, info) for name, info in films.items() if int(year) == int(info["year"])
    ]

    if not matched_films:
        await message.answer("No movies found in this rating", reply_markup=main_kb)
    else:
        result = "\n\n".join(
            [format_film_info(name, info) for name, info in matched_films]
        )
        await message.answer(
            f"<b>Movies in year '{html.escape(message.text)}':</b> \n\n{result}",
            parse_mode="HTML",
            reply_markup=main_kb,
            disable_web_page_preview=(len(matched_films) > 1),
        )

    await state.clear()


@router.message(InspectFilmState.waiting_for_genre)
async def film_by_genre(message: types.Message, state: FSMContext):
    films = await load_films(message.from_user.id)

    if not films:
        await message.answer("No films added.")
        state.clear()
        return

    genre = message.text.strip().lower()

    matched_films = [
        (name, info) for name, info in films.items() if genre in info["genre"].lower()
    ]

    if not matched_films:
        await message.answer("No movies found in this genre.", reply_markup=main_kb)
    else:
        result = "\n\n".join(
            [format_film_info(name, info) for name, info in matched_films]
        )
        await message.answer(
            f"<b>Movies in genre '{html.escape(message.text)}':</b>\n\n{result}",
            parse_mode="HTML",
            reply_markup=main_kb,
            disable_web_page_preview=(len(matched_films) > 1),
        )

    await state.clear()


@router.message(InspectFilmState.waiting_for_description)
async def film_by_description(message: types.Message, state: FSMContext):
    user_input = message.text.strip().lower()
    films = await load_films(message.from_user.id)

    if not films:
        await message.answer("No films added.")
        await state.clear()
        return

    matched = []
    # Порівнюємо опис користувача з описами фільмів у базі за допомогою SequenceMatcher
    for name, info in films.items():
        description = str(info.get("description", "")).lower()
        similarity = difflib.SequenceMatcher(None, user_input, description).ratio()

        # Якщо схожість більше 20% — додаємо до результату
        if similarity >= 0.2:
            matched.append((similarity, name, info))

    if not matched:
        await message.answer("No movies with this description.", reply_markup=main_kb)
    else:
        matched.sort(reverse=True)
        top_matches = matched[:5]

        result = "\n\n".join(
            [
                f"{format_film_info(name, info)}\n📊Similarity: {round(similarity * 100)}%"
                for similarity, name, info in top_matches
            ]
        )

        await message.answer(
            f"<b>Most similar descriptions:</b>\n\n{result}",
            parse_mode="HTML",
            reply_markup=main_kb,
            disable_web_page_preview=(len(matched) > 1),
        )

    await state.clear()


@router.message(InspectFilmState.waiting_for_answer)
async def user_answer_handler(message: types.Message, state: FSMContext):
    answer = message.text.strip().lower()
    if answer in ("y", "yes"):
        data = await state.get_data()
        film_data = data.get("last_tmdb_film")

        if film_data:
            saved = await save_film(message.from_user.id, film_data)
            if saved:
                await message.answer(
                    "Movie successfully added to your collection.", reply_markup=main_kb
                )
            else:
                await message.answer(
                    "Could not save the movie. It may already exist.",
                    reply_markup=main_kb,
                )
        else:
            await message.answer(
                "No movie data available to save.", reply_markup=main_kb
            )
    elif answer in ("n", "no"):
        await message.answer("Not added to the collection.", reply_markup=main_kb)

    else:
        await message.answer("Please use menu.")
        return

    await state.clear()


@router.message(InspectFilmState.waiting_for_tag)
async def get_film_by_tag(message: types.Message, state: FSMContext):
    user_input = message.text.strip().lower()
    films = await load_films(message.from_user.id)

    if not films:
        await message.answer("No films added.")
        await state.clear()
        return

    matched_films = [
        (name, info)
        for name, info in films.items()
        if user_input == info["tag"].lower()
    ]

    if not matched_films:
        await message.answer("No movies found with this tag", reply_markup=main_kb)
    else:
        result = "\n\n".join(
            [format_film_info(name, info) for name, info in matched_films]
        )
        await message.answer(
            f"<b>Movies with tag '{html.escape(message.text)}':</b>\n\n{result}",
            parse_mode="HTML",
            reply_markup=main_kb,
            disable_web_page_preview=(len(matched_films) > 1),
        )
    await state.clear()


@router.message(InspectFilmState.waiting_for_random)
async def random_film_handler(message: types.Message, state: FSMContext):
    answer = message.text.strip().lower()
    if not answer or answer not in ("from own collection", "via tmdb"):
        await message.answer("Use keyboard buttons")
        return

    if answer == "from own collection":
        films = await load_films(message.from_user.id)

        if not films:
            await message.answer("No movies found.", reply_markup=main_kb)
            return

        name, info = random.choice(list(films.items()))
        text = format_film_info(name, info)

        await message.answer(
            f"<b>Random film:</b>\n\n{text}", parse_mode="HTML", reply_markup=main_kb
        )
    elif answer == "via tmdb":
        total_pages = 500
        random_page = random.randint(1, total_pages)

        url = "https://api.themoviedb.org/3/discover/movie"
        params = {
            "api_key": API_KEY,
            "sort_by": "popularity.desc",
            "page": random_page,
        }

        async with ClientSession() as session:
            async with session.get(url, params=params) as response:
                data = await response.json()
                results = data.get("results", [])

                if not results:
                    await message.answer("Could not fetch films from TMDb.")
                    return

                film = random.choice(results)
                title = film.get("title") or film.get("name")
                overview = film.get("overview") or "No description"
                rating = film.get("vote_average", 0)
                year = (film.get("release_date") or "Unknown")[:4]
                poster_url = (
                    f"https://image.tmdb.org/t/p/w500{film['poster_path']}"
                    if film.get("poster_path")
                    else ""
                )
                trailer_url = ""  # Можно добавить запрос позже

                # Структура для сохранения
                film_data = {
                    "year": year,
                    "genre": "Unknown",  # жанры можно подтянуть, если хочешь
                    "rating": rating,
                    "description": overview,
                    "poster_url": poster_url,
                    "trailer": trailer_url,
                    "tag": "Not set",
                }

                text = (
                    f"<b>Random TMDb film:</b>\n\n{format_film_info(title, film_data)}"
                )

                await message.answer(
                    f"{text}",
                    parse_mode="HTML",
                    disable_web_page_preview=False,
                    reply_markup=main_kb,
                )
    await state.clear()
