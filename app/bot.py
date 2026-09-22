from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from .config import BOT_TOKEN, ADMIN_IDS
from .db import (
    init_db,
    add_product,
    get_products,
    get_product,
    create_order,
    get_user_orders,
    get_all_orders,
    delete_product,
)


dp = Dispatcher()


# =========================
# КЛАВИАТУРЫ
# =========================

def main_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🪙 Купить вирты",
                    callback_data="category:virts"
                ),
                InlineKeyboardButton(
                    text="🎮 Купить аккаунт",
                    callback_data="category:accounts"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📦 Мои заказы",
                    callback_data="my_orders"
                ),
                InlineKeyboardButton(
                    text="💬 Поддержка",
                    callback_data="support"
                ),
            ],
        ]
    )


def back_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="◀️ Главное меню",
                    callback_data="main"
                )
            ]
        ]
    )


def admin_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Добавить вирты",
                    callback_data="admin_add:virts"
                )
            ],
            [
                InlineKeyboardButton(
                    text="➕ Добавить аккаунт",
                    callback_data="admin_add:accounts"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📦 Товары",
                    callback_data="admin_products"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🧾 Заказы",
                    callback_data="admin_orders"
                )
            ],
            [
                InlineKeyboardButton(
                    text="◀️ Главное меню",
                    callback_data="main"
                )
            ],
        ]
    )


# =========================
# ВРЕМЕННОЕ СОСТОЯНИЕ АДМИНА
# =========================

admin_states = {}


# =========================
# START
# =========================

@dp.message(Command("start"))
async def start_handler(message: Message):
    text = (
        "👋 <b>Добро пожаловать в MinPay!</b>\n\n"
        "🛒 Магазин игровых товаров\n\n"
        "Здесь можно приобрести:\n"
        "• 🪙 игровую валюту\n"
        "• 🎮 игровые аккаунты\n\n"
        "Выбирай нужный раздел ниже 👇"
    )

    await message.answer(
        text,
        reply_markup=main_keyboard()
    )


# =========================
# ГЛАВНОЕ МЕНЮ
# =========================

@dp.callback_query(F.data == "main")
async def main_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "👋 <b>MinPay</b>\n\n"
        "🛒 Магазин игровых товаров\n\n"
        "Выбирай нужный раздел 👇",
        reply_markup=main_keyboard()
    )

    await callback.answer()


# =========================
# КАТЕГОРИИ
# =========================

@dp.callback_query(F.data.startswith("category:"))
async def category_handler(callback: CallbackQuery):
    category = callback.data.split(":", 1)[1]

    products = get_products(category)

    if category == "virts":
        title = "🪙 <b>Продажа виртов</b>"
    else:
        title = "🎮 <b>Продажа аккаунтов</b>"

    if not products:
        await callback.message.edit_text(
            f"{title}\n\n"
            "😔 Сейчас товаров в этом разделе нет.",
            reply_markup=back_keyboard()
        )
        await callback.answer()
        return

    buttons = []

    for product in products:
        buttons.append([
            InlineKeyboardButton(
                text=f"{product['name']} — {product['price']:.0f} ₽",
                callback_data=f"product:{product['id']}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="◀️ Назад",
            callback_data="main"
        )
    ])

    await callback.message.edit_text(
        title + "\n\nВыбери товар:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=buttons
        )
    )

    await callback.answer()


# =========================
# ТОВАР
# =========================

@dp.callback_query(F.data.startswith("product:"))
async def product_handler(callback: CallbackQuery):
    product_id = int(callback.data.split(":", 1)[1])

    product = get_product(product_id)

    if not product:
        await callback.answer(
            "Товар не найден",
            show_alert=True
        )
        return

    category_name = (
        "🪙 Вирты"
        if product["category"] == "virts"
        else "🎮 Аккаунт"
    )

    text = (
        f"{category_name}\n\n"
        f"<b>{product['name']}</b>\n\n"
        f"{product['description']}\n\n"
        f"💰 Цена: <b>{product['price']:.0f} ₽</b>"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💳 Купить",
                    callback_data=f"buy:{product_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="◀️ Назад",
                    callback_data=f"category:{product['category']}"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        text,
        reply_markup=keyboard
    )

    await callback.answer()


