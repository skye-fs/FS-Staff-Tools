import requests
import time
import os
from dotenv import load_dotenv

ENV_FILE = ".env"

# Ask for session and CSRF token, and update .env
def update_tokens():
    session_id = input("Session ID: ").strip()
    csrf_token = input("csrf_token: ").strip()

    cookie = f"felsong_session={session_id}; csrf_cookie_name={csrf_token}"

    with open(ENV_FILE, "w") as f:
        f.write(f"FELSONG_COOKIE={cookie}\n")
        f.write(f"FELSONG_CSRF={csrf_token}\n")

    load_dotenv(override=True)

update_tokens()

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
            if "<!DOCTYPE html>" in resp.text:
                print("Session expired or tokens are invalid. Stopping.")
                return "expired"
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
        if result == "expired":
            break
        if result:
            print("Found:", result)
            print(f"Armory link: https://felsong.gg/en/community/armory/{result['armory_id']}")
        else:
            print("Character not found")
        time.sleep(1)
