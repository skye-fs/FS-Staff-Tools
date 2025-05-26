import requests
import time
import os
from dotenv import load_dotenv

ENV_FILE = ".env"

def update_env(key, value):
    lines = []
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, "r") as f:
            lines = f.readlines()
    kv = {line.split("=")[0]: line.strip().split("=", 1)[1] for line in lines if "=" in line}
    kv[key] = value
    with open(ENV_FILE, "w") as f:
        for k, v in kv.items():
            f.write(f"{k}={v}\n")

def prompt_for_tokens():
    csrf = input("CSRF token: ").strip()
    session_id = input("Session ID: ").strip()

    cookie = f"felsong_session={session_id}; csrf_cookie_name={csrf}"

    update_env("FELSONG_COOKIE", cookie)
    update_env("FELSONG_CSRF", csrf)

    # Reload .env
    load_dotenv(override=True)

prompt_for_tokens()

BASE_URL = "https://felsong.gg/en/community"
SEARCH_URL = f"{BASE_URL}/armory_research_characters"
REALM_ID = "15"

FELSONG_COOKIE = os.getenv("FELSONG_COOKIE")
FELSONG_CSRF = os.getenv("FELSONG_CSRF")

def search_character(name):
    with requests.Session() as session:
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"{BASE_URL}/research",
            "User-Agent": "Mozilla/5.0",
            "Cookie": FELSONG_COOKIE
        }

        payload = {
            "csrf_test_name": FELSONG_CSRF,
            "search_type": "1",
            "search_text": name,
            "search_realm": REALM_ID,
            "draw": "1",
            "start": "0",
            "length": "15",
        }

        resp = session.post(SEARCH_URL, data=payload, headers=headers)

        try:
            data = resp.json()
        except Exception as e:
            print(f"Failed to parse JSON: {e}")
            print("Response text:", resp.text[:500])
            return None

        for char in data.get("aaData", []):
            if char[0].lower() == name.lower():
                return {
                    "name": char[0],
                    "level": char[1],
                    "race_img": char[2],
                    "class_img": char[3],
                    "faction": char[4],
                    "guild": char[5],
                    "armory_id": char[6],
                }
        return None

if __name__ == "__main__":
    target = "Skye"
    while True:
        result = search_character(target)
        if result:
            print("Found:", result)
            print(f"Armory link: https://felsong.gg/en/community/armory/{result['armory_id']}")
        else:
            print("Character not found")
        time.sleep(1)
