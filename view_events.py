import discord
import json
import os
from discord import app_commands

EVENTS_FILE = 'event_records.json'


def load_event_data():
    # If file doesn't exist or is empty, initialize with base structure
    if not os.path.exists(EVENTS_FILE) or os.path.getsize(EVENTS_FILE) == 0:
        with open(EVENTS_FILE, 'w') as f:
            json.dump({"events": []}, f, indent=2)

    try:
        with open(EVENTS_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        # If the file is corrupted or not proper JSON, reinitialize
        with open(EVENTS_FILE, 'w') as f:
            json.dump({"events": []}, f, indent=2)
        return {"events": []}


def format_event_list(event_list):
    if not event_list:
        return "No events have been recorded yet."

    output = "```\n"
    output += f"{'Event ID':<9} | {'Type':<15} | {'Hosted By':<10} | {'Date & Time':<20}\n"
    output += "-" * 65 + "\n"

    for event in event_list:
        output += f"{event['event_id']:<9} | {event['event_type']:<15} | {event['hosted_by']:<10} | {event['hosted_on']:<20}\n"

        if event.get("winners"):
            output += f"{'':<9} | {'Winners:':<15}\n"
            for winner in event["winners"]:
                output += f"{'':<9} |    - {winner['name']} ({winner['reward']})\n"
        else:
            output += f"{'':<9} |    No winners recorded\n"

        output += "-" * 65 + "\n"

    output += "```"
    return output


@app_commands.command(name="view-events", description="View all recorded GM events.")
async def view_events(interaction: discord.Interaction):
    event_data = load_event_data()
    event_block = format_event_list(event_data["events"])

    await interaction.response.send_message(event_block)
