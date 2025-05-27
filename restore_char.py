import os
from dotenv import load_dotenv
from discord import app_commands
from playwright.async_api import async_playwright
import re

load_dotenv()

WOW_FREAKZ_USER = os.getenv("WOW_FREAKZ_USER")
WOW_FREAKZ_PASS = os.getenv("WOW_FREAKZ_PASS")

async def restore_character(name: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # login
        await page.goto("https://legion.wow-freakz.com/index.php", wait_until="domcontentloaded")

        # credentials
        await page.evaluate(f'''
            document.querySelector('input[name="user"]').value = "{WOW_FREAKZ_USER}";
            document.querySelector('input[name="pass"]').value = "{WOW_FREAKZ_PASS}";
            document.querySelector('input[name="submit"][value="Login"]').click();
        ''')

        await page.wait_for_selector('a.medium_link[href="/admin/deleted_characters.php"]')

        # deleted characters + all levels
        await page.goto("https://legion.wow-freakz.com/admin/deleted_characters.php?all", wait_until="domcontentloaded")

        # query character
        font_elements = await page.query_selector_all('font[color="yellow"]')
        char_id = None

        for font_el in font_elements:
            char_name = (await font_el.inner_text()).strip()
            if char_name.lower() == name.lower():
                parent = await font_el.evaluate_handle("el => el.closest('tr') || el.parentElement")
                text = await parent.inner_text()
                match = re.search(rf'{re.escape(char_name)}\[(\d+)\]', text)
                if match:
                    char_id = match.group(1)
                    break

        if not char_id:
            await browser.close()
            return False

        restore_link = await page.query_selector(f'a[href="?restore={char_id}"]')
        if not restore_link:
            await browser.close()
            return False

        await restore_link.click()
        await page.wait_for_load_state("domcontentloaded")

        success_font = await page.query_selector('font[color="cyan"] > b')
        if not success_font:
            await browser.close()
            return False

        restored_name = (await success_font.inner_text()).strip()
        await browser.close()

        return restored_name.lower() == name.lower()

@app_commands.command(name="restore-char", description="Restore a deleted character")
@app_commands.describe(name="Character name to restore")
async def restore_char(interaction, name: str):
    await interaction.response.defer()
    msg = await interaction.followup.send(f"Searching for **{name}**...")

    restored = await restore_character(name)

    if restored:
        await msg.edit(content=f"<a:done:1363613944417222788> **{name}** was successfully restored.")
    else:
        await msg.edit(content=f"❌ Could not restore character: **{name}**. Wrong name or character was not Level 100 or above.")
