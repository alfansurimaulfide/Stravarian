from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
db = SQLAlchemy()

def create_app():

    app = Flask(__name__)

    from routes import auth, strava, dashboard
    app.register_blueprint(auth)
    app.register_blueprint(strava)
    app.register_blueprint(dashboard)

    # For local testing, SQLite database in project folder
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = os.getenv("SECRET_KEY", "supersecret")

    db.init_app(app)

    # Create Migrate object
    # 3. What migrate = Migrate(app, db) Actually Does
    # Tells Flask-Migrate which app and which SQLAlchemy database object to monitor.
    # db is the SQLAlchemy object holding your models.
    # app is your Flask instance.
    # You don’t return migrate — it just attaches itself internally and hooks into Flask’s CLI commands (flask db ...).
    migrate = Migrate(app, db)

    return app