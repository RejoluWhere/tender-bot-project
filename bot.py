import asyncio
import os
import psycopg2 # Библиотека для работы с Neon (Postgres)
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart

# --- Настройки (вставь свои данные) ---
# Эти переменные Render.com возьмет из Environment
BOT_TOKEN = os.environ.get("BOT_TOKEN") 
NEON_DB_URL = os.environ.get("NEON_DB_URL") 

# --- Инициализация ---
dp = Dispatcher()
bot = Bot(BOT_TOKEN)

# --- Функции для работы с Базой (Neon) ---
# ИСПРАВЛЕНО: Используем 'with' для безопасного управления соединением

def run_sql(sql_query, params=(), fetch=False):
    """Универсальная функция для выполнения SQL-запросов."""
    try:
        # 'with' гарантирует, что conn и cur будут закрыты
        with psycopg2.connect(NEON_DB_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(sql_query, params)
                conn.commit() # Сохраняем изменения
                if fetch:
                    return cur.fetchall() # Возвращаем результат (для SELECT)
    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Ошибка SQL: {error}")
        return None # В случае ошибки

def add_user_to_db(user_id, username):
    """Добавляем нового пользователя (или ничего не делаем, если он есть)"""
    sql = "INSERT INTO users (user_id, username) VALUES (%s, %s) ON CONFLICT (user_id) DO NOTHING"
    run_sql(sql, (user_id, username))

def add_subscription_to_db(user_id, query_text):
    """Добавляем новую подписку для пользователя"""
    sql = "INSERT INTO subscriptions (user_id, query_text) VALUES (%s, %s)"
    run_sql(sql, (user_id, query_text))
    return True # (Для упрощения считаем, что всегда успешно)

# --- Обработчики Команд Бота ---

@dp.message(CommandStart())
async def handle_start(message: types.Message):
    """Обработчик команды /start"""
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

@dp.message() # Обработчик ЛЮБОГО текста
async def handle_new_subscription(message: types.Message):
    """Обработчик любого текстового сообщения (создание подписки)"""
    if not message.text or message.text.startswith('/'):
        return # Игнорируем команды или пустые сообщения

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

# --- Запуск Бота ---
async def main():
    # Проверяем, что токен бота есть
    if not BOT_TOKEN or not NEON_DB_URL:
        print("КРИТИЧЕСКАЯ ОШИБКА: Отсутствуют BOT_TOKEN или NEON_DB_URL в переменных окружения.")
        return

    print("Бот запускается (Секретарь на Render.com)...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())