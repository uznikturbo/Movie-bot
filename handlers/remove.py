import html

import aiosqlite
from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove

from config import DB_PATH
from db import load_films
from keyboards import main_kb
from states import RemoveFilmState

router = Router(name=__name__)


@router.message(lambda m: m.text == "Remove film")
async def remove_film_start(message: types.Message, state: FSMContext):
    await message.answer(
        "Enter a film name to remove:", reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(RemoveFilmState.waiting_for_name)


@router.message(RemoveFilmState.waiting_for_name)
async def remove_film(message: types.Message, state: FSMContext):
    film_name = message.text.strip()
    user_id = message.from_user.id
    films = await load_films(user_id)
    if film_name not in films:
        await message.answer(
            "Movie not found in database. Cancelling.", reply_markup=main_kb
        )
        await state.clear()
        return
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM films WHERE user_id = ? AND name = ?", (user_id, film_name)
        )
        await db.commit()
    await message.answer(
        f"Movie <b>{html.escape(film_name)}</b> deleted.",
        parse_mode="HTML",
        reply_markup=main_kb,
    )
    await state.clear()
