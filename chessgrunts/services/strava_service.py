import requests
import time
from datetime import datetime
from flask import current_app


def get_strava_auth_url(app):
    params = {
        "client_id": app.config["STRAVA_CLIENT_ID"],
        "redirect_uri": app.config["STRAVA_REDIRECT_URI"],
        "response_type": "code",
        "approval_prompt": "auto",
        "scope": "read,activity:read_all",
    }
    base = app.config["STRAVA_AUTH_URL"]
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{base}?{query}"


def exchange_code_for_token(app, code):
    resp = requests.post(app.config["STRAVA_TOKEN_URL"], data={
        "client_id": app.config["STRAVA_CLIENT_ID"],
        "client_secret": app.config["STRAVA_CLIENT_SECRET"],
        "code": code,
        "grant_type": "authorization_code",
    })
    resp.raise_for_status()
    return resp.json()


def refresh_access_token(app, user):
    resp = requests.post(app.config["STRAVA_TOKEN_URL"], data={
        "client_id": app.config["STRAVA_CLIENT_ID"],
        "client_secret": app.config["STRAVA_CLIENT_SECRET"],
        "grant_type": "refresh_token",
        "refresh_token": user.strava_refresh_token,
    })
    resp.raise_for_status()
    data = resp.json()
    user.strava_access_token = data["access_token"]
    user.strava_refresh_token = data["refresh_token"]
    user.strava_token_expires = data["expires_at"]
    return user


def get_valid_token(app, user, db):
    if user.strava_token_expires and user.strava_token_expires < int(time.time()) + 60:
        user = refresh_access_token(app, user)
        db.session.commit()
    return user.strava_access_token


def fetch_activities(app, user, db, after=None, per_page=50):
    token = get_valid_token(app, user, db)
    headers = {"Authorization": f"Bearer {token}"}
    params = {"per_page": per_page, "page": 1}
    if after:
        params["after"] = int(after.timestamp())

    base = app.config["STRAVA_API_BASE"]
    resp = requests.get(f"{base}/athlete/activities", headers=headers, params=params)
    resp.raise_for_status()
    return resp.json()


def sync_user_strava(app, user):
    """Sync run/walk activities for a single user."""
    from app import db
    from models import RunActivity

    if not user.strava_connected:
        return 0

    try:
        # Get last synced activity date
        last = RunActivity.query.filter_by(user_id=user.id)\
            .order_by(RunActivity.start_date.desc()).first()
        after = last.start_date if last else None

        activities = fetch_activities(app, user, db, after=after)
        count = 0
        for act in activities:
            if act.get("sport_type") not in ("Run", "Walk", "TrailRun"):
                continue
            existing = RunActivity.query.filter_by(strava_activity_id=act["id"]).first()
            if existing:
                continue
            ra = RunActivity(
                user_id=user.id,
                strava_activity_id=act["id"],
                name=act.get("name"),
                sport_type=act.get("sport_type"),
                distance=act.get("distance"),
                moving_time=act.get("moving_time"),
                elapsed_time=act.get("elapsed_time"),
                total_elevation_gain=act.get("total_elevation_gain"),
                average_speed=act.get("average_speed"),
                max_speed=act.get("max_speed"),
                average_heartrate=act.get("average_heartrate"),
                max_heartrate=act.get("max_heartrate"),
                start_date=datetime.strptime(act["start_date"], "%Y-%m-%dT%H:%M:%SZ")
                if act.get("start_date") else None,
                map_polyline=act.get("map", {}).get("summary_polyline"),
                kudos_count=act.get("kudos_count", 0),
                raw_data=act,
            )
            db.session.add(ra)
            count += 1
        db.session.commit()
        return count
    except Exception as e:
        print(f"[Strava] Error syncing user {user.id}: {e}")
        db.session.rollback()
        return 0


def sync_all_strava(app):
    """Called by scheduler every hour."""
    with app.app_context():
        from models import User
        from app import db
        users = User.query.filter_by(strava_connected=True).all()
        for user in users:
            sync_user_strava(app, user)
