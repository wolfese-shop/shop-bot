from sqlalchemy import func, select
from .db import Payment

async def bank_stats(session):
    result = await session.execute(
        select(Payment.bank_name, func.count(Payment.id))
        .where(Payment.status == "succeeded")
        .group_by(Payment.bank_name)
        .order_by(func.count(Payment.id).desc())
    )
    return [(name or "Не определён", count) for name, count in result.all()]

async def method_stats(session):
    result = await session.execute(
        select(Payment.method, func.count(Payment.id))
        .where(Payment.status == "succeeded")
        .group_by(Payment.method)
        .order_by(func.count(Payment.id).desc())
    )
    return [(name or "Не определён", count) for name, count in result.all()]
