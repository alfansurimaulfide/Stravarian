from flask import Blueprint, redirect, request, url_for
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import requests
from strava.models import db, User

#all routes related variable are specified here, ideally each (auth, strava, dashboard) should represent subpackages. but at least temporarily they are put here together

dashboard = Blueprint("dashboard", __name__)

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

@dashboard.route("/")
def home():
    return