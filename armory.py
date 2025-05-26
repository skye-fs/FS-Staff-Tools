import discord
from discord import app_commands
from dotenv import load_dotenv
import os
import requests
from bs4 import BeautifulSoup
import html
import asyncio
from playwright.async_api import async_playwright
import httpx

load_dotenv()

BASE_URL = "https://felsong.gg/en/community"
LOGIN_URL = "https://felsong.gg/en/welcome/login"
SEARCH_URL = f"{BASE_URL}/armory_research_characters"
REALM_ID = "15"

FELSONG_SESSION = os.getenv("FELSONG_SESSION")
CSRF_TOKEN = os.getenv("CSRF_TOKEN")
FELSONG_USERNAME = os.getenv("FELSONG_USERNAME")
FELSONG_PASSWORD = os.getenv("FELSONG_PASSWORD")
TWO_CAPTCHA_API_KEY = os.getenv("TWO_CAPTCHA_API_KEY")
SITE_KEY = "6LdcE7gUAAAAAICvGm0wDYOcin727TlFCA0HqRcU"
PAGE_URL = LOGIN_URL
ENV_PATH = ".env"

def update_env_file(session_value, csrf_value, env_path=ENV_PATH):
    lines = []
    try:
        with open(env_path, "r") as f:
            lines = f.readlines()
    except FileNotFoundError:
        pass

    session_set = False
    csrf_set = False
    for i, line in enumerate(lines):
        if line.startswith("FELSONG_SESSION="):
            lines[i] = f"FELSONG_SESSION={session_value}\n"
            session_set = True
        elif line.startswith("CSRF_TOKEN="):
            lines[i] = f"CSRF_TOKEN={csrf_value}\n"
            csrf_set = True

    if not session_set:
        lines.append(f"FELSONG_SESSION={session_value}\n")
    if not csrf_set:
        lines.append(f"CSRF_TOKEN={csrf_value}\n")

    with open(env_path, "w") as f:
        f.writelines(lines)

async def solve_recaptcha():
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "http://2captcha.com/in.php",
            data={
                "key": TWO_CAPTCHA_API_KEY,
                "method": "userrecaptcha",
                "googlekey": SITE_KEY,
                "pageurl": PAGE_URL,
                "json": 1
            }
        )
        json_resp = resp.json()
        request_id = json_resp.get("request")
        if not request_id or json_resp.get("status") != 1:
            raise Exception(f"2Captcha submit error: {json_resp}")

        fetch_url = f"http://2captcha.com/res.php?key={TWO_CAPTCHA_API_KEY}&action=get&id={request_id}&json=1"
        for _ in range(24):
            await asyncio.sleep(5)
            res = await client.get(fetch_url)
            res_json = res.json()
            if res_json.get("status") == 1:
                return res_json.get("request")
            elif res_json.get("request") == "CAPCHA_NOT_READY":
                continue
            else:
                raise Exception(f"2Captcha error: {res_json.get('request')}")
        raise Exception("2Captcha solving timed out")

# ONLY NEED TO BE DONE ONCE
async def login_and_fetch_cookies():
    global FELSONG_SESSION, CSRF_TOKEN
    print("[DEBUG] Starting Playwright to fetch fresh cookies.")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # presentation page
        await page.goto("https://felsong.gg/en/presentation", wait_until="domcontentloaded")
        await page.click("i.fa-solid.fa-angles-right")

        # redirect
        await page.wait_for_url("https://felsong.gg/en/", timeout=5000)

        # login
        await page.click('#form-register-light a[href$="/welcome/login"]')

        # redirect
        await page.wait_for_url("**/welcome/login", timeout=5000)

        # credentials
        await page.fill('form#login-form input[name="username"]', FELSONG_USERNAME)
        await page.fill('form#login-form input[name="password"]', FELSONG_PASSWORD)

        # solve captcha
        print("[DEBUG] Solving captcha, this may take some time.")
        token = await solve_recaptcha()

        await page.evaluate(f'''
            () => {{
                const textarea = document.querySelector('textarea[name="g-recaptcha-response"]');
                textarea.style.display = 'block';
                textarea.value = "{token}";
                textarea.dispatchEvent(new Event('input', {{ bubbles: true }}));
                textarea.dispatchEvent(new Event('change', {{ bubbles: true }}));
            }}
        ''')

        # login
        await page.click('form#login-form button.btn.btn-primary')

        # redirect
        await asyncio.sleep(5)

        # initialize session
        await page.goto("https://felsong.gg/en/community/research", wait_until="networkidle")
        await asyncio.sleep(2)

        # extract cookies
        cookies = await context.cookies()
        felsong_session = None
        csrf_cookie_name = None
        for c in cookies:
            if c["name"] == "felsong_session":
                felsong_session = c["value"]
            elif c["name"] == "csrf_cookie_name":
                csrf_cookie_name = c["value"]

        await browser.close()

        if not felsong_session or not csrf_cookie_name:
            print("[ERROR] Could not find required cookies!")
            return False

        FELSONG_SESSION = felsong_session
        CSRF_TOKEN = csrf_cookie_name

        print("[DEBUG] New session cookie:", FELSONG_SESSION)
        print("[DEBUG] New CSRF token:", CSRF_TOKEN)

        update_env_file(FELSONG_SESSION, CSRF_TOKEN)
        print("[DEBUG] .env file updated with new tokens.")

        return True

def extract_guild_info(guild_html):
    soup = BeautifulSoup(guild_html, 'html.parser')
    text = soup.get_text()
    return html.unescape(text).strip()

async def search_character(name):
    global FELSONG_SESSION, CSRF_TOKEN

    if not FELSONG_SESSION or not CSRF_TOKEN:
        refreshed = await login_and_fetch_cookies()
        if not refreshed:
            return "expired"

    cookie = f"felsong_session={FELSONG_SESSION}; csrf_cookie_name={CSRF_TOKEN}"
    print("[DEBUG] Using session cookie:", FELSONG_SESSION)
    print("[DEBUG] Using CSRF token:", CSRF_TOKEN)
    print("[DEBUG] Full cookie header:", cookie)

    with requests.Session() as session:
        headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"{BASE_URL}/research",
            "Origin": "https://felsong.gg",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
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

        print("[DEBUG] Sending POST request to:", SEARCH_URL)
        resp = session.post(SEARCH_URL, data=payload, headers=headers)

        print("[DEBUG] Status code:", resp.status_code)
        print("[DEBUG] Content-Type:", resp.headers.get("Content-Type", ""))
        if resp.history:
            print("[DEBUG] Redirect history:", resp.history)

        try:
            data = resp.json()
        except Exception:
            print("[ERROR] Failed to parse JSON. Likely received HTML instead.")
            print(resp.text[:1000])
            if "login" in resp.text.lower():
                print("❗Likely redirected to login page.")
            elif "create an account" in resp.text.lower():
                print("❗Likely redirected to account creation.")
            refreshed = await login_and_fetch_cookies()
            if refreshed:
                return await search_character(name)
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
@app_commands.describe(character="Name of the character to search")
async def armory(interaction: discord.Interaction, character: str):
    await interaction.response.defer(thinking=True)
    result = await search_character(character)
    if result == "expired":
        await interaction.followup.send("❗ Tokens expired or invalid. Please run the login command again.")
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
