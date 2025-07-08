import discord
from discord import app_commands
import json

EVENTS_FILE = "event_records.json"

def save_event_data(data):
    with open(EVENTS_FILE, 'w') as f:
        json.dump(data, f, indent=4)

@app_commands.command(name="wipe-events", description="TESTING PURPOSE. WIPES ALL EVENT RECORDS - DO NOT USE")
async def wipe_events(interaction: discord.Interaction):
    empty_data = {"events": []}
    save_event_data(empty_data)
    await interaction.response.send_message("**ALL EVENT ENTRIES WIPED**")
