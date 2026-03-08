from flask import Blueprint, redirect, request, url_for
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import requests
from strava.models import db, User

#all routes related variable are specified here, ideally each (auth, strava, dashboard) should represent subpackages. but at least temporarily they are put here together

auth = Blueprint("auth", __name__)

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