import discord
from discord import app_commands
import json

ACCOUNTS_FILE = "accounts.json"

def save_account_data(data):
    with open(ACCOUNTS_FILE, 'w') as f:
        json.dump(data, f, indent=4)

@app_commands.command(name="wipe", description="TESTING PURPOSE DO NOT USE DO NOT USE DO NOT USE DO NOT USE")
async def wipe_do_not_use(interaction: discord.Interaction):
    empty_data = {"GM": [], "QA": []}
    save_account_data(empty_data)
    await interaction.response.send_message("**ALL STAFF ENTRIES WIPED**")
