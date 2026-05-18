import asyncio
from aiogram import Dispatcher, F

from config import bot
from handlers_admin import router as admin_router
from handlers_listing import router as listing_router
from handlers_fallback import router as fallback_router

dp = Dispatcher()
dp.include_router(admin_router)
dp.include_router(listing_router)
dp.include_router(fallback_router)

async def main():
    await dp.start_polling(bot)

asyncio.run(main())