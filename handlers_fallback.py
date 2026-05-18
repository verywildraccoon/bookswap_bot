from aiogram import F, Router
from aiogram.types import Message

router = Router()


@router.message(F.text.startswith("/"), F.chat.type == "private")
async def handle_unknown_command(message: Message):
    await message.answer("Неизвестная команда. Введите /help, чтобы увидеть список доступных команд.")