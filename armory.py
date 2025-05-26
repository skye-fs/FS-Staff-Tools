import discord
from discord import app_commands
import requests

BASE_URL = "https://felsong.gg/en/community"
SEARCH_URL = f"{BASE_URL}/armory_research_characters"
REALM_ID = "15"

def search_character(name, cookie, csrf_token):
    with requests.Session() as session:
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"{BASE_URL}/research",
            "User-Agent": "Mozilla/5.0",
            "Cookie": cookie
        }

        payload = {
            "csrf_test_name": csrf_token,
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
        except Exception:
            return "expired"

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

@app_commands.command(name="armory", description="Search for a character on the armory.")
@app_commands.describe(
    character="Name of the character to search",
    felsong_session="felsong_session token",
    csrf_token="csrf_token value"
)
async def armory(
    interaction: discord.Interaction,
    character: str,
    felsong_session: str,
    csrf_token: str
):
    await interaction.response.defer(thinking=True)

    cookie = f"felsong_session={felsong_session}; csrf_cookie_name={csrf_token}"
    result = search_character(character, cookie, csrf_token)

    if result == "expired":
        await interaction.followup.send("Tokens expired or invalid.")
    elif result:
        msg = (
            f"**Found:** {result['name']}\n"
            f"**Level:** {result['level']}\n"
            f"**Guild:** {result['guild']}\n"
            f"**Armory link:** https://felsong.gg/en/community/armory/{result['armory_id']}"
        )
        await interaction.followup.send(msg)
    else:
        await interaction.followup.send("❌ Character not found.")
