import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-production"
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or "sqlite:///chessgrunts.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Strava OAuth
    STRAVA_CLIENT_ID = os.environ.get("STRAVA_CLIENT_ID")
    STRAVA_CLIENT_SECRET = os.environ.get("STRAVA_CLIENT_SECRET")
    STRAVA_REDIRECT_URI = os.environ.get("STRAVA_REDIRECT_URI", "http://localhost:5000/auth/strava/callback")
    STRAVA_AUTH_URL = "https://www.strava.com/oauth/authorize"
    STRAVA_TOKEN_URL = "https://www.strava.com/oauth/token"
    STRAVA_API_BASE = "https://www.strava.com/api/v3"

    # Chess.com API (no auth needed — public)
    CHESSDOTCOM_API_BASE = "https://api.chess.com/pub"

    # Lichess API
    LICHESS_API_BASE = "https://lichess.org/api"
    LICHESS_TOKEN = os.environ.get("LICHESS_TOKEN")  # optional, for higher rate limits

    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)
    REMEMBER_COOKIE_DURATION = timedelta(days=30)


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
