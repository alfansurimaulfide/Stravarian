from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timedelta
# db = SQLAlchemy()
from app import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    password = db.Column(db.String(200))

    strava_id = db.Column(db.String(50))
    strava_token = db.Column(db.String(200))
    refresh_token = db.Column(db.String(200))

    token_expiry = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)