# =========================
# ПОКУПКА
# =========================

@dp.callback_query(F.data.startswith("buy:"))
async def buy_handler(callback: CallbackQuery):
    product_id = int(callback.data.split(":", 1)[1])

    product = get_product(product_id)

    if not product:
        await callback.answer(
            "Товар не найден",
            show_alert=True
        )
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🏦 Сбер",
                    callback_data=f"pay:{product_id}:Сбер"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💳 Т-Банк",
                    callback_data=f"pay:{product_id}:Т-Банк"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏦 Альфа-Банк",
                    callback_data=f"pay:{product_id}:Альфа-Банк"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏦 ВТБ",
                    callback_data=f"pay:{product_id}:ВТБ"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⚡ СБП",
                    callback_data=f"pay:{product_id}:СБП"
                )
            ],
            [
                InlineKeyboardButton(
                    text="◀️ Назад",
                    callback_data=f"product:{product_id}"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        f"💳 <b>Оплата заказа</b>\n\n"
        f"Товар: <b>{product['name']}</b>\n"
        f"Сумма: <b>{product['price']:.0f} ₽</b>\n\n"
        "Выбери способ оплаты:",
        reply_markup=keyboard
    )

    await callback.answer()


# =========================
# СОЗДАНИЕ ЗАКАЗА
# =========================

@dp.callback_query(F.data.startswith("pay:"))
async def payment_handler(callback: CallbackQuery):
    parts = callback.data.split(":", 2)

    product_id = int(parts[1])
    payment_method = parts[2]

    product = get_product(product_id)

    if not product:
        await callback.answer(
            "Товар не найден",
            show_alert=True
        )
        return

    order_id = create_order(
        user_id=callback.from_user.id,
        product_id=product_id,
        payment_method=payment_method
    )

    text = (
        "🧾 <b>Заказ создан</b>\n\n"
        f"Номер заказа: <b>#{order_id}</b>\n"
        f"Товар: <b>{product['name']}</b>\n"
        f"Сумма: <b>{product['price']:.0f} ₽</b>\n"
        f"Оплата: <b>{payment_method}</b>\n\n"
        "💳 Для оплаты используй приложение или официальный сайт выбранного банка.\n\n"
        "После оплаты обратись в поддержку и укажи номер заказа."
    )

    await callback.message.edit_text(
        text,
        reply_markup=back_keyboard()
    )

    await callback.answer("Заказ создан")


# =========================
# МОИ ЗАКАЗЫ
# =========================

@dp.callback_query(F.data == "my_orders")
async def my_orders_handler(callback: CallbackQuery):
    orders = get_user_orders(callback.from_user.id)

    if not orders:
        await callback.message.edit_text(
            "📦 <b>Мои заказы</b>\n\n"
            "У тебя пока нет заказов.",
            reply_markup=back_keyboard()
        )

        await callback.answer()
        return

    lines = ["📦 <b>Мои заказы</b>\n"]

    for order in orders[:20]:
        lines.append(
            f"🧾 #{order['id']} — {order['name']}\n"
            f"💰 {order['price']:.0f} ₽\n"
            f"💳 {order['payment_method']}\n"
            f"📌 Статус: {order['status']}\n"
        )

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=back_keyboard()
    )

    await callback.answer()


# =========================
# ПОДДЕРЖКА
# =========================

@dp.callback_query(F.data == "support")
async def support_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "💬 <b>Поддержка</b>\n\n"
        "Если возникла проблема с заказом, "
        "напиши администратору и укажи номер заказа.",
        reply_markup=back_keyboard()
    )

    await callback.answer()


# =========================
# ADMIN
# =========================

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


