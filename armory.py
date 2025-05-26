import discord
from discord import app_commands
from dotenv import load_dotenv
import os
import requests
import time
from bs4 import BeautifulSoup
import html

load_dotenv()

BASE_URL = "https://felsong.gg/en/community"
SEARCH_URL = f"{BASE_URL}/armory_research_characters"
REALM_ID = "15"
FELSONG_SESSION = os.getenv("FELSONG_SESSION")
CSRF_TOKEN = os.getenv("CSRF_TOKEN")

def extract_guild_info(guild_html):
    soup = BeautifulSoup(guild_html, 'html.parser')
    text = soup.get_text()
    return html.unescape(text).strip()

def search_character(name):
    cookie = f"felsong_session={FELSONG_SESSION}; csrf_cookie_name={CSRF_TOKEN}"
    with requests.Session() as session:
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"{BASE_URL}/research",
            "User-Agent": "Mozilla/5.0",
            "Cookie": cookie
        }

        payload = {
            "csrf_test_name": CSRF_TOKEN,
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
                    "guild": extract_guild_info(char[5]),
                    "armory_id": char[6],
                }
        return None

@app_commands.command(name="armory", description="Search for a character on the armory.")
@app_commands.describe(
    character="Name of the character to search"
)
async def armory(
    interaction: discord.Interaction,
    character: str
):
    await interaction.response.defer(thinking=True)
    result = search_character(character)
    if result == "expired":
        await interaction.followup.send("Tokens expired or invalid.")
    elif result:
        msg = (
            f"**Found:** {result['name']}\n"
            f"**Level:** {result['level']}\n"
            #f"**Faction:** {result['faction']}\n"
            #f"**Race:** {result['race_img']}\n"
            f"**Guild:** {result['guild']}\n"
            f"**Armory link:** https://felsong.gg/en/community/armory/{result['armory_id']}"
        )
        await interaction.followup.send(msg)
    else:
        await interaction.followup.send("❌ Character not found.")