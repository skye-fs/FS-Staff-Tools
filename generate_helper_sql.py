import discord
from discord import app_commands
import asyncio
import json
import os

ACCOUNTS_FILE = "accounts.json"
ACTIVITY_FILE = "discord_activity.json"
HISTORY_FILE = "helper_rewards_history.json"

def load_account_data():
    if not os.path.exists(ACCOUNTS_FILE):
        return {"GM": [], "QA": [], "Helper": []}
    with open(ACCOUNTS_FILE, 'r') as f:
        return json.load(f)

def load_discord_activity():
    if not os.path.exists(ACTIVITY_FILE):
        return {}
    with open(ACTIVITY_FILE, 'r') as f:
        return json.load(f)

@app_commands.command(name="generate-helper-sql", description="Generate SQL for Helper rewards.")
async def generate_helper_sql(interaction: discord.Interaction):
    await interaction.response.send_message("🗓️ Enter the **month/period** (e.g. May-1 to May-31):")

    def check(msg):
        return msg.author == interaction.user and msg.channel == interaction.channel

    try:
        period_msg = await interaction.client.wait_for("message", timeout=60.0, check=check)
        period_str = period_msg.content.strip()
        await period_msg.add_reaction("<a:done:1363613944417222788>")
    except asyncio.TimeoutError:
        await interaction.followup.send("⏰ Timed out waiting for input.")
        return

    account_data = load_account_data()
    helpers = account_data.get("Helper", [])
    discord_activity = load_discord_activity()

    rewards = []
    summary_msg = await interaction.followup.send("Calculating Helper rewards...")

    for index, helper in enumerate(helpers):
        name = helper["name"]
        acc_id = helper["id"]
        discord_id = str(helper.get("discord_id", ""))

        support = discord_activity.get(discord_id, {}).get("support", 0)
        chat = discord_activity.get(discord_id, {}).get("chat", 0)

        total = round(200 + (support * 1.5) + (chat * 0.2))

        rewards.append({
            "name": name,
            "id": acc_id,
            "support": support,
            "chat": chat,
            "total": total
        })

        updated_text = "🧮 Calculating Helper rewards...\n" + "\n".join(
            f"{r['name']} - {r['total']}{' 👈' if i == index else ''}" for i, r in enumerate(rewards)
        )
        await summary_msg.edit(content=updated_text)

    if not rewards:
        await interaction.followup.send("❌ No Helper data processed.")
        return

    # Final summary
    final_summary = "<a:done:1363613944417222788> **Helper reward distribution complete!**\n" + "\n".join(
        f"- {r['name']} - {r['total']}" for r in rewards
    )
    await summary_msg.edit(content=final_summary)

    # SQL block
    sql_lines = []
    for r in rewards:
        sql = f"""INSERT INTO api_points (AccountID, Date, Points, Data, reference)
VALUES
({r['id']}, NOW(), {r['total']},
'{{\n  "code": "",\n  "reason": "Helper Funds {period_str} {r['name']}",\n  "source": "admin",\n  "by": "{interaction.user.name}"\n}}', '');"""
        sql_lines.append(sql)

    await interaction.followup.send("```sql\n" + "\n".join(sql_lines) + "\n```")

    # Save to helper_rewards_history.json (FOR VIEWING PAYMENT HISTORY)
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            try:
                history = json.load(f)
            except json.JSONDecodeError:
                history = {}
    else:
        history = {}

    history[period_str] = rewards

    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)
