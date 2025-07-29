from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Add film")],
        [KeyboardButton(text="Inspect films")],
        [KeyboardButton(text="Edit film")],
        [KeyboardButton(text="Remove film")],
    ],
    resize_keyboard=True,
    one_time_keyboard=False,
)

inspect_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Inspect all films"),
            KeyboardButton(text="Inspect by name"),
        ],
        [
            KeyboardButton(text="Inspect by rating"),
            KeyboardButton(text="Inspect by year"),
            KeyboardButton(text="Inspect by tag"),
        ],
        [
            KeyboardButton(text="Inspect by genre"),
            KeyboardButton(text="Inspect by description"),
            KeyboardButton(text="Inspect random film"),
        ],
        [KeyboardButton(text="Back to main menu")],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)


edit_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Name"), KeyboardButton(text="Rating")],
        [KeyboardButton(text="Year"), KeyboardButton(text="Genre")],
        [
            KeyboardButton(text="Description"),
            KeyboardButton(text="Poster"),
            KeyboardButton(text="Review"),
        ],
        [KeyboardButton(text="Back to main menu")],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)

add_or_no_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="yes")], [KeyboardButton(text="no")]],
    resize_keyboard=True,
)

viewed_or_not_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Viewed")], [KeyboardButton(text="Not viewed")]],
    resize_keyboard=True,
)


answer_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Enter data manually")],
        [KeyboardButton(text="Search via TMDb")],
    ],
    resize_keyboard=True,
)
