import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import os
from datetime import datetime
import pytz

# slash command imports
from add_staff import add_staff
from remove_staff import remove_staff
from view_staff import view_staff
from generate_qa_sql import generate_qa_sql
from generate_gm_sql import generate_gm_sql
from wipe_staff import wipe_do_not_use
from wipe_events import wipe_events
from get_discord_activity import get_discord_activity
from payout_dates import payout_dates
from event_records import view_events
from record_event import record_event
from view_reward_history import view_reward_history
from armory import armory
from restore_char import restore_char
from generate_helper_sql import generate_helper_sql

# load .env variables
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
FELSONG_SESSION = os.getenv("FELSONG_SESSION")
CSRF_TOKEN = os.getenv("CSRF_TOKEN")
REMINDER_CHANNEL_ID = 1366862354972676166  # weekly event reminder channel id

GUILD_IDS = [
    785816801602830346,
    873228748458188841
]

KEYWORD_IDS = 516459534714404874
RESUME_LOG_CHANNEL_ID = 1366862354972676166

class Client(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reminder_sent = False

    async def on_ready(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        session_id = self.ws.session_id

        # connection log
        msg = f"[{now}] [INFO] discord.gateway: Shard ID None has connected to Gateway (Session ID: {session_id})."
        channel = self.get_channel(RESUME_LOG_CHANNEL_ID)

        await channel.send(msg)
        print(f'Logged on as {self.user}.')
        self.start_time = datetime.now()
        activity = discord.Game("/armory")
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
                self.tree.add_command(generate_helper_sql, guild=guild)
                self.tree.add_command(wipe_events, guild=guild)

            synced = await self.tree.sync(guild=guild)
            print(f"Synced {len(synced)} commands to guilds ({', '.join(f'{g.id} - {g.name}' for g in self.guilds if g.id in GUILD_IDS)})")
        except Exception as e:
            print(f'Error syncing commands: {e}')

        self.weekly_reminder.start()

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

    @tasks.loop(minutes=1)
    async def weekly_reminder(self):
        now = datetime.now(pytz.timezone("Europe/London"))
        if now.weekday() == 6 and now.hour == 17 and now.minute == 0:
            if not self.reminder_sent:
                channel = self.get_channel(REMINDER_CHANNEL_ID)
                if channel:
                    await channel.send(
                        content="<@&873242778413457458> - Reminder to host weekly **Where am I** event on Monday. Let us know here if you're hosting.",
                        allowed_mentions=discord.AllowedMentions(roles=True)
                    )
                self.reminder_sent = True
        else:
            self.reminder_sent = False

intents = discord.Intents.default()
intents.message_content = True
client = Client(command_prefix="%", intents=intents)

client.run(TOKEN)
