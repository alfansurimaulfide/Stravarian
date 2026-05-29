from flask import Flask
# from flask_sqlalchemy import SQLAlchemy
# from flask_login import LoginManager
# from flask_migrate import Migrate
# from apscheduler.schedulers.background import BackgroundScheduler
from config import Config
from models import User
from extensions import db, login_manager, migrate, scheduler

# db = SQLAlchemy()
# login_manager = LoginManager()
# migrate = Migrate()
# scheduler = BackgroundScheduler()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from routes.auth import auth_bp
    from routes.running import running_bp
    from routes.chess import chess_bp
    from routes.chessgrunts import chessgrunts_bp
    from routes.main import main_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(running_bp, url_prefix="/running")
    app.register_blueprint(chess_bp, url_prefix="/chess")
    app.register_blueprint(chessgrunts_bp, url_prefix="/chessgrunts")
    app.register_blueprint(main_bp)

    # Background jobs
    from services.strava_service import sync_all_strava
    from services.chess_service import sync_all_chess

    if not scheduler.running:
        scheduler.add_job(
            func=lambda: sync_all_strava(app),
            trigger="interval",
            hours=1,
            id="strava_sync",
            replace_existing=True,
        )
        scheduler.add_job(
            func=lambda: sync_all_chess(app),
            trigger="interval",
            minutes=30,
            id="chess_sync",
            replace_existing=True,
        )
        scheduler.start()

    return app


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True)
