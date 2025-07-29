from aiogram.fsm.state import State, StatesGroup


class AddFilmsState(StatesGroup):
    waiting_for_answer = State()
    waiting_for_name = State()
    waiting_for_tmdb_name = State()
    waiting_for_rating = State()
    waiting_for_year = State()
    waiting_for_genre = State()
    waiting_for_description = State()
    waiting_for_poster = State()
    waiting_for_review = State()
    waiting_for_tag = State()
    waiting_for_tmdb_tag = State()
    waiting_for_confirm = State()
    waiting_for_trailer = State()


class InspectFilmState(StatesGroup):
    waiting_for_name = State()
    waiting_for_rating = State()
    waiting_for_year = State()
    waiting_for_genre = State()
    waiting_for_description = State()
    waiting_for_tmdb_name = State()
    waiting_for_tag = State()
    waiting_for_answer = State()


class EditFilmState(StatesGroup):
    waiting_for_film_name_edit = State()
    waiting_for_field_choice = State()
    waiting_for_new_value = State()


class RemoveFilmState(StatesGroup):
    waiting_for_name = State()
