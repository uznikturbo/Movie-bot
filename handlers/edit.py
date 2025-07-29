from datetime import datetime

import aiosqlite
from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove

from config import DB_PATH
from db import load_films, save_film
from keyboards import edit_kb, main_kb
from states import EditFilmState
from utils import validate_text_field

router = Router(name=__name__)


@router.message(lambda m: m.text == "Edit film")
async def edit_film_start(message: types.Message, state: FSMContext):
    await message.answer(
        "Enter a film name to edit:", reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(EditFilmState.waiting_for_film_name_edit)


@router.message(EditFilmState.waiting_for_film_name_edit)
async def edit_film_name(message: types.Message, state: FSMContext):
    films = await load_films(message.from_user.id)
    name = message.text.strip()
    if name not in films:
        await message.answer("Movie not found.", reply_markup=main_kb)
        await state.clear()
        return
    await state.update_data(film_name=name)
    await message.answer(
        f"Editing movie: <b>{name}</b>\nSelect field to edit:",
        reply_markup=edit_kb,
        parse_mode="HTML",
    )
    await state.set_state(EditFilmState.waiting_for_field_choice)


@router.message(EditFilmState.waiting_for_field_choice)
async def edit_field_choice(message: types.Message, state: FSMContext):
    field = message.text.lower()
    allowed_field = {
        "name",
        "rating",
        "year",
        "genre",
        "description",
        "review",
        "poster",
        "tag",
        "trailer",
    }
    # Якщо користувач натиснув "Back to main menu" — повертаємо в головне меню
    if field == "back to main menu":
        await message.answer("Select a menu item:", reply_markup=main_kb)
        await state.clear()
        return
    # Перевірка, чи поле для редагування дозволене
    if field not in allowed_field:
        await message.answer("Invalid field. Please select from the keyboard")
        return
    await state.update_data(field=field)
    # Для постера і трейлера просимо ввести посилання, для інших — просто значення
    if field == "poster":
        await message.answer(f"Enter a direct URL to the new poster:")
    elif field == "trailer":
        await message.answer(f"Enter a direct URL to the new trailer:")
    else:
        await message.answer(f"Enter a new value for {field.capitalize()}:")
    await state.set_state(EditFilmState.waiting_for_new_value)


@router.message(EditFilmState.waiting_for_new_value)
async def save_new_field_value(message: types.Message, state: FSMContext):
    data = await state.get_data()
    film_name = data.get("film_name")
    field = data.get("field")
    user_id = message.from_user.id
    new_value = message.text.strip()
    films = await load_films(user_id)
    if film_name not in films:
        await message.answer(
            "Movie not found in database. Cancelling edit.", reply_markup=main_kb
        )
        await state.clear()
        return
    if field == "name":
        valid, result = validate_text_field(new_value, 100)
        if not valid:
            await message.answer(f"Invalid name: {result}. Try again.")
            return

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "DELETE FROM films WHERE user_id = ? AND name = ?", (user_id, film_name)
            )
            await db.commit()

        film_data = films.pop(film_name)
        film_data["name"] = result
        films[result] = film_data
        saved = await save_film(user_id, film_data)

    elif field == "rating":
        try:
            rating = float(new_value.replace(",", "."))
            if not (1 <= rating <= 10):
                await message.answer("Rating must be from 1 to 10. Try again:")
                return
        except ValueError:
            await message.answer(
                "Please enter a valid number between 1 and 10. Try again:"
            )
            return
        film_data = films[film_name]
        film_data["name"] = film_name
        film_data["rating"] = rating
        saved = await save_film(user_id, film_data)
    elif field == "year":
        try:
            year = int(new_value)
            current_year = datetime.now().year
            if not (1888 <= year <= current_year + 5):
                await message.answer(
                    f"Year must be between 1888 and {current_year + 5}. Try again:"
                )
                return
        except ValueError:
            await message.answer("Please enter a valid numerical year. Try again:")
            return
        film_data = films[film_name]
        film_data["name"] = film_name
        film_data["year"] = year
        saved = await save_film(user_id, film_data)
    elif field == "genre":
        valid, result = validate_text_field(new_value, 50)
        if not valid:
            await message.answer(f"Invalid genre: {result} Try again:")
            return
        film_data = films[film_name]
        film_data["name"] = film_name
        film_data["genre"] = result
        saved = await save_film(user_id, film_data)
    elif field == "description":
        valid, result = validate_text_field(new_value, 500)
        if not valid:
            await message.answer(f"Invalid description: {result} Try again:")
            return
        film_data = films[film_name]
        film_data["name"] = film_name
        film_data["description"] = result
        saved = await save_film(user_id, film_data)
    elif field == "poster":
        if not (new_value.startswith("http://") or new_value.startswith("https://")):
            await message.answer("Invalid URL. Please send a valid link to an image.")
            return
        film_data = films[film_name]
        film_data["name"] = film_name
        film_data["poster_url"] = new_value
        saved = await save_film(user_id, film_data)
    elif field == "review":
        if not (new_value == "like" or new_value == "dislike"):
            await message.answer(
                "Invalid review. Please write valid review (like or dislike)."
            )
            return
        film_data = films[film_name]
        film_data["name"] = film_name
        film_data["review"] = new_value
        saved = await save_film(user_id, film_data)
    elif field == "tag":
        if not new_value in ("viewed", "not viewed"):
            await message.answer(
                "Invalid tag. Please write valid tag (viewed or not viewed)."
            )
            return
        film_data = films[film_name]
        film_data["name"] = film_name
        film_data["tag"] = new_value
        saved = await save_film(user_id, film_data)
    elif field == "trailer":
        if not (new_value.startswith("http://") or new_value.startswith("https://")):
            await message.answer("Invalid URL. Please send a valid link to a trailer.")
            return
        film_data = films[film_name]
        film_data["name"] = film_name
        film_data["trailer"] = new_value
        saved = await save_film(user_id, film_data)

    else:
        await message.answer("Unexpected error. Cancelling.", reply_markup=main_kb)
        await state.clear()
        return
    if saved:
        await message.answer(
            f"Field <b>{field.capitalize()}</b> updated successfully",
            parse_mode="HTML",
        )
    else:
        await message.answer("Error saving changes.", reply_markup=main_kb)
        await state.clear()
        return
    await message.answer(
        "Select another field to edit or 'Back to main menu'", reply_markup=edit_kb
    )
    await state.set_state(EditFilmState.waiting_for_field_choice)
