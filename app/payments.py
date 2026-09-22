import uuid
import aiohttp
from .config import settings

class YooKassaClient:
    async def create_payment(self, order_id, amount, method):
        if not settings.yookassa_shop_id or not settings.yookassa_secret_key:
            raise RuntimeError("YooKassa credentials are not configured")

        payload = {
            "amount": {"value": f"{amount:.2f}", "currency": settings.currency},
            "capture": True,
            "description": f"WOLFESE order #{order_id}",
            "metadata": {"order_id": str(order_id)},
            "payment_method_data": {"type": "sbp" if method == "sbp" else "bank_card"},
            "confirmation": {
                "type": "redirect",
                "return_url": f"{settings.public_base_url.rstrip('/')}/payment-return?order_id={order_id}"
            }
        }

        auth = aiohttp.BasicAuth(settings.yookassa_shop_id, settings.yookassa_secret_key)
        async with aiohttp.ClientSession(auth=auth) as session:
            async with session.post(
                "https://api.yookassa.ru/v3/payments",
                json=payload,
                headers={"Idempotence-Key": str(uuid.uuid4())},
                timeout=30,
            ) as response:
                response.raise_for_status()
                data = await response.json()

        return data["id"], data["confirmation"]["confirmation_url"]
