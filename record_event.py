import discord
import json
import os
from datetime import datetime
from discord import app_commands

EVENTS_FILE = 'event_records.json'

def load_event_data():
    if not os.path.exists(EVENTS_FILE) or os.path.getsize(EVENTS_FILE) == 0:
        with open(EVENTS_FILE, 'w') as f:
            json.dump({"events": []}, f, indent=2)

    try:
        with open(EVENTS_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        with open(EVENTS_FILE, 'w') as f:
            json.dump({"events": []}, f, indent=2)
        return {"events": []}

def save_event_data(data):
    with open(EVENTS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

@app_commands.command(name="record-event", description="Record a new GM event.")
@app_commands.describe(
    event_type="Provide event type (Trivia, Hide and Seek, Where am I",
    winners="Winners in format: playerName:Reward name + ID, playerName:Reward name + ID"
)
async def record_event(
    interaction: discord.Interaction,
    event_type: str,
    winners: str
):
    # Event Types
    allowed_types = ["Trivia", "Hide and Seek", "Where am I"]
    if event_type not in allowed_types:
        await interaction.response.send_message(f"❌ Invalid event type. Choose from: {', '.join(allowed_types)}", ephemeral=True)
        return

    data = load_event_data()
    event_id = len(data["events"]) + 1
    host_name = interaction.user.display_name
    hosted_on = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    # Parse winners
    winners_list = []
    if winners:
        try:
            winners_split = [w.strip() for w in winners.split(',')]
            winners_list = []
            for w in winners_split:
                name, reward = w.split(':')
                winners_list.append({
                    "name": name.strip(),
                    "reward": reward.strip()
                })
            if not winners_list:
                raise ValueError
        except ValueError:
            await interaction.response.send_message(
                "❌ You must include at least one winner in the format: `playerName:Reward name + ID`", ephemeral=True)
            return

    # Add new event to json
    new_event = {
        "event_id": event_id,
        "event_type": event_type,
        "hosted_by": host_name,
        "hosted_on": hosted_on,
        "winners": winners_list
    }

    data["events"].append(new_event)
    save_event_data(data)

    await interaction.response.send_message(f"<a:done:1363613944417222788> Event **{event_type}** recorded successfully by **{host_name}**!")
