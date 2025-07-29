from aiogram import Router, types
from aiogram.filters import Command

from keyboards import main_kb

router = Router(name=__name__)


@router.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "Welcome! type '/help' to see commands\nSelect a menu item:",
        reply_markup=main_kb,
    )


@router.message(Command("help"))
async def help_handler(message: types.Message):
    await message.answer(
        "Allowed commands:\n\n/start - Start bot\n/help - See all commands\n/cancel - Cancelling operation"
    )


@router.message(lambda m: m.text == "Back to main menu")
async def back_menu(message: types.Message):
    await message.answer("Select a menu item:", reply_markup=main_kb)


@router.message()
async def unknown_message(message: types.Message):
    await message.answer("Unknown command. Use menu buttons.", reply_markup=main_kb)
