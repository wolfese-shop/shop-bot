from decimal import Decimal
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from sqlalchemy import select
from .config import settings
from .db import SessionLocal, User, Product, Order
from .payments import YooKassaClient
from .services import suspicious_order
from .bank_analytics import bank_stats, method_stats

dp = Dispatcher()

def products_keyboard(products):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🛒 {p.name} — {p.price} ₽", callback_data=f"product:{p.id}")]
        for p in products
    ])

@dp.message(Command("start"))
async def start(message: Message):
    async with SessionLocal() as session:
        user = await session.scalar(select(User).where(User.telegram_id == message.from_user.id))
        if not user:
            session.add(User(telegram_id=message.from_user.id, username=message.from_user.username))
        products = (await session.execute(
            select(Product).where(Product.active == True).order_by(Product.id)
        )).scalars().all()
        await session.commit()
    await message.answer(
        "🐺 <b>WOLFESE DISTRICT</b>\n\nВыбери товар:",
        reply_markup=products_keyboard(products)
    )

@dp.callback_query(F.data.startswith("product:"))
async def product(call: CallbackQuery):
    product_id = int(call.data.split(":")[1])
    async with SessionLocal() as session:
        p = await session.get(Product, product_id)
    if not p or not p.active:
        await call.answer("Товар недоступен", show_alert=True)
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 СБП", callback_data=f"buy:{p.id}:sbp")],
        [InlineKeyboardButton(text="💳 Банковская карта", callback_data=f"buy:{p.id}:bank_card")]
    ])
    await call.message.answer(
        f"🐺 <b>{p.name}</b>\n\n{p.description}\n\n💰 <b>{p.price} ₽</b>",
        reply_markup=kb
    )
    await call.answer()

@dp.callback_query(F.data.startswith("buy:"))
async def buy(call: CallbackQuery):
    _, product_id, method = call.data.split(":")
    async with SessionLocal() as session:
        p = await session.get(Product, int(product_id))
        user = await session.scalar(select(User).where(User.telegram_id == call.from_user.id))
        if not p or not user:
            await call.answer("Ошибка", show_alert=True)
            return
        order = Order(
            user_id=user.id,
            product_id=p.id,
            amount=Decimal(p.price),
            status="WAITING_PAYMENT",
            payment_method=method,
        )
        session.add(order)
        await session.flush()
        order.suspicious = await suspicious_order(session, order.amount)
        await session.commit()
        order_id = order.id
        amount = p.price

    try:
        payment_id, url = await YooKassaClient().create_payment(order_id, amount, method)
    except Exception:
        await call.message.answer("⚠️ Не удалось создать оплату. Проверь настройки платёжного провайдера.")
        await call.answer()
        return

    async with SessionLocal() as session:
        order = await session.get(Order, order_id)
        order.payment_id = payment_id
        await session.commit()

    await call.message.answer(
        f"🧾 Заказ <b>#{order_id}</b>\n💰 {amount} ₽",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 ОПЛАТИТЬ", url=url)]
        ])
    )
    await call.answer()

@dp.message(Command("orders"))
async def orders(message: Message):
    async with SessionLocal() as session:
        user = await session.scalar(select(User).where(User.telegram_id == message.from_user.id))
        if not user:
            await message.answer("Заказов пока нет.")
            return
        rows = (await session.execute(
            select(Order).where(Order.user_id == user.id).order_by(Order.id.desc()).limit(10)
        )).scalars().all()
    await message.answer("\n".join(
        f"🧾 #{o.id} — {o.amount} ₽ — {o.status}" for o in rows
    ) or "Заказов пока нет.")

@dp.message(Command("banks"))
async def banks(message: Message):
    if message.from_user.id not in settings.admin_id_set:
        return
    async with SessionLocal() as session:
        bs = await bank_stats(session)
        ms = await method_stats(session)
    text = ["🏦 <b>БАНКИ КЛИЕНТОВ</b>"]
    text += [f"{i}. {name} — {count}" for i, (name, count) in enumerate(bs, 1)] or ["Нет данных"]
    text += ["", "💳 <b>СПОСОБЫ ОПЛАТЫ</b>"]
    text += [f"• {name} — {count}" for name, count in ms]
    await message.answer("\n".join(text))

@dp.message(Command("stock"))
async def stock(message: Message):
    if message.from_user.id not in settings.admin_id_set:
        return
    async with SessionLocal() as session:
        products = (await session.execute(select(Product))).scalars().all()
    await message.answer("\n".join(f"#{p.id} {p.name} — {p.price} ₽" for p in products) or "Товаров нет.")

async def run_bot():
    bot = Bot(settings.bot_token)
    await dp.start_polling(bot)
