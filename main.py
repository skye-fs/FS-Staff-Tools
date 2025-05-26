import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import os
from add_staff import add_staff
from remove_staff import remove_staff
from view_staff import view_staff
from generate_qa_sql import generate_qa_sql
from generate_gm_sql import generate_gm_sql
from wipe_donotuse import wipe_do_not_use
from get_discord_activity import get_discord_activity
from payout_dates import payout_dates
from event_records import view_events
from record_event import record_event
from view_reward_history import view_reward_history
from armory import armory, search_character
import asyncio

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

GUILD_IDS = [
    785816801602830346,
    873228748458188841
]

USER_ID = 516459534714404874  # Users to DM for Bot Alerts
# LOOP START to identify expired tokens (ARMORY)
async def background_search_task(bot):
    target = "Skye"
    await bot.wait_until_ready()
    user = await bot.fetch_user(USER_ID)

    while not bot.is_closed():
        result = search_character(target)
        if result == "expired":
            print("Tokens expired or invalid. Stopping background search.")
            if user:
                try:
                    await user.send("Armory tokens expired.")
                except Exception as e:
                    print(f"Failed to send DM: {e}")
            break
        if result:
            print("Found:", result)
            print(f"Armory link: https://felsong.gg/en/community/armory/{result['armory_id']}")
        else:
            print("Character not found")
        await asyncio.sleep(1)
# LOOP END to identify expired tokens (ARMORY)

class Client(commands.Bot):
    async def setup_hook(self):
        self.loop.create_task(background_search_task(self))
    async def on_ready(self):
        print(f'Logged on as {self.user}.')

        # Custom status
        activity = discord.Game("staff tools with more to come soon.")
        await self.change_presence(status=discord.Status.online, activity=activity)

        try:
            for guild_id in GUILD_IDS:
                guild = discord.Object(id=guild_id)
                self.tree.add_command(add_staff, guild=guild)
                self.tree.add_command(remove_staff, guild=guild)
                self.tree.add_command(view_staff, guild=guild)
                self.tree.add_command(generate_qa_sql, guild=guild)
                self.tree.add_command(generate_gm_sql, guild=guild)
                self.tree.add_command(wipe_do_not_use, guild=guild)
                self.tree.add_command(get_discord_activity, guild=guild)
                self.tree.add_command(payout_dates, guild=guild)
                self.tree.add_command(view_events, guild=guild)
                self.tree.add_command(record_event, guild=guild)
                self.tree.add_command(view_reward_history, guild=guild)
                self.tree.add_command(armory, guild=guild)

            synced = await self.tree.sync(guild=guild)
            print(f"Synced {len(synced)} commands to guilds ({', '.join(f'{g.id} - {g.name}' for g in self.guilds if g.id in GUILD_IDS)})")
        except Exception as e:
            print(f'Error syncing commands: {e}')


intents = discord.Intents.default()
intents.message_content = True
client = Client(command_prefix="!", intents=intents)

client.run(TOKEN)
