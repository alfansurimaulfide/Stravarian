from flask import Blueprint, redirect, request, url_for
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import requests
from strava.models import db, User

#all routes related variable are specified here, ideally each (auth, strava, dashboard) should represent subpackages. but at least temporarily they are put here together

auth = Blueprint("auth", __name__)
strava = Blueprint("strava", __name__)
dashboard = Blueprint("dashboard", __name__)

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

@auth.route("strava/connect")
def auth():
    url = (
        "https://www.strava.com/oauth/authorize"
        f"?client_id={CLIENT_ID}"
        "&response_type=code"
        f"&redirect_uri={REDIRECT_URI}"
        "&approval_prompt=auto"
        "&scope=activity:read_all"
    )

    return redirect(url)

#currently only use callback mechanism, webhook (if necessary) will be explored later
@strava.route("/strava/callback")
def strava():
    code = request.args.get("code")

    response = requests.post(
        "https://www.strava.com/oauth/token",
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code"
        }
    )

    token_data = response.json()

    strava_id = token_data["athlete"]["id"]
    user = User.query.filter_by(strava_id=strava_id).first()
    if not user:
        user = User(
            strava_id=strava_id,
            username=token_data["athlete"]["username"]
        )
        db.session.add(user)

    user.strava_id = token_data["athlete"]["id"]
    user.strava_token = token_data["access_token"]
    user.refresh_token = token_data["refresh_token"]

    db.session.commit()

    return redirect(url_for("dashboard.home"))
    # return "Connected to Strava!"

def get_activities(user):

    headers = {
        "Authorization": f"Bearer {user.strava_token}"
    }

    r = requests.get(
        "https://www.strava.com/api/v3/athlete/activities",
        headers=headers
    )

    return r.json()

@dashboard.route("/dashboard/")
def dashboard():
    return