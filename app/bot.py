from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from .config import BOT_TOKEN, ADMIN_IDS, SUPPORT_USERNAME
from .db import (
    init_db,
    save_user,
    add_product,
    get_products,
    get_product,
    create_order,
    get_user_orders,
    get_all_orders,
    get_all_products,
    deactivate_product
)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# =========================
# КАТЕГОРИИ
# =========================

CATEGORY_VIRTS = "virts"
CATEGORY_ACCOUNTS = "accounts"


# =========================
# БАНКИ
# =========================

BANKS = {
    "sber": "🏦 Сбербанк",
    "tbank": "🟡 Т-Банк",
    "alfa": "🔴 Альфа-Банк",
    "vtb": "🔵 ВТБ",
    "sbp": "⚡ СБП",
    "gazprom": "🔷 Газпромбанк",
    "mts": "🔴 МТС Банк",
    "rosbank": "🏦 Росбанк",
    "sovcom": "🟢 Совкомбанк",
    "otp": "🏦 ОТП Банк",
    "raiffeisen": "🟡 Райффайзенбанк",
    "bspb": "🔵 Банк Санкт-Петербург",
    "akbars": "🟢 Ак Барс",
    "uralsib": "🔵 Уралсиб",
    "pochta": "🟠 Почта Банк",
}


# =========================
# СОСТОЯНИЯ АДМИНА
# =========================

class AdminProduct(StatesGroup):
    category = State()
    name = State()
    description = State()
    price = State()
    stock = State()


# =========================
# КЛАВИАТУРЫ
# =========================

def main_keyboard(user_id: int):
    buttons = [
        [
            KeyboardButton(text="🪙 Купить вирты"),
            KeyboardButton(text="🎮 Купить аккаунт")
        ],
        [
            KeyboardButton(text="📦 Мои заказы"),
            KeyboardButton(text="💬 Поддержка")
        ]
    ]

    if user_id in ADMIN_IDS:
        buttons.append([
            KeyboardButton(text="🛠 Админ-панель")
        ])

    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        is_persistent=True
    )


def back_button():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Главное меню",
                    callback_data="main_menu"
                )
            ]
        ]
    )


def category_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🪙 Вирты",
                    callback_data="category_virts"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎮 Аккаунты",
                    callback_data="category_accounts"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="main_menu"
                )
            ]
        ]
    )


def products_keyboard(products):
    buttons = []

    for product in products:
        buttons.append([
            InlineKeyboardButton(
                text=f"{product['name']} — {product['price']:.2f} ₽",
                callback_data=f"product_{product['id']}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data="main_menu"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def banks_keyboard(product_id):
    buttons = []

    bank_items = list(BANKS.items())

    for i in range(0, len(bank_items), 2):
        row = []

        for key, name in bank_items[i:i + 2]:
            row.append(
                InlineKeyboardButton(
                    text=name,
                    callback_data=f"bank_{key}_{product_id}"
                )
            )

        buttons.append(row)

    buttons.append([
        InlineKeyboardButton(
            text="⬅️ Назад к товару",
            callback_data=f"product_{product_id}"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Добавить товар",
                    callback_data="admin_add"
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
                    text="⬅️ Главное меню",
                    callback_data="main_menu"
                )
            ]
        ]
    )


def admin_category_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🪙 Вирты",
                    callback_data="admin_cat_virts"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎮 Аккаунт",
                    callback_data="admin_cat_accounts"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отмена",
                    callback_data="admin_cancel"
                )
            ]
        ]
    )


# =========================
# ГЛАВНЫЙ ЭКРАН
# =========================

