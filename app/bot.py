from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from .config import BOT_TOKEN, ADMIN_ID
from .db import (
    init_db,
    add_product,
    get_products,
    get_product,
    create_order,
    get_user_orders,
    get_all_orders,
)

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

user_states = {}


def main_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🪙 Купить вирты",
                    callback_data="virtuals",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎮 Аккаунты",
                    callback_data="accounts",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📦 Мои заказы",
                    callback_data="orders",
                )
            ],
            [
                InlineKeyboardButton(
                    text="💬 Поддержка",
                    callback_data="support",
                )
            ],
        ]
    )


def back_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="◀️ Назад",
                    callback_data="menu",
                )
            ]
        ]
    )


def admin_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Добавить вирты",
                    callback_data="admin_add_virtuals",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎮 Добавить аккаунт",
                    callback_data="admin_add_account",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📦 Товары",
                    callback_data="admin_products",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📋 Заказы",
                    callback_data="admin_orders",
                )
            ],
            [
                InlineKeyboardButton(
                    text="◀️ В магазин",
                    callback_data="menu",
                )
            ],
        ]
    )


@dp.message(CommandStart())
async def start(message: Message):
    text = (
        "💎 <b>MinPay</b>\n\n"
        "Магазин игровых виртов и аккаунтов.\n\n"
        "🪙 Вирты — пакеты до 200 млн\n"
        "🎮 Аккаунты — товары из наличия\n"
        "🔐 Быстрое оформление заказа\n\n"
        "Выбери нужный раздел:"
    )

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=main_menu(),
    )


@dp.callback_query(F.data == "menu")
async def menu(callback: CallbackQuery):
    await callback.answer()

    await callback.message.edit_text(
        "💎 <b>MinPay</b>\n\nВыбери нужный раздел:",
        parse_mode="HTML",
        reply_markup=main_menu(),
    )


@dp.callback_query(F.data == "virtuals")
async def virtuals(callback: CallbackQuery):
    await callback.answer()

    products = get_products("virtuals")

    if not products:
        await callback.message.edit_text(
            "🪙 <b>Вирты</b>\n\n"
            "Сейчас товаров в наличии нет.",
            parse_mode="HTML",
            reply_markup=back_menu(),
        )
        return

    buttons = []

    for product in products:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"🪙 {product['title']} — {product['price']:,.0f} ₽",
                    callback_data=f"product:{product['id']}",
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data="menu",
            )
        ]
    )

    await callback.message.edit_text(
        "🪙 <b>Вирты</b>\n\n"
        "Выбери пакет:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=buttons
        ),
    )


@dp.callback_query(F.data == "accounts")
async def accounts(callback: CallbackQuery):
    await callback.answer()

    products = get_products("accounts")

    if not products:
        await callback.message.edit_text(
            "🎮 <b>Аккаунты</b>\n\n"
            "Сейчас аккаунтов в наличии нет.",
            parse_mode="HTML",
            reply_markup=back_menu(),
        )
        return

    buttons = []

    for product in products:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"🎮 {product['title']} — {product['price']:,.0f} ₽",
                    callback_data=f"product:{product['id']}",
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data="menu",
            )
        ]
    )

    await callback.message.edit_text(
        "🎮 <b>Аккаунты</b>\n\n"
        "Выбери аккаунт:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=buttons
        ),
    )


@dp.callback_query(F.data.startswith("product:"))
async def product_page(callback: CallbackQuery):
    await callback.answer()

    product_id = int(callback.data.split(":")[1])
    product = get_product(product_id)

    if not product or not product["active"]:
        await callback.message.edit_text(
            "❌ Товар больше недоступен.",
            reply_markup=back_menu(),
        )
        return

    description = product["description"] or "Описание отсутствует."

    text = (
        f"<b>{product['title']}</b>\n\n"
        f"{description}\n\n"
        f"💰 Цена: <b>{product['price']:,.0f} ₽</b>\n"
        "📦 В наличии"
    )

    category = product["category"]

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="💳 Выбрать оплату",
                        callback_data=f"pay:{product_id}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="◀️ Назад",
                        callback_data=category,
                    )
                ],
            ]
        ),
    )


