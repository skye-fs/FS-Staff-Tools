import requests
import time
import os
from dotenv import load_dotenv

load_dotenv()

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
