import html
from datetime import datetime

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException

from db import load_films, save_film
from keyboards import add_or_no_kb, answer_kb, main_kb, viewed_or_not_kb
from states import AddFilmsState
from utils import search_tmdb_film, validate_text_field

router = Router(name=__name__)


@router.message(lambda m: m.text == "Add film")
async def add_film(message: types.Message, state: FSMContext):
    await message.answer("Select a method to add a movie:", reply_markup=answer_kb)
    await state.set_state(AddFilmsState.waiting_for_answer)


@router.message(Command("cancel"))
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()

    if current_state is None:
        await message.answer(
            "You are not in the middle of any action", reply_markup=main_kb
        )
    else:
        await state.clear()
        await message.answer(
            "Operation cancelled. Returning to main menu", reply_markup=main_kb
        )


@router.message(AddFilmsState.waiting_for_answer)
async def wait_for_answer(message: types.Message, state: FSMContext):
    if message.text == "Enter data manually":
        await message.answer("Enter a movie title:", reply_markup=ReplyKeyboardRemove())
        await state.set_state(AddFilmsState.waiting_for_name)
    elif message.text == "Search via TMDb":
        await message.answer("Enter a movie title:", reply_markup=ReplyKeyboardRemove())
        await state.set_state(AddFilmsState.waiting_for_tmdb_name)


@router.message(AddFilmsState.waiting_for_name)
async def get_film_name(message: types.Message, state: FSMContext):
    # Перевірка валідності введеного тексту (назва фільму)
    valid, result = validate_text_field(message.text, 100)
    if not valid:
        await message.answer(f"Invalid movie title: {result} Try again:")
        return

    # Завантажуємо всі фільми користувача для перевірки на дублікати
    films = await load_films(message.from_user.id)
    if result in films:
        await message.answer(
            "Film with this name already in database!", reply_markup=main_kb
        )
        return

    # Зберігаємо назву фільму у стані FSM
    await state.update_data(film_name=result)
    await message.answer("Enter movie rating (1 to 10):")
    await state.set_state(AddFilmsState.waiting_for_rating)


@router.message(AddFilmsState.waiting_for_rating)
async def get_film_rating(message: types.Message, state: FSMContext):
    try:
        rating = float(message.text.replace(",", "."))
        if 1 <= rating <= 10:
            await state.update_data(rating=rating)
            await message.answer("Enter the year the movie was released:")
            await state.set_state(AddFilmsState.waiting_for_year)
        else:
            await message.answer("Enter a number from 1 to 10")
    except ValueError:
        await message.answer("Please enter a valid number between 1 and 10")


@router.message(AddFilmsState.waiting_for_year)
async def get_film_year(message: types.Message, state: FSMContext):

    try:
        year = int(message.text)
        current_year = datetime.now().year
        if 1888 <= year <= current_year + 5:
            await state.update_data(year=year)
            await message.answer("Enter the movie genre:")
            await state.set_state(AddFilmsState.waiting_for_genre)
        else:
            await message.answer(f"Please enter a valid year (1888-{current_year + 5})")
    except ValueError:
        await message.answer("Please enter a valid numerical year.")


@router.message(AddFilmsState.waiting_for_genre)
async def get_film_genre(message: types.Message, state: FSMContext):
    valid, result = validate_text_field(message.text, 50)
    if not valid:
        await message.answer(f"Invalid genre: {result} Try again:")
        return
    await state.update_data(genre=result)
    await message.answer("Enter a description of the movie:")
    await state.set_state(AddFilmsState.waiting_for_description)


@router.message(AddFilmsState.waiting_for_description)
async def get_film_description(message: types.Message, state: FSMContext):
    valid, result = validate_text_field(message.text, 500)
    if not valid:
        await message.answer(f"Invalid description: {result} Try again:")
        return
    await state.update_data(description=result)
    await message.answer(
        "Write tag for film (viewed, not viewed):", reply_markup=viewed_or_not_kb
    )
    await state.set_state(AddFilmsState.waiting_for_tag)