@dp.callback_query(F.data.startswith("pay:"))
async def payment_methods(callback: CallbackQuery):
    await callback.answer()

    product_id = int(callback.data.split(":")[1])
    product = get_product(product_id)

    if not product:
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🟢 Сбер",
                    callback_data=f"bank:Сбер:{product_id}",
                ),
                InlineKeyboardButton(
                    text="🔵 Т-Банк",
                    callback_data=f"bank:Т-Банк:{product_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔴 Альфа-Банк",
                    callback_data=f"bank:Альфа-Банк:{product_id}",
                ),
                InlineKeyboardButton(
                    text="🔵 ВТБ",
                    callback_data=f"bank:ВТБ:{product_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🟠 Газпромбанк",
                    callback_data=f"bank:Газпромбанк:{product_id}",
                ),
                InlineKeyboardButton(
                    text="🟡 Совкомбанк",
                    callback_data=f"bank:Совкомбанк:{product_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔵 МТС Банк",
                    callback_data=f"bank:МТС Банк:{product_id}",
                ),
                InlineKeyboardButton(
                    text="🟣 Райффайзен",
                    callback_data=f"bank:Райффайзенбанк:{product_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🟢 Ак Барс",
                    callback_data=f"bank:Ак Барс Банк:{product_id}",
                ),
                InlineKeyboardButton(
                    text="🟠 Уралсиб",
                    callback_data=f"bank:Уралсиб:{product_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🟠 ОТП Банк",
                    callback_data=f"bank:ОТП Банк:{product_id}",
                ),
                InlineKeyboardButton(
                    text="🟢 СБП",
                    callback_data=f"bank:СБП:{product_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="◀️ Назад",
                    callback_data=f"product:{product_id}",
                )
            ],
        ]
    )

    await callback.message.edit_text(
        "💳 <b>Выбор оплаты</b>\n\n"
        f"🛒 {product['title']}\n"
        f"💰 {product['price']:,.0f} ₽\n\n"
        "Выбери удобный способ:",
        parse_mode="HTML",
        reply_markup=keyboard,
    )


@dp.callback_query(F.data.startswith("bank:"))
async def bank_selected(callback: CallbackQuery):
    await callback.answer()

    _, bank, product_id = callback.data.split(":", 2)

    product = get_product(int(product_id))

    if not product:
        return

    order_id = create_order(
        callback.from_user.id,
        product["id"],
        product["price"],
        bank,
    )

    await callback.message.edit_text(
        "💳 <b>Заказ создан</b>\n\n"
        f"🧾 Заказ: <b>#{order_id}</b>\n"
        f"🛒 {product['title']}\n"
        f"💰 {product['price']:,.0f} ₽\n"
        f"🏦 {bank}\n\n"
        "Для оплаты используй официальный сайт или приложение "
        "выбранного банка.\n\n"
        "⚠️ MinPay никогда не запрашивает пароль, SMS-код "
        "или данные карты.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📦 Мои заказы",
                        callback_data="orders",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="◀️ В магазин",
                        callback_data="menu",
                    )
                ],
            ]
        ),
    )


@dp.callback_query(F.data == "orders")
async def orders(callback: CallbackQuery):
    await callback.answer()

    rows = get_user_orders(callback.from_user.id)

    if not rows:
        await callback.message.edit_text(
            "📦 <b>Мои заказы</b>\n\n"
            "У тебя пока нет заказов.",
            parse_mode="HTML",
            reply_markup=back_menu(),
        )
        return

    text = "📦 <b>Мои заказы</b>\n\n"

    for row in rows:
        text += (
            f"🧾 <b>#{row['id']}</b>\n"
            f"🛒 {row['title']}\n"
            f"💰 {row['price']:,.0f} ₽\n"
            f"🏦 {row['payment_method']}\n"
            f"📌 {row['status']}\n"
            f"🕐 {row['created_at']}\n\n"
        )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=back_menu(),
    )


@dp.callback_query(F.data == "support")
async def support(callback: CallbackQuery):
    await callback.answer()

    await callback.message.edit_text(
        "💬 <b>Поддержка MinPay</b>\n\n"
        "Если возникла проблема с заказом или оплатой — "
        "обратись к администратору.",
        parse_mode="HTML",
        reply_markup=back_menu(),
    )


