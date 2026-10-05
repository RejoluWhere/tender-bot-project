import asyncio
import os
import psycopg2
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart

BOT_TOKEN = os.environ.get("BOT_TOKEN") 
NEON_DB_URL = os.environ.get("NEON_DB_URL") 

dp = Dispatcher()
bot = Bot(BOT_TOKEN)


def run_sql(sql_query, params=(), fetch=False):
    """Универсальная функция для выполнения SQL-запросов."""
    try:
        with psycopg2.connect(NEON_DB_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(sql_query, params)
                conn.commit() 
                if fetch:
                    return cur.fetchall() 
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Ошибка SQL: {error}")
        return None 
        
def add_user_to_db(user_id, username):
    sql = "INSERT INTO users (user_id, username) VALUES (%s, %s) ON CONFLICT (user_id) DO NOTHING"
    run_sql(sql, (user_id, username))

def add_subscription_to_db(user_id, query_text):
    sql = "INSERT INTO subscriptions (user_id, query_text) VALUES (%s, %s)"
    run_sql(sql, (user_id, query_text))
    return True # (Для упрощения считаем, что всегда успешно)

@dp.message(CommandStart())
async def handle_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or f"User_{user_id}"
    
    add_user_to_db(user_id, username)
    
    await message.answer(
        f"Привет, {username}!\n"
        "Я бот для поиска тендеров по *смыслу*.\n\n"
        "Просто напиши мне, что ты ищешь (например: 'строительство детских площадок'), "
        "и я создам для тебя подписку.",
        parse_mode="Markdown"
    )

@dp.message() 
async def handle_new_subscription(message: types.Message):
    if not message.text or message.text.startswith('/'):
        return 

    user_id = message.from_user.id
    query_text = message.text

    if add_subscription_to_db(user_id, query_text):
        await message.answer(
            f"✅ Подписка создана!\n\n"
            f"Запрос: '{query_text}'\n\n"
            "Раз в день я буду проверять *новые* тендеры и присылать тебе совпадения."
        )
    else:
        await message.answer("❌ Произошла ошибка при создании подписки, попробуйте позже.")

async def main():
    if not BOT_TOKEN or not NEON_DB_URL:
        print("КРИТИЧЕСКАЯ ОШИБКА: Отсутствуют BOT_TOKEN или NEON_DB_URL в переменных окружения.")
        return

    print("Бот запускается (Секретарь на Render.com)...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