@router.message(AddFilmsState.waiting_for_tag)
async def get_film_tag(message: types.Message, state: FSMContext):
    valid, result = validate_text_field(message.text, 10)
    result = result.lower()

    if not result:
        await message.answer("Write viewed or not viewed:")
        return

    if not valid or result not in ("viewed", "not viewed"):
        await message.answer(f"Invalid tag: {result} Try again:")
        return

    await state.update_data(tag=result)
    await message.answer(
        "Optional: write you review(like or dislike) (or type 'skip'):",
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(AddFilmsState.waiting_for_review)


@router.message(AddFilmsState.waiting_for_review)
async def get_film_review(message: types.Message, state: FSMContext):
    valid, result = validate_text_field(message.text, 8)

    if result == "skip":
        result = None
    else:
        if not valid or result not in ("like", "dislike"):
            await message.answer(f"Invalid review: {result} Try again:")
            return

    await state.update_data(review=result)
    await message.answer("Optional: send a link to the movie trailer (or type 'skip'):")
    await state.set_state(AddFilmsState.waiting_for_trailer)


@router.message(AddFilmsState.waiting_for_trailer)
async def get_film_trailer(message: types.Message, state: FSMContext):
    trailer = message.text.strip()

    if trailer.lower() == "skip" or not (
        trailer.startswith("http://") or trailer.startswith("https://")
    ):
        trailer = None
    await state.update_data(trailer=trailer)
    await message.answer("Optional: send a link to the movie poster (or type 'skip'):")
    await state.set_state(AddFilmsState.waiting_for_poster)


@router.message(AddFilmsState.waiting_for_poster)
async def get_film_poster(message: types.Message, state: FSMContext):
    poster_url = message.text.strip()

    if poster_url.lower() == "skip" or not (
        poster_url.startswith("http://") or poster_url.startswith("https://")
    ):
        poster_url = None

    await state.update_data(poster_url=poster_url)
    data = await state.get_data()

    film_data = {
        "name": data["film_name"],
        "rating": data["rating"],
        "year": data["year"],
        "genre": data["genre"],
        "description": data["description"],
        "tag": data.get("tag"),
        "review": data.get("review"),
        "poster_url": data.get("poster_url"),
        "trailer": data.get("trailer"),
    }

    saved = await save_film(message.from_user.id, film_data)
    if saved:
        text = f"Movie '<b>{html.escape(film_data['name'])}'</b> saved successfully!"
        if film_data["poster_url"]:
            text += f"\n <a href=\"{film_data['poster_url']}\">Poster link</a>"
        if film_data["trailer"]:
            text += f"\n <a href=\"{film_data['trailer']}\">Trailer link</a>"
        await message.answer(
            text,
            parse_mode="HTML",
            reply_markup=main_kb,
            disable_web_page_preview=not bool(film_data["poster_url"]),
        )
    else:
        await message.answer("Error saving movie", reply_markup=main_kb)

    await state.clear()


@router.message(AddFilmsState.waiting_for_tmdb_name)
async def film_via_tmdb(message: types.Message, state: FSMContext):
    name = message.text.strip()
    try:
        user_lang = detect(name)
    except LangDetectException:
        user_lang = "en"

    title, film_data, result = await search_tmdb_film(name, user_lang)
    if result:
        print(film_data)
        await message.answer(
            f"This film? (y/n)\n\n{result}",
            parse_mode="HTML",
            reply_markup=add_or_no_kb,
        )
        await state.update_data(
            last_tmdb_film={**film_data, "name": title, "tag": None}
        )
        await state.set_state(AddFilmsState.waiting_for_confirm)
    else:
        await message.answer("Film not found. Try again.", reply_markup=main_kb)
        await state.clear()


@router.message(AddFilmsState.waiting_for_confirm)
async def add_via_tmdb(message: types.Message, state: FSMContext):
    answer = message.text.strip().lower()
    if answer in ("y", "yes"):

        await message.answer(
            "Write tag for film (viewed / not viewed):", reply_markup=viewed_or_not_kb
        )
        await state.set_state(AddFilmsState.waiting_for_tmdb_tag)
    elif answer in ("n", "no"):
        await message.answer("Not added to the collection.", reply_markup=main_kb)
        await state.clear()
    else:
        await message.answer("Please reply with y/n")


@router.message(AddFilmsState.waiting_for_tmdb_tag)
async def tag_via_tmdb(message: types.Message, state: FSMContext):
    valid, result = validate_text_field(message.text, 10)
    result = result.lower()
    if not valid or result not in ("viewed", "not viewed"):
        await message.answer(f"Invalid tag: {result.capitalize()} Try again:")
        return

    data = await state.get_data()
    film_data = data.get("last_tmdb_film")
    if not film_data:
        await message.answer("No film data found.", reply_markup=main_kb)
        await state.clear()
        return

    films = await load_films(message.from_user.id)
    if film_data["name"] in films:
        await message.answer(
            "A film with this name already exists in your collection. Not added.",
            reply_markup=main_kb,
        )
        await state.clear()
        return

    film_data["tag"] = result
    await state.update_data(last_tmdb_film=film_data)
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

    await state.clear()
