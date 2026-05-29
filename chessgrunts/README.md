# ChessgRunts ⚡

> **Sprint. Play. Repeat.** — A sport tracking web app combining running (via Strava) and chess (Chess.com / Lichess) into one competitive platform.

---

## Features

### 🏃 Running
- OAuth login with Strava (no password needed for Strava users)
- Auto-sync every hour for Run and Walk activities
- Multiple leaderboard events with distance tracking and progress bars
- Per-activity stats: distance, pace, elevation, heart rate

### ♟ Chess
- Import game history from **Chess.com** (public API) and **Lichess**
- Separate leaderboards for **Bullet / Blitz / Rapid / Classical**
- Win rate, peak rating, recent game history

### ⚡ ChessgRunts
- Combined sport: interval run + chess game, repeated
- Default format: **400m × 4 intervals** with **bullet chess**
- Customizable events (distance, time control, interval count)
- Combined score formula: `chess_points × 10 + run_speed_bonus`
- Global leaderboard across all events

---

## Setup

### 1. Clone & install

```bash
git clone <repo>
cd chessgrunts #this is updated one
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your keys
```

#### Strava API Setup
1. Go to https://www.strava.com/settings/api
2. Create an application
3. Set **Authorization Callback Domain** to `localhost`
4. Copy **Client ID** and **Client Secret** to `.env`
5. Set `STRAVA_REDIRECT_URI=http://localhost:5000/auth/strava/callback`

#### Chess.com
No setup needed — Chess.com's API is public.

#### Lichess (optional)
For higher rate limits, get a token at https://lichess.org/account/oauth/token

### 3. Initialize database

```bash
flask db init
flask db migrate -m "initial"
flask db upgrade
```

Or for quick start without migrations:
```bash
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
```

### 4. Run

```bash
python app.py
```

Open http://localhost:5000

---

## Architecture

```
chessgrunts/
├── app.py              # Flask factory, APScheduler setup
├── config.py           # Configuration (env-based)
├── models.py           # SQLAlchemy models
├── routes/
│   ├── auth.py         # Login, register, Strava OAuth
│   ├── main.py         # Index, profile
│   ├── running.py      # Activities, events, leaderboards
│   ├── chess.py        # Games, stats, leaderboards
│   └── chessgrunts.py   # Combined events & sessions
├── services/
│   ├── strava_service.py   # OAuth + activity sync
│   └── chess_service.py    # Chess.com + Lichess sync
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── profile.html
│   ├── auth/
│   ├── running/
│   ├── chess/
│   └── chessgrunts/
└── static/
    ├── css/main.css
    └── js/main.js
```

---

## Production Deployment

```bash
# With gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app()"
```

Use PostgreSQL in production by setting `DATABASE_URL=postgresql://...`

Update `STRAVA_REDIRECT_URI` to your production domain.

---

## Scoring Formula

**ChessRunt Combined Score:**
```
chess_points = wins × 1.0 + draws × 0.5
run_score    = max(0, 600 - pace_sec_per_km) / 10
total_score  = chess_points × 10 + run_score
```

A 4-interval session with 4 chess wins at 5:00/km pace scores approximately:
`4 × 10 + (600-300)/10 = 40 + 30 = 70 pts`
