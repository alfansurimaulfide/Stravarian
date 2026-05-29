from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from models import RunActivity, RunEvent, EventMembership, User
from services.strava_service import sync_user_strava

running_bp = Blueprint("running", __name__)


@running_bp.route("/")
@login_required
def dashboard():
    activities = RunActivity.query.filter_by(user_id=current_user.id)\
        .order_by(RunActivity.start_date.desc()).limit(10).all()
    events = RunEvent.query.filter_by(is_active=True).all()
    my_events = [m.event_id for m in EventMembership.query.filter_by(user_id=current_user.id).all()]
    return render_template("running/dashboard.html",
                           activities=activities, events=events, my_events=my_events)


@running_bp.route("/sync")
@login_required
def manual_sync():
    if not current_user.strava_connected:
        flash("Please connect your Strava account first.", "warning")
        return redirect(url_for("auth.strava_connect"))
    count = sync_user_strava(current_app, current_user)
    flash(f"Synced {count} new activities from Strava.", "success")
    return redirect(url_for("running.dashboard"))


@running_bp.route("/events")
@login_required
def events():
    all_events = RunEvent.query.order_by(RunEvent.start_date.desc()).all()
    return render_template("running/events.html", events=all_events)


@running_bp.route("/events/create", methods=["GET", "POST"])
@login_required
def create_event():
    if request.method == "POST":
        event = RunEvent(
            name=request.form.get("name"),
            description=request.form.get("description"),
            start_date=datetime.fromisoformat(request.form.get("start_date")),
            end_date=datetime.fromisoformat(request.form.get("end_date")),
            target_distance=float(request.form.get("target_distance") or 0) * 1000,
            created_by=current_user.id,
        )
        db.session.add(event)
        db.session.flush()
        # Auto-join creator
        membership = EventMembership(user_id=current_user.id, event_id=event.id)
        db.session.add(membership)
        db.session.commit()
        flash("Event created!", "success")
        return redirect(url_for("running.leaderboard", event_id=event.id))
    return render_template("running/create_event.html")


@running_bp.route("/events/<int:event_id>/join", methods=["POST"])
@login_required
def join_event(event_id):
    event = RunEvent.query.get_or_404(event_id)
    existing = EventMembership.query.filter_by(user_id=current_user.id, event_id=event_id).first()
    if not existing:
        db.session.add(EventMembership(user_id=current_user.id, event_id=event_id))
        db.session.commit()
        flash(f"Joined {event.name}!", "success")
    return redirect(url_for("running.leaderboard", event_id=event_id))


@running_bp.route("/events/<int:event_id>/leaderboard")
@login_required
def leaderboard(event_id):
    event = RunEvent.query.get_or_404(event_id)
    members = EventMembership.query.filter_by(event_id=event_id).all()
    member_ids = [m.user_id for m in members]

    board = []
    for uid in member_ids:
        user = User.query.get(uid)
        acts = RunActivity.query.filter(
            RunActivity.user_id == uid,
            RunActivity.start_date >= event.start_date,
            RunActivity.start_date <= event.end_date,
        ).all()
        total_distance = sum(a.distance or 0 for a in acts)
        total_time = sum(a.moving_time or 0 for a in acts)
        avg_pace = (total_time / (total_distance / 1000)) if total_distance else None
        board.append({
            "user": user,
            "total_distance": total_distance,
            "total_time": total_time,
            "avg_pace": avg_pace,
            "run_count": len(acts),
        })

    board.sort(key=lambda x: x["total_distance"], reverse=True)
    my_membership = EventMembership.query.filter_by(
        user_id=current_user.id, event_id=event_id).first()

    return render_template("running/leaderboard.html",
                           event=event, board=board, my_membership=my_membership)


@running_bp.route("/api/activities")
@login_required
def api_activities():
    page = request.args.get("page", 1, type=int)
    acts = RunActivity.query.filter_by(user_id=current_user.id)\
        .order_by(RunActivity.start_date.desc()).paginate(page=page, per_page=20)
    return jsonify({
        "activities": [{
            "id": a.id,
            "name": a.name,
            "sport_type": a.sport_type,
            "distance": a.distance,
            "moving_time": a.moving_time,
            "start_date": a.start_date.isoformat() if a.start_date else None,
            "average_speed": a.average_speed,
            "pace_per_km": a.pace_per_km(),
        } for a in acts.items],
        "has_next": acts.has_next,
        "page": page,
    })
