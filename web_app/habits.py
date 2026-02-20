import json
from datetime import date, datetime
from pathlib import Path

DATA_FILE = Path(__file__).parent / "data.json"
FIRE = "🔥"
ICE = "🧊"


def _default_data():
    return {
        "user": None,
        "last_check_in_date": None,
        "habits": {}
    }


def load_data():
    """Load data only from web_app/data.json."""
    try:
        with DATA_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = _default_data()

    if not isinstance(data, dict):
        return _default_data()

    data.setdefault("user", None)
    data.setdefault("last_check_in_date", None)
    data.setdefault("habits", {})

    if not isinstance(data["habits"], dict):
        data["habits"] = {}
    else:
        for habit in data["habits"].values():
            if isinstance(habit, dict):
                habit.setdefault("is_main", False)

    return data


def save_data(data):
    """Persist habits data only to web_app/data.json."""
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with DATA_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def set_user(data, name):
    clean = (name or "").strip()
    if not clean:
        return False, "Name cannot be empty."

    data["user"] = clean
    save_data(data)
    return True, f"Welcome, {clean}."


def add_habit(data, name):
    clean = (name or "").strip().lower()
    if not clean:
        return False, "Habit name cannot be empty."

    if clean in data["habits"]:
        return False, "Habit already exists."

    today = date.today().isoformat()
    data["habits"][clean] = {
        "creation_date": today,
        "last_check_in_date": None,
        "history": [],
        "streak": 0,
        "is_main": False,
    }
    save_data(data)
    return True, f"Habit '{clean}' added."


def delete_habit(data, name):
    if name not in data["habits"]:
        return False, "Habit not found."

    del data["habits"][name]
    save_data(data)
    return True, f"Habit '{name}' deleted."

def select_main_habit(data, habit_name):
    if habit_name not in data["habits"]:
        return False, "Habit not found."

    for name, habit in data["habits"].items():
        habit["is_main"] = name == habit_name

    save_data(data)
    return True, f"Habit '{habit_name}' is now main."


def deselect_main_habit(data, habit_name):
    if habit_name not in data["habits"]:
        return False, "Habit not found."

    data["habits"][habit_name]["is_main"] = False
    save_data(data)
    return True, f"Habit '{habit_name}' is no longer main."


def toggle_main_habit(data, habit_name):
    if habit_name not in data["habits"]:
        return False, "Habit not found."

    if data["habits"][habit_name].get("is_main", False):
        return deselect_main_habit(data, habit_name)
    return select_main_habit(data, habit_name)


def fill_missed_days(habit):
    """Fill skipped days between last check-in and today with ICE markers."""
    last = date.fromisoformat(habit["last_check_in_date"])
    today = date.today()
    missed = (today - last).days - 1

    if missed > 0:
        habit["history"].extend([ICE] * missed)


def break_streak(habit):
    """Reset streak if the most recent day in history is a miss."""
    if habit["last_check_in_date"] is None:
        return

    if habit["history"] and habit["history"][-1] == ICE:
        habit["streak"] = 0


def check_in(data, habit_name):
    if habit_name not in data["habits"]:
        return False, "Habit not found."

    today = date.today().isoformat()
    habit = data["habits"][habit_name]

    if habit["last_check_in_date"] == today:
        return False, "Already checked in today."

    if habit["last_check_in_date"] is None:
        habit["last_check_in_date"] = today
        habit["history"].append(FIRE)
        habit["streak"] += 1
    else:
        fill_missed_days(habit)
        break_streak(habit)
        habit["history"].append(FIRE)
        habit["streak"] += 1
        habit["last_check_in_date"] = today

    data["last_check_in_date"] = today
    save_data(data)
    return True, f"Checked in '{habit_name}'."


def _format_date(value):
    if not value:
        return "-"
    return datetime.fromisoformat(value).strftime("%d %b")


def get_habit_rows(data):
    rows = []
    for name, habit in data["habits"].items():
        rows.append(
            {
                "name": name,
                "name_title": name.title(),
                "is_main": habit.get("is_main", False),
                "created": _format_date(habit.get("creation_date")),
                "last_check": _format_date(habit.get("last_check_in_date")),
                "streak": habit.get("streak", 0),
                "history": "".join(habit.get("history", [])[-7:]),
            }
        )
    return rows
