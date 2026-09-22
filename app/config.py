from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    bot_token: str
    admin_ids: str = ""
    database_url: str
    public_base_url: str = ""
    yookassa_shop_id: str = ""
    yookassa_secret_key: str = ""
    support_username: str = "@suport_wolfese_shop"
    currency: str = "RUB"
    suspicious_review_minutes: int = 30
    suspicious_amount_rub: int = 50000
    suspicious_orders_per_hour: int = 3

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def admin_id_set(self):
        return {int(x.strip()) for x in self.admin_ids.split(",") if x.strip().isdigit()}

settings = Settings()
