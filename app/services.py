from datetime import datetime, timedelta
from sqlalchemy import func, select
from .config import settings
from .db import InventoryAccount, Order

async def suspicious_order(session, amount):
    if amount >= settings.suspicious_amount_rub:
        return True
    since = datetime.utcnow() - timedelta(hours=1)
    count = await session.scalar(select(func.count(Order.id)).where(Order.created_at >= since))
    return (count or 0) >= settings.suspicious_orders_per_hour

async def deliver_account(session, order):
    result = await session.execute(
        select(InventoryAccount)
        .where(
            InventoryAccount.product_id == order.product_id,
            InventoryAccount.reserved_order_id == order.id,
            InventoryAccount.status == "reserved",
        )
        .with_for_update()
    )
    account = result.scalar_one_or_none()
    if not account:
        return None
    account.status = "sold"
    return account
