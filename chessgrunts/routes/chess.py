from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from models import ChessGame, User
from services.chess_service import sync_user_chess
from sqlalchemy import func

chess_bp = Blueprint("chess", __name__)

TIME_CONTROLS = ["bullet", "blitz", "rapid", "classical"]


@chess_bp.route("/")
@login_required
def dashboard():
    tc = request.args.get("tc", "blitz")
    if tc not in TIME_CONTROLS:
        tc = "blitz"

    games = ChessGame.query.filter_by(user_id=current_user.id, time_control=tc)\
        .order_by(ChessGame.played_at.desc()).limit(20).all()

    stats = _compute_stats(current_user.id, tc)
    return render_template("chess/dashboard.html",
                           games=games, stats=stats, tc=tc, time_controls=TIME_CONTROLS)


@chess_bp.route("/sync")
@login_required
def manual_sync():
    if not current_user.chessdotcom_username and not current_user.lichess_username:
        flash("Add your Chess.com or Lichess username in your profile first.", "warning")
        return redirect(url_for("main.profile"))
    count = sync_user_chess(current_app, current_user)
    flash(f"Synced {count} new chess games.", "success")
    return redirect(url_for("chess.dashboard"))


@chess_bp.route("/leaderboard")
@login_required
def leaderboard():
    tc = request.args.get("tc", "blitz")
    if tc not in TIME_CONTROLS:
        tc = "blitz"

    # Get all users with chess games of this time control
    user_ids = db.session.query(ChessGame.user_id)\
        .filter(ChessGame.time_control == tc).distinct().all()
    user_ids = [u[0] for u in user_ids]

    board = []
    for uid in user_ids:
        user = User.query.get(uid)
        stats = _compute_stats(uid, tc)
        if stats["total"] > 0:
            board.append({"user": user, **stats})

    board.sort(key=lambda x: (x["wins"] / x["total"] if x["total"] else 0), reverse=True)
    return render_template("chess/leaderboard.html", board=board, tc=tc, time_controls=TIME_CONTROLS)


def _compute_stats(user_id, tc):
    games = ChessGame.query.filter_by(user_id=user_id, time_control=tc).all()
    wins = sum(1 for g in games if g.result == "win")
    losses = sum(1 for g in games if g.result == "loss")
    draws = sum(1 for g in games if g.result == "draw")
    total = len(games)
    ratings = [g.user_rating for g in games if g.user_rating]
    latest_rating = ratings[-1] if ratings else None
    peak_rating = max(ratings) if ratings else None
    return {
        "wins": wins,
        "losses": losses,
        "draws": draws,
        "total": total,
        "win_rate": round(wins / total * 100, 1) if total else 0,
        "latest_rating": latest_rating,
        "peak_rating": peak_rating,
    }


@chess_bp.route("/api/games")
@login_required
def api_games():
    tc = request.args.get("tc", "blitz")
    page = request.args.get("page", 1, type=int)
    games = ChessGame.query.filter_by(user_id=current_user.id, time_control=tc)\
        .order_by(ChessGame.played_at.desc()).paginate(page=page, per_page=20)
    return jsonify({
        "games": [{
            "id": g.id,
            "platform": g.platform,
            "time_control": g.time_control,
            "color": g.color,
            "result": g.result,
            "opponent": g.opponent_username,
            "user_rating": g.user_rating,
            "played_at": g.played_at.isoformat() if g.played_at else None,
        } for g in games.items],
        "has_next": games.has_next,
    })
