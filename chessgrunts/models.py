from extensions import db, login_manager
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


# @login_manager.user_loader
# def load_user(user_id):
#     return User.query.get(int(user_id))


# ─── User ────────────────────────────────────────────────────────────────────

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    avatar_url = db.Column(db.String(512))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Strava
    strava_id = db.Column(db.BigInteger, unique=True)
    strava_access_token = db.Column(db.String(256))
    strava_refresh_token = db.Column(db.String(256))
    strava_token_expires = db.Column(db.Integer)
    strava_connected = db.Column(db.Boolean, default=False)

    # Chess platforms
    chessdotcom_username = db.Column(db.String(64))
    lichess_username = db.Column(db.String(64))

    # Relationships
    run_activities = db.relationship("RunActivity", backref="user", lazy="dynamic")
    chess_games = db.relationship("ChessGame", backref="user", lazy="dynamic")
    event_memberships = db.relationship("EventMembership", backref="user", lazy="dynamic")
    chessrunt_sessions = db.relationship("ChessgRuntsSession", backref="user", lazy="dynamic")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"


# ─── Running ─────────────────────────────────────────────────────────────────

class RunActivity(db.Model):
    __tablename__ = "run_activities"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    strava_activity_id = db.Column(db.BigInteger, unique=True)
    name = db.Column(db.String(256))
    sport_type = db.Column(db.String(32))   # Run, Walk
    distance = db.Column(db.Float)          # meters
    moving_time = db.Column(db.Integer)     # seconds
    elapsed_time = db.Column(db.Integer)    # seconds
    total_elevation_gain = db.Column(db.Float)
    average_speed = db.Column(db.Float)     # m/s
    max_speed = db.Column(db.Float)
    average_heartrate = db.Column(db.Float)
    max_heartrate = db.Column(db.Float)
    start_date = db.Column(db.DateTime)
    map_polyline = db.Column(db.Text)
    kudos_count = db.Column(db.Integer, default=0)
    raw_data = db.Column(db.JSON)
    synced_at = db.Column(db.DateTime, default=datetime.utcnow)

    def pace_per_km(self):
        """Returns pace in seconds per km"""
        if self.distance and self.moving_time:
            return (self.moving_time / self.distance) * 1000
        return None

    def __repr__(self):
        return f"<RunActivity {self.strava_activity_id}>"


class RunEvent(db.Model):
    __tablename__ = "run_events"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    target_distance = db.Column(db.Float)   # optional target in meters
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    memberships = db.relationship("EventMembership", backref="event", lazy="dynamic")

    def __repr__(self):
        return f"<RunEvent {self.name}>"


class EventMembership(db.Model):
    __tablename__ = "event_memberships"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("run_events.id"), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint("user_id", "event_id"),)


# ─── Chess ───────────────────────────────────────────────────────────────────

class ChessGame(db.Model):
    __tablename__ = "chess_games"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    platform = db.Column(db.String(16))             # chessdotcom | lichess
    game_id = db.Column(db.String(128), unique=True)
    time_control = db.Column(db.String(16))         # bullet | blitz | rapid | classical
    time_control_seconds = db.Column(db.Integer)
    increment = db.Column(db.Integer, default=0)
    color = db.Column(db.String(8))                 # white | black
    opponent_username = db.Column(db.String(64))
    opponent_rating = db.Column(db.Integer)
    user_rating = db.Column(db.Integer)
    result = db.Column(db.String(8))                # win | loss | draw
    termination = db.Column(db.String(32))          # checkmate, resignation, timeout...
    pgn = db.Column(db.Text)
    played_at = db.Column(db.DateTime)
    synced_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ChessGame {self.game_id}>"


# ─── ChessgRunts ──────────────────────────────────────────────────────────────

class ChessgRuntsEvent(db.Model):
    __tablename__ = "chessgrunts_events"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    run_distance = db.Column(db.Float, default=400)  # meters per interval
    chess_time_control = db.Column(db.String(16), default="bullet")  # bullet|blitz|rapid
    intervals = db.Column(db.Integer, default=4)     # how many run+chess rounds
    scheduled_at = db.Column(db.DateTime)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    sessions = db.relationship("ChessgRuntsSession", backref="event", lazy="dynamic")


class ChessgRuntsSession(db.Model):
    __tablename__ = "chessgrunts_sessions"
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("chessgrunts_events.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    total_run_distance = db.Column(db.Float, default=0)
    total_run_time = db.Column(db.Integer, default=0)   # seconds
    chess_wins = db.Column(db.Integer, default=0)
    chess_losses = db.Column(db.Integer, default=0)
    chess_draws = db.Column(db.Integer, default=0)
    combined_score = db.Column(db.Float, default=0)
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def calculate_score(self):
        """Score = chess_points * 10 + (1/avg_pace_km * 1000)"""
        chess_points = self.chess_wins * 1 + self.chess_draws * 0.5
        pace = self.total_run_time / (self.total_run_distance / 1000) if self.total_run_distance else 999
        run_score = max(0, 600 - pace) / 10  # reward faster pace
        self.combined_score = round(chess_points * 10 + run_score, 2)
        return self.combined_score
