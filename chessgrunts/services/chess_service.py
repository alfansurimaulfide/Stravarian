import requests
from datetime import datetime, timezone


CHESSDOTCOM_BASE = "https://api.chess.com/pub"
LICHESS_BASE = "https://lichess.org/api"

TIME_CONTROL_MAP = {
    "bullet": (0, 179),
    "blitz": (180, 599),
    "rapid": (600, 1799),
    "classical": (1800, 99999),
}


def classify_time_control(seconds, increment=0):
    effective = seconds + increment * 40  # FIDE formula approximation
    for name, (lo, hi) in TIME_CONTROL_MAP.items():
        if lo <= effective <= hi:
            return name
    return "classical"


# ─── Chess.com ───────────────────────────────────────────────────────────────

def fetch_chessdotcom_archives(username):
    resp = requests.get(f"{CHESSDOTCOM_BASE}/player/{username}/games/archives",
                        headers={"User-Agent": "ChessgRunts/1.0"})
    if resp.status_code != 200:
        return []
    return resp.json().get("archives", [])


def fetch_chessdotcom_games(archive_url):
    resp = requests.get(archive_url, headers={"User-Agent": "ChessgRunts/1.0"})
    if resp.status_code != 200:
        return []
    return resp.json().get("games", [])


def parse_chessdotcom_game(game, username, user_id):
    from models import ChessGame
    white = game.get("white", {})
    black = game.get("black", {})
    is_white = white.get("username", "").lower() == username.lower()

    color = "white" if is_white else "black"
    my_info = white if is_white else black
    opp_info = black if is_white else white

    result_str = my_info.get("result", "")
    if result_str == "win":
        result = "win"
    elif result_str in ("checkmated", "timeout", "resigned", "abandoned", "lose"):
        result = "loss"
    else:
        result = "draw"

    tc = game.get("time_control", "")
    try:
        if "+" in tc:
            base, inc = tc.split("+")
            seconds, increment = int(base), int(inc)
        else:
            seconds, increment = int(tc), 0
    except Exception:
        seconds, increment = 600, 0

    end_time = game.get("end_time")
    played_at = datetime.fromtimestamp(end_time, tz=timezone.utc) if end_time else None

    return ChessGame(
        user_id=user_id,
        platform="chessdotcom",
        game_id=f"cdc_{game.get('uuid', game.get('url', ''))}",
        time_control=classify_time_control(seconds, increment),
        time_control_seconds=seconds,
        increment=increment,
        color=color,
        opponent_username=opp_info.get("username"),
        opponent_rating=opp_info.get("rating"),
        user_rating=my_info.get("rating"),
        result=result,
        termination=my_info.get("result"),
        pgn=game.get("pgn"),
        played_at=played_at,
    )


# ─── Lichess ─────────────────────────────────────────────────────────────────

def fetch_lichess_games(username, max_games=100, token=None):
    headers = {"Accept": "application/x-ndjson"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    params = {"max": max_games, "perfType": "bullet,blitz,rapid,classical", "color": ""}
    resp = requests.get(f"{LICHESS_BASE}/games/user/{username}",
                        headers=headers, params=params, stream=True)
    if resp.status_code != 200:
        return []
    games = []
    for line in resp.iter_lines():
        if line:
            import json
            try:
                games.append(json.loads(line))
            except Exception:
                pass
    return games


def parse_lichess_game(game, username, user_id):
    from models import ChessGame
    players = game.get("players", {})
    white_p = players.get("white", {})
    black_p = players.get("black", {})

    is_white = white_p.get("user", {}).get("name", "").lower() == username.lower()
    color = "white" if is_white else "black"
    my_info = white_p if is_white else black_p
    opp_info = black_p if is_white else white_p

    winner = game.get("winner")
    if winner == color:
        result = "win"
    elif winner and winner != color:
        result = "loss"
    else:
        result = "draw"

    clock = game.get("clock", {})
    seconds = clock.get("initial", 600) // 100 if "initial" in clock else 600
    increment = clock.get("increment", 0) // 100 if "increment" in clock else 0

    speed = game.get("speed", "rapid")
    tc_map = {"bullet": "bullet", "blitz": "blitz", "rapid": "rapid",
              "classical": "classical", "correspondence": "classical"}
    time_control = tc_map.get(speed, "rapid")

    created_at = game.get("createdAt")
    played_at = datetime.fromtimestamp(created_at / 1000, tz=timezone.utc) if created_at else None

    return ChessGame(
        user_id=user_id,
        platform="lichess",
        game_id=f"li_{game.get('id')}",
        time_control=time_control,
        time_control_seconds=seconds,
        increment=increment,
        color=color,
        opponent_username=opp_info.get("user", {}).get("name"),
        opponent_rating=opp_info.get("rating"),
        user_rating=my_info.get("rating"),
        result=result,
        termination=game.get("status"),
        pgn=game.get("pgn"),
        played_at=played_at,
    )


# ─── Sync helpers ─────────────────────────────────────────────────────────────

def sync_user_chess(app, user):
    from app import db
    from models import ChessGame
    count = 0

    if user.chessdotcom_username:
        try:
            archives = fetch_chessdotcom_archives(user.chessdotcom_username)
            # Last 2 months only for regular sync
            for archive_url in archives[-2:]:
                games = fetch_chessdotcom_games(archive_url)
                for g in games:
                    gid = f"cdc_{g.get('uuid', g.get('url', ''))}"
                    if ChessGame.query.filter_by(game_id=gid).first():
                        continue
                    cg = parse_chessdotcom_game(g, user.chessdotcom_username, user.id)
                    db.session.add(cg)
                    count += 1
        except Exception as e:
            print(f"[Chess.com] Error for {user.chessdotcom_username}: {e}")

    if user.lichess_username:
        try:
            token = app.config.get("LICHESS_TOKEN")
            games = fetch_lichess_games(user.lichess_username, max_games=50, token=token)
            for g in games:
                gid = f"li_{g.get('id')}"
                if ChessGame.query.filter_by(game_id=gid).first():
                    continue
                cg = parse_lichess_game(g, user.lichess_username, user.id)
                db.session.add(cg)
                count += 1
        except Exception as e:
            print(f"[Lichess] Error for {user.lichess_username}: {e}")

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()

    return count


def sync_all_chess(app):
    with app.app_context():
        from models import User
        users = User.query.filter(
            (User.chessdotcom_username.isnot(None)) |
            (User.lichess_username.isnot(None))
        ).all()
        for user in users:
            sync_user_chess(app, user)
