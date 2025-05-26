import discord
from discord.ext import commands
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
from armory import armory

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
FELSONG_SESSION = os.getenv("FELSONG_SESSION")
CSRF_TOKEN = os.getenv("CSRF_TOKEN")

GUILD_IDS = [
    785816801602830346,
    873228748458188841
]

class Client(commands.Bot):
    async def on_ready(self):
        print(f'Logged on as {self.user}.')

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
client = Client(command_prefix="%", intents=intents)

client.run(TOKEN)
