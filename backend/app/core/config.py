from dotenv import load_dotenv
import os

load_dotenv()

class Settings:

    # Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY")
    SUPABASE_JWT_SECRET: str = os.getenv("SUPABASE_JWT_SECRET")
    DATABASE_URL: str = os.getenv("DATABASE_URL")

    # OpenRouter
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY")
    
    # Amadeus
    AMADEUS_CLIENT_ID: str = os.getenv("AMADEUS_CLIENT_ID")
    AMADEUS_CLIENT_SECRET: str = os.getenv("AMADEUS_CLIENT_SECRET")
    AMADEUS_ENV: str = os.getenv("AMADEUS_ENV")

    # Google Calendar
    GOOGLE_CALENDAR_CREDENTIALS_JSON: str = os.getenv("GOOGLE_CALENDAR_CREDENTIALS_JSON")

    # Resend
    RESEND_API_KEY: str = os.getenv("RESEND_API_KEY")
    RESEND_FROM_EMAIL: str = os.getenv("RESEND_FROM_EMAIL")

    # App
    APP_NAME: str = os.getenv("APP_NAME")
    APP_VERSION: str = os.getenv("APP_VERSION")
    APP_ENV: str = os.getenv("APP_ENV")
    APP_DEBUG: bool = os.getenv("APP_DEBUG")
    APP_CORS_ALLOWED_ORIGINS: list[str] = (
        os.getenv("APP_CORS_ALLOWED_ORIGINS", "").split(",")
        if os.getenv("APP_CORS_ALLOWED_ORIGINS")
        else []
    )
    APP_JWT_SECRET: str = os.getenv("APP_JWT_SECRET")
    APP_JWT_EXP_TIME: int = int(os.getenv("APP_JWT_EXP_TIME", "30"))  # minutes
    APP_REFRESH_TOKEN_DAYS: int = int(os.getenv("APP_REFRESH_TOKEN_DAYS", "7"))

    # LLM

settings = Settings()