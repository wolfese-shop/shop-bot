import asyncio
import os
import sqlite3
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

# =========================================================
# НАСТРОЙКИ
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("Не найден BOT_TOKEN. Добавь его в переменные окружения.")

DB_NAME = "money_bot.db"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# =========================================================
# БАЗА ДАННЫХ
# =========================================================

db = sqlite3.connect(DB_NAME)
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    balance REAL DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    amount REAL,
    type TEXT,
    comment TEXT,
    created_at TEXT
)
""")

db.commit()


# =========================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =========================================================

def get_user(user_id: int):
    cursor.execute(
        "SELECT user_id, balance FROM users WHERE user_id = ?",
        (user_id,)
    )

    user = cursor.fetchone()

    if not user:
        cursor.execute(
            "INSERT INTO users (user_id, balance) VALUES (?, ?)",
            (user_id, 0)
        )
        db.commit()
        return (user_id, 0)

    return user


def get_balance(user_id: int) -> float:
    user = get_user(user_id)
    return float(user[1])


def change_balance(
    user_id: int,
    amount: float,
    transaction_type: str,
    comment: str
):
    get_user(user_id)

    balance = get_balance(user_id)

    if transaction_type == "expense":
        new_balance = balance - amount
    else:
        new_balance = balance + amount

    cursor.execute(
        "UPDATE users SET balance = ? WHERE user_id = ?",
        (new_balance, user_id)
    )

    cursor.execute(
        """
        INSERT INTO transactions
        (user_id, amount, type, comment, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            user_id,
            amount,
            transaction_type,
            comment,
            datetime.now().strftime("%d.%m.%Y %H:%M")
        )
    )

    db.commit()

    return new_balance


def main_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💰 Баланс",
                    callback_data="balance"
                ),
                InlineKeyboardButton(
                    text="📊 Статистика",
                    callback_data="stats"
                )
            ],
            [
                InlineKeyboardButton(
                    text="➕ Доход",
                    callback_data="income"
                ),
                InlineKeyboardButton(
                    text="➖ Расход",
                    callback_data="expense"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📜 История",
                    callback_data="history"
                )
            ]
        ]
    )


def back_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="◀️ Назад",
                    callback_data="menu"
                )
            ]
        ]
    )


# =========================================================
# СТАРТ
# =========================================================

@dp.message(CommandStart())
async def start(message: Message):
    user_id = message.from_user.id
    get_user(user_id)

    name = message.from_user.first_name or "друг"

    text = (
        f"👋 Привет, {name}!\n\n"
        "💳 Личный финансовый помощник\n\n"
        "Здесь можно:\n"
        "• учитывать доходы\n"
        "• записывать расходы\n"
        "• смотреть баланс\n"
        "• смотреть статистику\n"
        "• просматривать историю операций\n\n"
        "Выбирай действие ниже 👇"
    )

    await message.answer(
        text,
        reply_markup=main_keyboard()
    )


# =========================================================
# ГЛАВНОЕ МЕНЮ
# =========================================================

@dp.callback_query(F.data == "menu")
async def menu(callback: CallbackQuery):
    await callback.answer()

    await callback.message.edit_text(
        "🏠 Главное меню\n\nВыбери нужное действие:",
        reply_markup=main_keyboard()
    )


# =========================================================
# БАЛАНС
# =========================================================

@dp.callback_query(F.data == "balance")
async def balance(callback: CallbackQuery):
    await callback.answer()

    user_id = callback.from_user.id
    current_balance = get_balance(user_id)

    if current_balance > 0:
        status = "🟢"
    elif current_balance < 0:
        status = "🔴"
    else:
        status = "⚪"

    text = (
        "💰 Текущий баланс\n\n"
        f"{status} {current_balance:,.2f} ₽\n\n"
        "Баланс рассчитан по всем сохранённым операциям."
    )

    await callback.message.edit_text(
        text,
        reply_markup=back_keyboard()
    )


# =========================================================
# СТАТИСТИКА
# =========================================================

@dp.callback_query(F.data == "stats")
async def statistics(callback: CallbackQuery):
    await callback.answer()

    user_id = callback.from_user.id

    cursor.execute(
        """
        SELECT
            COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 0),
            COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0)
        FROM transactions
        WHERE user_id = ?
        """,
        (user_id,)
    )

    income, expense = cursor.fetchone()

    balance_value = income - expense

    text = (
        "📊 Финансовая статистика\n\n"
        f"🟢 Доходы: {income:,.2f} ₽\n"
        f"🔴 Расходы: {expense:,.2f} ₽\n"
        f"💰 Баланс: {balance_value:,.2f} ₽\n\n"
        f"📈 Оборот: {income + expense:,.2f} ₽"
    )

    await callback.message.edit_text(
        text,
        reply_markup=back_keyboard()
    )


# =========================================================
# ДОБАВЛЕНИЕ ДОХОДА
# =========================================================

