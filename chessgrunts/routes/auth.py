from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from models import User
from services.strava_service import (get_strava_auth_url, exchange_code_for_token,
                                      sync_user_strava)

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        if User.query.filter_by(username=username).first():
            flash("Username already taken.", "error")
            return redirect(url_for("auth.register"))
        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "error")
            return redirect(url_for("auth.register"))
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user, remember=True)
        flash("Welcome to ChessgRunts!", "success")
        return redirect(url_for("main.index"))
    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter(
            (User.username == identifier) | (User.email == identifier)
        ).first()
        if user and user.check_password(password):
            login_user(user, remember=True)
            next_page = request.args.get("next")
            return redirect(next_page or url_for("main.index"))
        flash("Invalid credentials.", "error")
    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.index"))


@auth_bp.route("/strava/connect")
@login_required
def strava_connect():
    auth_url = get_strava_auth_url(current_app)
    return redirect(auth_url)


@auth_bp.route("/strava/callback")
@login_required
def strava_callback():
    code = request.args.get("code")
    error = request.args.get("error")
    if error or not code:
        flash("Strava authorization failed or was denied.", "error")
        return redirect(url_for("main.profile"))
    try:
        data = exchange_code_for_token(current_app, code)
        athlete = data.get("athlete", {})
        current_user.strava_id = athlete.get("id")
        current_user.strava_access_token = data.get("access_token")
        current_user.strava_refresh_token = data.get("refresh_token")
        current_user.strava_token_expires = data.get("expires_at")
        current_user.strava_connected = True
        if athlete.get("profile_medium"):
            current_user.avatar_url = athlete.get("profile_medium")
        db.session.commit()
        # Immediate sync
        sync_user_strava(current_app, current_user)
        flash("Strava connected! Your activities have been imported.", "success")
    except Exception as e:
        flash(f"Error connecting Strava: {str(e)}", "error")
    return redirect(url_for("running.dashboard"))


@auth_bp.route("/profile/update", methods=["POST"])
@login_required
def update_profile():
    chessdotcom = request.form.get("chessdotcom_username", "").strip()
    lichess = request.form.get("lichess_username", "").strip()
    current_user.chessdotcom_username = chessdotcom or None
    current_user.lichess_username = lichess or None
    db.session.commit()
    from services.chess_service import sync_user_chess
    sync_user_chess(current_app, current_user)
    flash("Profile updated and chess games synced.", "success")
    return redirect(url_for("main.profile"))
