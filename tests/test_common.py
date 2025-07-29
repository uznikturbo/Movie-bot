import pytest

from handlers.common import back_menu, help_handler, start_handler, unknown_message
from keyboards import main_kb


class DummyMessage:
    def __init__(self, text):
        self.text = text
        self.answer_called = False
        self.answer_args = None
        self.answer_kwargs = None

    async def answer(self, *args, **kwargs):
        self.answer_called = True
        self.answer_args = args
        self.answer_kwargs = kwargs


@pytest.mark.asyncio
async def test_start_handler():
    message = DummyMessage("/start")
    await start_handler(message)
    assert message.answer_called
    assert "Welcome!" in message.answer_args[0]
    assert message.answer_kwargs["reply_markup"] == main_kb


@pytest.mark.asyncio
async def test_help_handler():
    message = DummyMessage("/help")
    await help_handler(message)
    assert message.answer_called
    assert "Allowed commands" in message.answer_args[0]


@pytest.mark.asyncio
async def test_back_menu():
    message = DummyMessage("Back to main menu")
    await back_menu(message)
    assert message.answer_called
    assert "Select a menu item:" in message.answer_args[0]
    assert message.answer_kwargs["reply_markup"] == main_kb


@pytest.mark.asyncio
async def test_unknown_message():
    message = DummyMessage("abracadabra")
    await unknown_message(message)
    assert message.answer_called
    assert "Unknown command" in message.answer_args[0]
    assert message.answer_kwargs["reply_markup"]
