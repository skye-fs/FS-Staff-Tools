import discord
from discord import app_commands
import asyncio
import json
import os
import re
from datetime import datetime

ACCOUNTS_FILE = "accounts.json"
ACTIVITY_FILE = "discord_activity.json"

GUILD_ID = 873228748458188841
CHANNEL_IDS = [873265789157908510, 877411686192119818]

def load_account_data():
    if not os.path.exists(ACCOUNTS_FILE) or os.path.getsize(ACCOUNTS_FILE) == 0:
        return {"GM": [], "QA": [], "Helper": []}

    with open(ACCOUNTS_FILE, 'r') as f:
        data = json.load(f)

    for key in ["GM", "QA", "Helper"]:
        if key not in data:
            data[key] = []

    return data

def save_discord_activity(data):
    with open(ACTIVITY_FILE, 'w') as f:
        json.dump(data, f, indent=4)

@app_commands.command(name="get-discord-activity", description="Get Discord activity for GMs since given date.")
async def get_discord_activity(interaction: discord.Interaction):
    await interaction.response.send_message("📅 Provide start date to get Discord activity (format: `YYYY-MM-DD`)")

    def check(msg):
        return msg.author == interaction.user and msg.channel == interaction.channel

    try:
        date_msg = await interaction.client.wait_for("message", timeout=60.0, check=check)
        date_str = date_msg.content.strip()

        if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
            await interaction.followup.send("❌ Invalid date format. Use `YYYY-MM-DD`.")
            return

        start_date = datetime.strptime(date_str, "%Y-%m-%d")
        await date_msg.add_reaction("<a:done:1363613944417222788>")

    except asyncio.TimeoutError:
        await interaction.followup.send("⏰ Timed out waiting for date input.")
        return

    account_data = load_account_data()
    discord_id_entries = account_data.get("GM", []) + account_data.get("Helper", [])

    gm_discord_ids = {str(entry["discord_id"]) for entry in discord_id_entries if "discord_id" in entry}
    message_counts = {gm_id: {"support": 0, "chat": 0} for gm_id in gm_discord_ids}

    await interaction.followup.send("⏳ Counting messages...  This might take a while.")

    async def count_messages_in_channel(channel_id):
        channel = interaction.client.get_channel(channel_id)
        if not channel:
            return

        async for msg in channel.history(after=start_date, limit=None, oldest_first=True):
            author_id = str(msg.author.id)
            if author_id in message_counts:
                if channel_id == 873265789157908510:
                    message_counts[author_id]["support"] += 1
                elif channel_id == 877411686192119818:
                    message_counts[author_id]["chat"] += 1

    await asyncio.gather(*(count_messages_in_channel(ch_id) for ch_id in CHANNEL_IDS))

    save_discord_activity(message_counts)

    output_lines = []
    for uid, counts in message_counts.items():
        output_lines.append(f"<@{uid}>: {counts['support']} support / {counts['chat']} chat")

    output_text = "\n".join(output_lines)

    await interaction.followup.send(f"<a:done:1363613944417222788> **Activity count complete!**\n\n{output_text}")