WELCOME_TEXT = """
🐺 <b>VULFIS — МАГАЗИН ВИРТОВ И АККАУНТОВ</b>

Добро пожаловать в <b>Vulfis</b> — магазин, где можно быстро приобрести игровую валюту и аккаунты.

🪙 <b>ВИРТЫ</b>
Покупайте игровую валюту в нужном количестве. Перед оформлением заказа вы увидите актуальную стоимость и информацию о товаре.

🎮 <b>АККАУНТЫ</b>
Выбирайте доступные игровые аккаунты из каталога. Перед покупкой можно ознакомиться с описанием предложения.

📦 <b>КАК ПРОИСХОДИТ ПОКУПКА</b>

1️⃣ Выберите нужную категорию.
2️⃣ Выберите товар.
3️⃣ Ознакомьтесь с описанием и стоимостью.
4️⃣ Выберите удобный способ оплаты.
5️⃣ Оформите заказ.
6️⃣ После обработки заказа получите товар согласно условиям покупки.

🔒 <b>ЗАКАЗЫ И ИСТОРИЯ</b>
Все оформленные заказы сохраняются в системе. Историю покупок можно посмотреть в разделе «Мои заказы».

💬 <b>ПОДДЕРЖКА</b>
Если у вас возник вопрос по товару, оплате или заказу — обратитесь в поддержку Vulfis.

👇 <b>Выберите нужный раздел ниже и начните покупку.</b>
"""


async def show_main(message: Message):
    await message.answer(
        WELCOME_TEXT,
        reply_markup=main_keyboard(message.from_user.id),
        parse_mode="HTML"
    )


# =========================
# START
# =========================

@dp.message(Command("start"))
async def start(message: Message):
    save_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name
    )

    await show_main(message)


@dp.message(Command("menu"))
async def menu(message: Message):
    await show_main(message)


# =========================
# ПОКУПКА ВИРТОВ
# =========================

@dp.message(F.text == "🪙 Купить вирты")
async def buy_virts(message: Message):
    products = get_products(CATEGORY_VIRTS)

    if not products:
        await message.answer(
            "🪙 <b>Вирты</b>\n\n"
            "Сейчас доступных предложений нет.\n"
            "Попробуйте зайти позже.",
            parse_mode="HTML"
        )
        return

    await message.answer(
        "🪙 <b>ПОКУПКА ВИРТОВ</b>\n\n"
        "Выберите нужное предложение:",
        reply_markup=products_keyboard(products),
        parse_mode="HTML"
    )


# =========================
# ПОКУПКА АККАУНТОВ
# =========================

@dp.message(F.text == "🎮 Купить аккаунт")
async def buy_accounts(message: Message):
    products = get_products(CATEGORY_ACCOUNTS)

    if not products:
        await message.answer(
            "🎮 <b>АККАУНТЫ</b>\n\n"
            "Сейчас доступных аккаунтов нет.\n"
            "Попробуйте зайти позже.",
            parse_mode="HTML"
        )
        return

    await message.answer(
        "🎮 <b>АККАУНТЫ</b>\n\n"
        "Выберите интересующее предложение:",
        reply_markup=products_keyboard(products),
        parse_mode="HTML"
    )


# =========================
# ТОВАР
# =========================

@dp.callback_query(F.data.startswith("product_"))
async def product_view(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[1])
    product = get_product(product_id)

    if not product or not product["active"]:
        await callback.answer(
            "Товар больше недоступен.",
            show_alert=True
        )
        return

    category_icon = (
        "🪙"
        if product["category"] == CATEGORY_VIRTS
        else "🎮"
    )

    text = (
        f"{category_icon} <b>{product['name']}</b>\n\n"
        f"{product['description']}\n\n"
        f"💰 <b>Стоимость:</b> {product['price']:.2f} ₽\n\n"
        "👇 Выберите способ оплаты:"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💳 Выбрать способ оплаты",
                    callback_data=f"choose_bank_{product_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data=(
                        "category_virts"
                        if product["category"] == CATEGORY_VIRTS
                        else "category_accounts"
                    )
                )
            ]
        ]
    )

    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()


# =========================
# БАНКИ
# =========================

