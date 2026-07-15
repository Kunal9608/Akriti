"""
Akriti Lab — Application Settings
Loads all configuration from environment variables / .env file.
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List
import os


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/akriti_lab"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET_KEY: str = "change-this-secret"
    JWT_ACCESS_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_EXPIRE_HOURS: int = 4
    JWT_ALGORITHM: str = "HS256"

    # Email
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = "kunaldixit.2995@gmail.com"
    MAIL_FROM_NAME: str = "Akriti Diagnostics Center"
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_TLS: bool = True
    MAIL_SSL: bool = False
    BREVO_API_KEY: str = ""

    # Lab
    LAB_UPI_VPA: str = "akritilab@upi"
    LAB_NAME: str = "Akriti Diagnostics Center"
    LAB_ADDRESS: str = ""
    LAB_PHONE: str = ""
    LAB_GSTIN: str = ""

    # Face Recognition
    FACE_MATCH_THRESHOLD: float = 0.6
    FACE_MIN_SAMPLES: int = 3

    # Seed
    ADMIN_SEED_EMAIL: str = "kunaldixit.2995@gmail.com"
    ADMIN_SEED_TEMP_PASSWORD: str = "Akriti@2024"

    # Google reCAPTCHA
    RECAPTCHA_SITE_KEY: str = "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"
    RECAPTCHA_SECRET_KEY: str = "6LeIxAcTAAAAAGG-vFI1TnFTxWGRtAUMuO_FnD4Q"
    ENABLE_RECAPTCHA: bool = False

    # ClamAV Antivirus
    ENABLE_CLAMAV: bool = False
    CLAMAV_HOST: str = "localhost"
    CLAMAV_PORT: int = 3310

    # Environment
    ENVIRONMENT: str = "development"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:8000,http://127.0.0.1:8000"

    @property
    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @property
    def cookie_secure(self) -> bool:
        return self.is_production

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
