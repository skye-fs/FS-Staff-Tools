import discord
import json
import os
from discord import app_commands
from discord.ext import commands

EVENTS_FILE = 'event_records.json'

class EventView(discord.ui.View):
    def __init__(self, pages):
        super().__init__(timeout=180)
        self.pages = pages
        self.current = 0

    async def update(self, interaction):
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = False

        if self.current == 0:
            self.children[0].disabled = True
        if self.current == len(self.pages) - 1:
            self.children[1].disabled = True

        await interaction.response.edit_message(content=self.pages[self.current], view=self)

    @discord.ui.button(label='Previous', style=discord.ButtonStyle.secondary, disabled=True)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current -= 1
        await self.update(interaction)

    @discord.ui.button(label='Next', style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current += 1
        await self.update(interaction)

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

def format_event_pages(event_list, max_chars=1900):
    if not event_list:
        return ["No events have been recorded yet."]

    pages = []
    current_page = "```"
    header = f"{'Event ID':<9} | {'Type':<15} | {'Hosted By':<10} | {'Date & Time':<20}\n"
    separator = "-" * 65 + "\n"
    current_page += header + separator

    for event in event_list:
        event_text = f"{event['event_id']:<9} | {event['event_type']:<15} | {event['hosted_by']:<10} | {event['hosted_on']:<20}\n"
        if event.get("winners"):
            event_text += f"{'':<9} | {'Winners:':<15}\n"
            for winner in event["winners"]:
                event_text += f"{'':<9} |    - {winner['name']} ({winner['reward']})\n"
        else:
            event_text += f"{'':<9} |    No winners recorded\n"
        event_text += separator

        if len(current_page) + len(event_text) > max_chars:
            current_page += "```"
            pages.append(current_page)
            current_page = "``` " + header + separator + event_text
        else:
            current_page += event_text

    current_page += "```"
    pages.append(current_page)
    return pages

@app_commands.command(name="view-events", description="View all recorded GM events.")
async def view_events(interaction: discord.Interaction):
    await interaction.response.defer()
    event_data = load_event_data()
    pages = format_event_pages(event_data["events"])

    if len(pages) == 1:
        await interaction.followup.send(pages[0])
    else:
        await interaction.followup.send(content=pages[0], view=EventView(pages))