@dp.callback_query(F.data.startswith("choose_bank_"))
async def choose_bank(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[2])
    product = get_product(product_id)

    if not product:
        await callback.answer(
            "Товар не найден.",
            show_alert=True
        )
        return

    await callback.message.edit_text(
        "💳 <b>СПОСОБ ОПЛАТЫ</b>\n\n"
        "Выберите банк или способ оплаты:",
        reply_markup=banks_keyboard(product_id),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================
# СОЗДАНИЕ ЗАКАЗА
# =========================

@dp.callback_query(F.data.startswith("bank_"))
async def select_bank(callback: CallbackQuery):
    _, bank_key, product_id = callback.data.split("_")

    product_id = int(product_id)
    product = get_product(product_id)

    if not product:
        await callback.answer(
            "Товар не найден.",
            show_alert=True
        )
        return

    bank_name = BANKS.get(bank_key, "Неизвестный способ")

    order_id = create_order(
        callback.from_user.id,
        product_id,
        bank_name
    )

    text = (
        "✅ <b>ЗАКАЗ СОЗДАН</b>\n\n"
        f"🧾 <b>Номер заказа:</b> #{order_id}\n"
        f"📦 <b>Товар:</b> {product['name']}\n"
        f"💰 <b>Сумма:</b> {product['price']:.2f} ₽\n"
        f"💳 <b>Оплата:</b> {bank_name}\n\n"
        "📌 Заказ зарегистрирован в системе.\n\n"
        "Для дальнейших действий обратитесь в поддержку."
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💬 Написать в поддержку",
                    url=f"https://t.me/{SUPPORT_USERNAME.lstrip('@')}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📦 Мои заказы",
                    callback_data="my_orders"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏠 Главное меню",
                    callback_data="main_menu"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer("Заказ создан")


# =========================
# МОИ ЗАКАЗЫ
# =========================

@dp.message(F.text == "📦 Мои заказы")
async def my_orders_message(message: Message):
    await show_orders(message)


@dp.callback_query(F.data == "my_orders")
async def my_orders_callback(callback: CallbackQuery):
    await show_orders(callback.message)
    await callback.answer()


async def show_orders(message: Message):
    orders = get_user_orders(message.chat.id)

    if not orders:
        await message.answer(
            "📦 <b>МОИ ЗАКАЗЫ</b>\n\n"
            "У вас пока нет оформленных заказов.",
            parse_mode="HTML"
        )
        return

    text = "📦 <b>МОИ ЗАКАЗЫ</b>\n\n"

    for order in orders:
        text += (
            f"🧾 <b>#{order['id']}</b>\n"
            f"📦 {order['product_name']}\n"
            f"💰 {order['product_price']:.2f} ₽\n"
            f"💳 {order['payment_method']}\n"
            f"📌 {order['status']}\n"
            f"📅 {order['created_at']}\n\n"
        )

    await message.answer(
        text,
        parse_mode="HTML"
    )


# =========================
# ПОДДЕРЖКА
# =========================

@dp.message(F.text == "💬 Поддержка")
async def support(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💬 Написать в поддержку",
                    url=f"https://t.me/{SUPPORT_USERNAME.lstrip('@')}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Главное меню",
                    callback_data="main_menu"
                )
            ]
        ]
    )

    await message.answer(
        "💬 <b>ПОДДЕРЖКА VULFIS</b>\n\n"
        "Если у вас возникли вопросы по товару, "
        "оплате или уже оформленному заказу — "
        "напишите нашей поддержке.\n\n"
        "Перед обращением по заказу желательно "
        "указать его номер.\n\n"
        f"👤 Поддержка: <b>{SUPPORT_USERNAME}</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


# =========================
# АДМИН-ПАНЕЛЬ
# =========================

@dp.message(F.text == "🛠 Админ-панель")
async def admin_panel_message(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    await message.answer(
        "🛠 <b>АДМИН-ПАНЕЛЬ VULFIS</b>\n\n"
        "Здесь можно управлять товарами и просматривать заказы.",
        reply_markup=admin_keyboard(),
        parse_mode="HTML"
    )


@dp.callback_query(F.data == "admin_panel")
async def admin_panel_callback(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Доступ запрещён.", show_alert=True)
        return

    await callback.message.edit_text(
        "🛠 <b>АДМИН-ПАНЕЛЬ VULFIS</b>\n\n"
        "Выберите нужное действие:",
        reply_markup=admin_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================
# ДОБАВЛЕНИЕ ТОВАРА
# =========================

@dp.callback_query(F.data == "admin_add")
async def admin_add(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Доступ запрещён.", show_alert=True)
        return

    await state.set_state(AdminProduct.category)

    await callback.message.edit_text(
        "➕ <b>ДОБАВЛЕНИЕ ТОВАРА</b>\n\n"
        "Выберите категорию:",
        reply_markup=admin_category_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()


@dp.callback_query(F.data.startswith("admin_cat_"))
async def admin_category(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        return

    category = callback.data.replace("admin_cat_", "")

    await state.update_data(category=category)
    await state.set_state(AdminProduct.name)

    await callback.message.edit_text(
        "✏️ Введите название товара:"
    )

    await callback.answer()


@dp.message(AdminProduct.name)
async def admin_name(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return

    await state.update_data(name=message.text)
    await state.set_state(AdminProduct.description)

    await message.answer(
        "📝 Введите описание товара:"
    )


@dp.message(AdminProduct.description)
async def admin_description(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return

    await state.update_data(description=message.text)
    await state.set_state(AdminProduct.price)

    await message.answer(
        "💰 Введите цену товара в рублях:\n\n"
        "Например: <code>500</code>",
        parse_mode="HTML"
    )


@dp.message(AdminProduct.price)
async def admin_price(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return

    try:
        price = float(message.text.replace(",", "."))
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer(
            "❌ Введите корректную цену числом."
        )
        return

    await state.update_data(price=price)
    await state.set_state(AdminProduct.stock)

    await message.answer(
        "📦 Введите содержимое товара / данные аккаунта.\n\n"
        "Если дополнительного содержимого нет — напишите <code>Нет</code>.",
        parse_mode="HTML"
    )


@dp.message(AdminProduct.stock)
async def admin_stock(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return

    data = await state.get_data()

    product_id = add_product(
        category=data["category"],
        name=data["name"],
        description=data["description"],
        price=data["price"],
        stock=message.text
    )

    await state.clear()

    await message.answer(
        "✅ <b>ТОВАР ДОБАВЛЕН</b>\n\n"
        f"🆔 ID: <code>{product_id}</code>\n"
        f"📦 {data['name']}\n"
        f"💰 {data['price']:.2f} ₽",
        reply_markup=main_keyboard(message.from_user.id),
        parse_mode="HTML"
    )


# =========================
# АДМИН — ТОВАРЫ
# =========================

@dp.callback_query(F.data == "admin_products")
async def admin_products(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return

    products = get_all_products()

    if not products:
        await callback.message.edit_text(
            "📦 <b>ТОВАРЫ</b>\n\n"
            "Товаров пока нет.",
            reply_markup=admin_keyboard(),
            parse_mode="HTML"
        )
        return

    text = "📦 <b>ТОВАРЫ VULFIS</b>\n\n"

    for product in products:
        status = "🟢" if product["active"] else "🔴"

        text += (
            f"{status} <b>#{product['id']} — {product['name']}</b>\n"
            f"💰 {product['price']:.2f} ₽\n\n"
        )

    await callback.message.edit_text(
        text,
        reply_markup=admin_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================
# АДМИН — ЗАКАЗЫ
# =========================

@dp.callback_query(F.data == "admin_orders")
async def admin_orders(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return

    orders = get_all_orders()

    if not orders:
        await callback.message.edit_text(
            "🧾 <b>ЗАКАЗЫ</b>\n\n"
            "Заказов пока нет.",
            reply_markup=admin_keyboard(),
            parse_mode="HTML"
        )
        return

    text = "🧾 <b>ЗАКАЗЫ VULFIS</b>\n\n"

    for order in orders[:30]:
        text += (
            f"🧾 <b>#{order['id']}</b>\n"
            f"👤 ID: <code>{order['user_id']}</code>\n"
            f"📦 {order['product_name']}\n"
            f"💰 {order['product_price']:.2f} ₽\n"
            f"💳 {order['payment_method']}\n"
            f"📌 {order['status']}\n\n"
        )

    await callback.message.edit_text(
        text,
        reply_markup=admin_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================
# ГЛАВНОЕ МЕНЮ
# =========================

@dp.callback_query(F.data == "main_menu")
async def main_menu(callback: CallbackQuery):
    await callback.message.delete()

    await callback.message.answer(
        WELCOME_TEXT,
        reply_markup=main_keyboard(callback.from_user.id),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================
# ОТМЕНА
# =========================

@dp.callback_query(F.data == "admin_cancel")
async def admin_cancel(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        return

    await state.clear()

    await callback.message.edit_text(
        "🛠 <b>АДМИН-ПАНЕЛЬ VULFIS</b>",
        reply_markup=admin_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================
# ЗАПУСК
# =========================

async def run_bot():
    init_db()

    print("🐺 Vulfis запускается...")

    await dp.start_polling(bot)