@dp.message(F.text == "/admin")
async def admin(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Доступ запрещён.")
        return

    await message.answer(
        "🔐 <b>MinPay — админ-панель</b>",
        parse_mode="HTML",
        reply_markup=admin_menu(),
    )


@dp.callback_query(F.data.startswith("admin_"))
async def admin_callbacks(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer(
            "Доступ запрещён.",
            show_alert=True,
        )
        return

    await callback.answer()

    if callback.data == "admin_add_virtuals":
        user_states[callback.from_user.id] = "add_virtuals"

        await callback.message.edit_text(
            "➕ <b>Добавление виртов</b>\n\n"
            "Формат:\n\n"
            "<code>50 млн виртов | 2500 | Быстрая выдача</code>\n\n"
            "Можно добавлять пакеты вплоть до 200 млн.",
            parse_mode="HTML",
            reply_markup=back_menu(),
        )

    elif callback.data == "admin_add_account":
        user_states[callback.from_user.id] = "add_account"

        await callback.message.edit_text(
            "🎮 <b>Добавление аккаунта</b>\n\n"
            "Формат:\n\n"
            "<code>Название | Цена | Описание | Данные аккаунта</code>",
            parse_mode="HTML",
            reply_markup=back_menu(),
        )

    elif callback.data == "admin_products":
        products = get_products()

        if not products:
            text = "📦 Товаров пока нет."
        else:
            text = "📦 <b>Товары</b>\n\n"

            for product in products:
                text += (
                    f"#{product['id']} — {product['title']}\n"
                    f"💰 {product['price']:,.0f} ₽\n\n"
                )

        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=admin_menu(),
        )

    elif callback.data == "admin_orders":
        rows = get_all_orders()

        if not rows:
            text = "📋 Заказов пока нет."
        else:
            text = "📋 <b>Последние заказы</b>\n\n"

            for row in rows:
                text += (
                    f"🧾 #{row['id']} — {row['title']}\n"
                    f"👤 {row['user_id']}\n"
                    f"💰 {row['price']:,.0f} ₽\n"
                    f"🏦 {row['payment_method']}\n"
                    f"📌 {row['status']}\n\n"
                )

        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=admin_menu(),
        )


@dp.message(F.text)
async def admin_product_input(message: Message):
    if user_id not in ADMIN_IDS:
        return
        

    state = user_states.get(message.from_user.id)

    if state == "add_virtuals":
        parts = [x.strip() for x in message.text.split("|")]

        if len(parts) < 3:
            await message.answer(
                "❌ Нужно:\n\n"
                "Название | Цена | Описание"
            )
            return

        title = parts[0]

        try:
            price = float(
                parts[1]
                .replace(",", ".")
                .replace("₽", "")
                .strip()
            )
        except ValueError:
            await message.answer("❌ Неверная цена.")
            return

        description = parts[2]

        product_id = add_product(
            "virtuals",
            title,
            description,
            price,
        )

        user_states.pop(message.from_user.id, None)

        await message.answer(
            f"✅ Вирты добавлены.\n\n"
            f"🧾 ID: #{product_id}\n"
            f"🪙 {title}\n"
            f"💰 {price:,.0f} ₽",
            reply_markup=admin_menu(),
        )

    elif state == "add_account":
        parts = [x.strip() for x in message.text.split("|")]

        if len(parts) < 4:
            await message.answer(
                "❌ Нужно:\n\n"
                "Название | Цена | Описание | Данные аккаунта"
            )
            return

        title = parts[0]

        try:
            price = float(
                parts[1]
                .replace(",", ".")
                .replace("₽", "")
                .strip()
            )
        except ValueError:
            await message.answer("❌ Неверная цена.")
            return

        description = parts[2]
        stock = parts[3]

        product_id = add_product(
            "accounts",
            title,
            description,
            price,
            stock,
        )

        user_states.pop(message.from_user.id, None)

        await message.answer(
            f"✅ Аккаунт добавлен.\n\n"
            f"🧾 ID: #{product_id}\n"
            f"🎮 {title}\n"
            f"💰 {price:,.0f} ₽",
            reply_markup=admin_menu(),
        )

#dd
async def run_bot():
    init_db()

    print("MinPay запущен.")

    await dp.start_polling(
        bot,
        allowed_updates=dp.resolve_used_update_types(),
    )
