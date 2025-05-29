import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
from datetime import datetime

# slash command imports
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
from restore_char import restore_char

# load .env variables
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
FELSONG_SESSION = os.getenv("FELSONG_SESSION")
CSRF_TOKEN = os.getenv("CSRF_TOKEN")

GUILD_IDS = [
    785816801602830346,
    873228748458188841
]

KEYWORD_IDS = 516459534714404874
RESUME_LOG_CHANNEL_ID = 1366862354972676166

class Client(commands.Bot):
    async def on_ready(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        session_id = self.ws.session_id

        # connection log
        msg = f"[{now}] [INFO] discord.gateway: Shard ID None has connected to Gateway (Session ID: {session_id})."
        channel = self.get_channel(RESUME_LOG_CHANNEL_ID)

        await channel.send(msg)
        print(f'Logged on as {self.user}.')
        self.start_time = datetime.now()
        activity = discord.Game("staff tools with more to come soon.")
        await self.change_presence(status=discord.Status.online, activity=activity)

        # register slash commands
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
                self.tree.add_command(restore_char, guild=guild)

            synced = await self.tree.sync(guild=guild)
            print(f"Synced {len(synced)} commands to guilds ({', '.join(f'{g.id} - {g.name}' for g in self.guilds if g.id in GUILD_IDS)})")
        except Exception as e:
            print(f'Error syncing commands: {e}')

    # mention logs
    async def on_message(self, message):
        if message.author.bot:
            return

        if 'skye' in message.content.lower():
            try:
                user = await self.fetch_user(KEYWORD_IDS)
                if user:
                    channel = message.channel
                    msg_link = f"https://discord.com/channels/{message.guild.id}/{channel.id}/{message.id}"
                    dm_content = (
                        f"**You were mentioned in <#{channel.id}> by {message.author.mention}**\n\n"
                        f"Message link: {msg_link}\n"
                        f"Message content: {message.content}"
                    )
                    await user.send(dm_content)
            except Exception as e:
                print(f"Error sending DM: {e}")

intents = discord.Intents.default()
intents.message_content = True
client = Client(command_prefix="%", intents=intents)

client.run(TOKEN)
