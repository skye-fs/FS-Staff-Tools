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
from armory import armory, search_character
import asyncio

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
FELSONG_SESSION = os.getenv("FELSONG_SESSION")
CSRF_TOKEN = os.getenv("CSRF_TOKEN")

GUILD_IDS = [
    785816801602830346,
    873228748458188841
]

USER_ID = 516459534714404874  # Users to DM for Bot Alerts

user_token_states = {}

background_task = None  # Just for reference

def write_env_file(session_token, csrf_token):
    """Overwrite .env with updated token values."""
    lines = []
    with open(".env", "r") as f:
        for line in f:
            if line.startswith("FELSONG_SESSION="):
                lines.append(f"FELSONG_SESSION={session_token}\n")
            elif line.startswith("CSRF_TOKEN="):
                lines.append(f"CSRF_TOKEN={csrf_token}\n")
            else:
                lines.append(line)
    with open(".env", "w") as f:
        f.writelines(lines)

async def background_search_task(bot):
    target = "Skye"
    await bot.wait_until_ready()
    user = await bot.fetch_user(USER_ID)

    global FELSONG_SESSION, CSRF_TOKEN
    print("Starting background search task")

    while not bot.is_closed():
        result = search_character(target)
        if result == "expired":
            print("Tokens expired or invalid. Stopping background search.")
            if user:
                try:
                    await user.send("Armory tokens expired. Provide new value for **FELSONG_SESSION**.")
                    user_token_states[USER_ID] = "waiting_session"
                except Exception as e:
                    print(f"Failed to send DM: {e}")
            break
        if result:
            print("Found:", result)
            print(f"Armory link: https://felsong.gg/en/community/armory/{result['armory_id']}")
        else:
            print("Character not found")
        await asyncio.sleep(1)
    print("Background search task ended")

class Client(commands.Bot):
    async def setup_hook(self):
        global background_task
        background_task = self.loop.create_task(background_search_task(self))

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

    async def on_message(self, message):
        if message.author.bot:
            return
        if not isinstance(message.channel, discord.DMChannel):
            return

        state = user_token_states.get(message.author.id)
        global FELSONG_SESSION, CSRF_TOKEN, background_task

        if state == "waiting_session":
            FELSONG_SESSION = message.content.strip()
            user_token_states[message.author.id] = "waiting_csrf"
            await message.channel.send("Provide new value for **CSRF_TOKEN**.")
        elif state == "waiting_csrf":
            CSRF_TOKEN = message.content.strip()
            user_token_states.pop(message.author.id)

            try:
                write_env_file(FELSONG_SESSION, CSRF_TOKEN)
                await message.channel.send(".env updated successfully.")
                print("Tokens updated, restarting background task.")

                # Restart background task
                if background_task and not background_task.done():
                    background_task.cancel()
                    try:
                        await background_task
                    except asyncio.CancelledError:
                        pass

                background_task = self.loop.create_task(background_search_task(self))
            except Exception as e:
                await message.channel.send(f"Failed to update .env: {e}")
        else:
            pass


intents = discord.Intents.default()
intents.message_content = True
client = Client(command_prefix="!", intents=intents)

client.run(TOKEN)