@dp.callback_query(F.data == "income")
async def income_start(callback: CallbackQuery):
    await callback.answer()

    await callback.message.edit_text(
        "➕ Добавление дохода\n\n"
        "Отправь сообщение в формате:\n\n"
        "50000 зарплата\n\n"
        "Сначала укажи сумму, затем комментарий.",
        reply_markup=back_keyboard()
    )


# =========================================================
# ДОБАВЛЕНИЕ РАСХОДА
# =========================================================

@dp.callback_query(F.data == "expense")
async def expense_start(callback: CallbackQuery):
    await callback.answer()

    await callback.message.edit_text(
        "➖ Добавление расхода\n\n"
        "Отправь сообщение в формате:\n\n"
        "1500 продукты\n\n"
        "Сначала укажи сумму, затем комментарий.",
        reply_markup=back_keyboard()
    )


# =========================================================
# ОБРАБОТКА СУММ
# =========================================================

@dp.message(F.text)
async def process_transaction(message: Message):
    text = message.text.strip()

    parts = text.split(maxsplit=1)

    if not parts:
        return

    try:
        amount = float(
            parts[0]
            .replace(",", ".")
            .replace("₽", "")
            .replace("р", "")
            .strip()
        )
    except ValueError:
        return

    if amount <= 0:
        await message.answer(
            "❌ Сумма должна быть больше нуля.",
            reply_markup=main_keyboard()
        )
        return

    comment = parts[1] if len(parts) > 1 else "Без комментария"

    # Если перед этим пользователь нажал кнопку,
    # Telegram не хранит состояние автоматически.
    # Поэтому используем простое временное состояние.
    user_id = message.from_user.id

    state = user_states.get(user_id)

    if state == "income":
        new_balance = change_balance(
            user_id,
            amount,
            "income",
            comment
        )

        await message.answer(
            "✅ Доход добавлен\n\n"
            f"💵 Сумма: +{amount:,.2f} ₽\n"
            f"📝 Комментарий: {comment}\n\n"
            f"💰 Новый баланс: {new_balance:,.2f} ₽",
            reply_markup=main_keyboard()
        )

        user_states.pop(user_id, None)

    elif state == "expense":
        new_balance = change_balance(
            user_id,
            amount,
            "expense",
            comment
        )

        await message.answer(
            "✅ Расход добавлен\n\n"
            f"💸 Сумма: -{amount:,.2f} ₽\n"
            f"📝 Комментарий: {comment}\n\n"
            f"💰 Новый баланс: {new_balance:,.2f} ₽",
            reply_markup=main_keyboard()
        )

        user_states.pop(user_id, None)


# =========================================================
# СОСТОЯНИЕ ПОЛЬЗОВАТЕЛЕЙ
# =========================================================

user_states = {}


# =========================================================
# ПЕРЕОПРЕДЕЛЯЕМ КНОПКИ ДОХОДА И РАСХОДА
# =========================================================

@dp.callback_query(F.data == "income")
async def income_handler(callback: CallbackQuery):
    await callback.answer()

    user_states[callback.from_user.id] = "income"

    await callback.message.edit_text(
        "➕ Новый доход\n\n"
        "Напиши сумму и описание.\n\n"
        "Например:\n"
        "50000 зарплата\n\n"
        "Или:\n"
        "3000 подработка",
        reply_markup=back_keyboard()
    )


@dp.callback_query(F.data == "expense")
async def expense_handler(callback: CallbackQuery):
    await callback.answer()

    user_states[callback.from_user.id] = "expense"

    await callback.message.edit_text(
        "➖ Новый расход\n\n"
        "Напиши сумму и описание.\n\n"
        "Например:\n"
        "1500 продукты\n\n"
        "Или:\n"
        "2500 одежда",
        reply_markup=back_keyboard()
    )


# =========================================================
# ИСТОРИЯ
# =========================================================

@dp.callback_query(F.data == "history")
async def history(callback: CallbackQuery):
    await callback.answer()

    user_id = callback.from_user.id

    cursor.execute(
        """
        SELECT amount, type, comment, created_at
        FROM transactions
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 15
        """,
        (user_id,)
    )

    transactions = cursor.fetchall()

    if not transactions:
        await callback.message.edit_text(
            "📜 История пока пустая.\n\n"
            "Добавь первую операцию.",
            reply_markup=back_keyboard()
        )
        return

    lines = ["📜 Последние операции\n"]

    for amount, transaction_type, comment, created_at in transactions:

        if transaction_type == "income":
            icon = "🟢"
            sign = "+"
        else:
            icon = "🔴"
            sign = "-"

        lines.append(
            f"{icon} {sign}{amount:,.2f} ₽\n"
            f"   📝 {comment}\n"
            f"   🕐 {created_at}\n"
        )

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=back_keyboard()
    )


# =========================================================
# ЗАПУСК
# =========================================================

async def main():
    print("Бот запущен.")

    await dp.start_polling(
        bot,
        allowed_updates=dp.resolve_used_update_types()
    )


if __name__ == "__main__":
    asyncio.run(main())
async def run_bot():
    await dp.start_polling(
        bot,
        allowed_updates=dp.resolve_used_update_types()
    )
