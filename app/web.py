from datetime import datetime
from fastapi import FastAPI, Request
from sqlalchemy import select
from .db import SessionLocal, Order, Payment
from .services import deliver_account

app = FastAPI(title="WOLFESE DISTRICT")

@app.get("/health")
async def health():
    return {"ok": True, "service": "wolfese-district"}

@app.get("/payment-return")
async def payment_return(order_id: int):
    return {"ok": True, "order_id": order_id}

def nested_value(obj, names):
    if isinstance(obj, dict):
        for name in names:
            if obj.get(name) is not None:
                return obj[name]
        for value in obj.values():
            found = nested_value(value, names)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for value in obj:
            found = nested_value(value, names)
            if found is not None:
                return found
    return None

@app.post("/webhooks/yookassa")
async def yookassa_webhook(request: Request):
    payload = await request.json()
    if payload.get("event") != "payment.succeeded":
        return {"ok": True}

    obj = payload.get("object", {})
    payment_id = obj.get("id")
    order_id = (obj.get("metadata") or {}).get("order_id")
    if not order_id:
        return {"ok": True}

    async with SessionLocal() as session:
        order = await session.get(Order, int(order_id))
        if not order:
            return {"ok": True}

        order.status = "PAID"
        order.paid_at = datetime.utcnow()
        order.payment_id = payment_id

        payment = await session.scalar(
            select(Payment).where(Payment.provider_payment_id == payment_id)
        )
        if not payment:
            payment = Payment(
                order_id=order.id,
                provider_payment_id=payment_id,
                method=order.payment_method,
                bank_id=str(nested_value(obj, ["bank_id"]) or "") or None,
                bank_name=str(nested_value(obj, ["bank_name"]) or "") or None,
                amount=order.amount,
                status="succeeded",
            )
            session.add(payment)

        if order.suspicious:
            await session.commit()
            return {"ok": True, "suspicious": True}

        account = await deliver_account(session, order)
        if account:
            order.status = "DELIVERED"

        await session.commit()
        return {"ok": True, "delivered": bool(account)}
