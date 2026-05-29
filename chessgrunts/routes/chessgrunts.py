from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from models import ChessgRuntsEvent, ChessgRuntsSession, User

chessgrunts_bp = Blueprint("chessgrunts", __name__)


@chessgrunts_bp.route("/")
@login_required
def dashboard():
    upcoming = ChessgRuntsEvent.query.filter(
        ChessgRuntsEvent.is_active == True,
        ChessgRuntsEvent.scheduled_at >= datetime.utcnow()
    ).order_by(ChessgRuntsEvent.scheduled_at).limit(5).all()

    past_sessions = ChessgRuntsSession.query.filter_by(user_id=current_user.id)\
        .order_by(ChessgRuntsSession.created_at.desc()).limit(5).all()

    return render_template("running/dashboard.html",
                           upcoming=upcoming, past_sessions=past_sessions)


@chessgrunts_bp.route("/events")
@login_required
def events():
    all_events = ChessgRuntsEvent.query.order_by(ChessgRuntsEvent.scheduled_at.desc()).all()
    return render_template("chessgrunts/events.html", events=all_events)


@chessgrunts_bp.route("/events/create", methods=["GET", "POST"])
@login_required
def create_event():
    if request.method == "POST":
        scheduled_str = request.form.get("scheduled_at")
        event = ChessgRuntsEvent(
            name=request.form.get("name"),
            description=request.form.get("description"),
            run_distance=float(request.form.get("run_distance", 400)),
            chess_time_control=request.form.get("chess_time_control", "bullet"),
            intervals=int(request.form.get("intervals", 4)),
            scheduled_at=datetime.fromisoformat(scheduled_str) if scheduled_str else None,
            created_by=current_user.id,
        )
        db.session.add(event)
        db.session.commit()
        flash("ChessgRunts event created!", "success")
        return redirect(url_for("chessgrunts.events"))
    return render_template("chessgrunts/create_event.html")


@chessgrunts_bp.route("/events/<int:event_id>")
@login_required
def event_detail(event_id):
    event = ChessgRuntsEvent.query.get_or_404(event_id)
    sessions = ChessgRuntsSession.query.filter_by(event_id=event_id)\
        .order_by(ChessgRuntsSession.combined_score.desc()).all()
    board = []
    for s in sessions:
        user = User.query.get(s.user_id)
        board.append({"session": s, "user": user})
    my_session = ChessgRuntsSession.query.filter_by(
        event_id=event_id, user_id=current_user.id).first()
    return render_template("chessgrunts/event_detail.html",
                           event=event, board=board, my_session=my_session)


@chessgrunts_bp.route("/events/<int:event_id>/log", methods=["POST"])
@login_required
def log_session(event_id):
    event = ChessgRuntsEvent.query.get_or_404(event_id)
    session = ChessgRuntsSession.query.filter_by(
        event_id=event_id, user_id=current_user.id).first()
    if not session:
        session = ChessgRuntsSession(event_id=event_id, user_id=current_user.id)
        db.session.add(session)

    session.total_run_distance = float(request.form.get("total_run_distance", 0))
    session.total_run_time = int(request.form.get("total_run_time", 0))
    session.chess_wins = int(request.form.get("chess_wins", 0))
    session.chess_losses = int(request.form.get("chess_losses", 0))
    session.chess_draws = int(request.form.get("chess_draws", 0))
    session.completed_at = datetime.utcnow()
    session.calculate_score()
    db.session.commit()
    flash("Session logged!", "success")
    return redirect(url_for("chessgrunts.event_detail", event_id=event_id))


@chessgrunts_bp.route("/leaderboard")
@login_required
def global_leaderboard():
    sessions = ChessgRuntsSession.query\
        .order_by(ChessgRuntsSession.combined_score.desc()).limit(50).all()
    board = [{"session": s, "user": User.query.get(s.user_id)} for s in sessions]
    return render_template("chessgrunts/leaderboard.html", board=board)