@dp.message(Command("admin"))
async def admin_handler(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer(
            "⛔ У тебя нет доступа к админ-панели."
        )
        return

    await message.answer(
        "🛠 <b>Админ-панель MinPay</b>\n\n"
        "Выбери действие:",
        reply_markup=admin_keyboard()
    )


# =========================
# ADMIN ADD
# =========================

@dp.callback_query(F.data.startswith("admin_add:"))
async def admin_add_start(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer(
            "Нет доступа",
            show_alert=True
        )
        return

    category = callback.data.split(":", 1)[1]

    admin_states[callback.from_user.id] = {
        "step": "name",
        "category": category
    }

    await callback.message.edit_text(
        "➕ <b>Добавление товара</b>\n\n"
        "Напиши название товара:"
    )

    await callback.answer()


@dp.message()
async def admin_message_handler(message: Message):
    user_id = message.from_user.id

    if not is_admin(user_id):
        return

    if user_id not in admin_states:
        return

    state = admin_states[user_id]
    step = state["step"]

    if step == "name":
        state["name"] = message.text
        state["step"] = "description"

        await message.answer(
            "📝 Теперь напиши описание товара:"
        )

    elif step == "description":
        state["description"] = message.text
        state["step"] = "price"

        await message.answer(
            "💰 Напиши цену в рублях:\n\n"
            "Например: 500"
        )

    elif step == "price":
        try:
            price = float(message.text.replace(",", "."))
        except ValueError:
            await message.answer(
                "❌ Цена должна быть числом."
            )
            return

        state["price"] = price

        if state["category"] == "accounts":
            state["step"] = "stock"

            await message.answer(
                "🎮 Отправь данные аккаунта.\n\n"
                "Эти данные будут сохранены как содержимое товара."
            )
        else:
            product_id = add_product(
                category=state["category"],
                name=state["name"],
                description=state["description"],
                price=state["price"],
            )

            del admin_states[user_id]

            await message.answer(
                f"✅ Вирты добавлены.\n\n"
                f"ID товара: <b>#{product_id}</b>"
            )

    elif step == "stock":
        product_id = add_product(
            category=state["category"],
            name=state["name"],
            description=state["description"],
            price=state["price"],
            stock=message.text
        )

        del admin_states[user_id]

        await message.answer(
            f"✅ Аккаунт добавлен.\n\n"
            f"ID товара: <b>#{product_id}</b>"
        )


# =========================
# ADMIN PRODUCTS
# =========================

@dp.callback_query(F.data == "admin_products")
async def admin_products_handler(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer(
            "Нет доступа",
            show_alert=True
        )
        return

    virts = get_products("virts")
    accounts = get_products("accounts")

    lines = ["📦 <b>Товары</b>\n"]

    if virts:
        lines.append("🪙 <b>Вирты:</b>")

        for product in virts:
            lines.append(
                f"#{product['id']} — {product['name']} — "
                f"{product['price']:.0f} ₽"
            )

    if accounts:
        lines.append("\n🎮 <b>Аккаунты:</b>")

        for product in accounts:
            lines.append(
                f"#{product['id']} — {product['name']} — "
                f"{product['price']:.0f} ₽"
            )

    if not virts and not accounts:
        lines.append("Товаров пока нет.")

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=back_keyboard()
    )

    await callback.answer()


# =========================
# ADMIN ORDERS
# =========================

@dp.callback_query(F.data == "admin_orders")
async def admin_orders_handler(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer(
            "Нет доступа",
            show_alert=True
        )
        return

    orders = get_all_orders()

    if not orders:
        await callback.message.edit_text(
            "🧾 <b>Заказы</b>\n\n"
            "Заказов пока нет.",
            reply_markup=back_keyboard()
        )

        await callback.answer()
        return

    lines = ["🧾 <b>Последние заказы</b>\n"]

    for order in orders[:30]:
        lines.append(
            f"#{order['id']} — {order['name']}\n"
            f"👤 {order['user_id']}\n"
            f"💰 {order['price']:.0f} ₽\n"
            f"💳 {order['payment_method']}\n"
            f"📌 {order['status']}\n"
        )

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=back_keyboard()
    )

    await callback.answer()


# =========================
# RUN
# =========================

async def run_bot():
    init_db()

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML
        )
    )

    print("MinPay запущен")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
