import discord
from discord import app_commands
import asyncio
import json
import os

ACCOUNTS_FILE = "accounts.json"
ACTIVITY_FILE = "discord_activity.json"

BONUS_IF_MET_QUOTA = 600 # SUBJECT TO CHANGE

def load_account_data():
    if not os.path.exists(ACCOUNTS_FILE):
        return {"GM": [], "QA": []}
    with open(ACCOUNTS_FILE, 'r') as f:
        return json.load(f)

def load_discord_activity():
    if not os.path.exists(ACTIVITY_FILE):
        return {}
    with open(ACTIVITY_FILE, 'r') as f:
        return json.load(f)

@app_commands.command(name="generate-gm-sql", description="Generate SQL statements for GMs.")
async def generate_gm_sql(interaction: discord.Interaction):
    await interaction.response.send_message("🗓️ Enter the **month/period** (e.g. `Mar-12 to Apr-15`) for this GM reward distribution:")

    def check(msg):
        return msg.author == interaction.user and msg.channel == interaction.channel

    try:
        period_msg = await interaction.client.wait_for("message", timeout=60.0, check=check)
        month_str = period_msg.content.strip()
        await period_msg.add_reaction("<a:done:1363613944417222788>")
        payout_file = "payout_dates.json"
        try:
            payout_data = {"GM": [], "QA": []}

            if os.path.exists(payout_file):
                with open(payout_file, "r") as f:
                    try:
                        payout_data = json.load(f)
                        if not isinstance(payout_data, dict) or "GM" not in payout_data or "QA" not in payout_data:
                            payout_data = {"GM": [], "QA": []}
                    except json.JSONDecodeError:
                        payout_data = {"GM": [], "QA": []}

            gm_id = len(payout_data["GM"]) + 1

            payout_data["GM"].append({
                "id": gm_id,
                "payout_date": month_str
            })

            with open(payout_file, "w") as f:
                json.dump(payout_data, f, indent=2)

        except Exception as e:
            print(f"Error writing to {payout_file}: {e}")

    except asyncio.TimeoutError:
        await interaction.followup.send("⏰ Timed out waiting for month input.")
        return

    account_data = load_account_data()
    gm_entries = account_data.get("GM", [])
    discord_activity = load_discord_activity()

    rewards = []

    summary_msg = await interaction.followup.send(
        "<:felcoin:1363668083742474290> Adding GM funds...\n" +
        "\n".join(f"{gm['name']} - 0{' 👈' if i == 0 else ''}" for i, gm in enumerate(gm_entries))
    )

    for index, gm in enumerate(gm_entries):
        name = gm["name"]
        acc_id = gm["id"]
        rank = gm["rank"]
        BASE_AMOUNT = {
            "Regular GM": 400,
            "Senior GM": 800,
            "Head GM": 1600,
            "Server Manager": 2500
        }[rank]
        discord_id = str(gm.get("discord_id", ""))
        discord_messages = discord_activity.get(discord_id, 0)

        # Ask for ticket count
        ticket_prompt = await interaction.followup.send(f"🎟️ Enter ticket count for **{name}**:")
        try:
            ticket_msg = await interaction.client.wait_for("message", timeout=60.0, check=check)
            ticket_count = int(ticket_msg.content.strip())
            await ticket_msg.add_reaction("<a:done:1363613944417222788>")
        except (asyncio.TimeoutError, ValueError):
            await ticket_prompt.delete()
            await interaction.followup.send(f"❌ Skipping {name} due to invalid or no ticket input.")
            continue
        await ticket_prompt.delete()

        # Ask for quota
        quota_prompt = await interaction.followup.send(f"📊 Did **{name}** meet their monthly quota? (yes/no):")
        try:
            quota_msg = await interaction.client.wait_for("message", timeout=60.0, check=check)
            quota_bonus = BONUS_IF_MET_QUOTA if quota_msg.content.strip().lower() == "yes" else 0
            await quota_msg.add_reaction("<a:done:1363613944417222788>")
        except asyncio.TimeoutError:
            quota_bonus = 0
        await quota_prompt.delete()

        total = round(BASE_AMOUNT + (ticket_count * 3) + (discord_messages * 1.5) + quota_bonus)

        rewards.append({
            "name": name,
            "id": acc_id,
            "ticket_count": ticket_count,
            "discord_messages": discord_messages,
            "quota_bonus": quota_bonus,
            "base_amount": BASE_AMOUNT,
            "total": total
        })

        # Update progress
        updated_text = "<:felcoin:1363668083742474290> Adding GM funds...\n" + "\n".join(
            f"{g['name']} - {next((r['total'] for r in rewards if r['name'] == g['name']), 0)}{' 👈' if i == index + 1 else ''}"
            for i, g in enumerate(gm_entries)
        )
        await summary_msg.edit(content=updated_text)

    if not rewards:
        await interaction.followup.send("❌ No GM data was processed.")
        return

    # Final summary message
    final_text = "<a:done:1363613944417222788> **Adding GM funds... done!**\n" + "\n".join(
        f"- {r['name']} - {r['total']}" for r in rewards
    )
    await summary_msg.edit(content=final_text)

    # Detailed payout summary
    summary = ["<:felcoin:1363668083742474290> **GM Payout Summary:**\n"]
    for r in rewards:
        summary.append(
            f"**{r['name']}**\n"
            f"Tickets: `{r['ticket_count']}`\n"
            f"Discord: `{r['discord_messages']}`\n"
            f"Quota Bonus: `{r['quota_bonus']}`\n"
            f"Rank Bonus: `{r['base_amount']}`\n"
            f"Total: `{r['total']}`\n"
        )
    await interaction.followup.send("\n".join(summary))

    # Generate SQL block
    sql_lines = []
    for r in rewards:
        sql = f"""INSERT INTO `api_points` (`AccountID`, `Date`, `Points`, `Data`, `reference`) 
VALUES
({r['id']}, NOW(), {r['total']},
'{{\n  "code": "",\n  "reason": "GM Funds {month_str} {r['name']}",\n  "source": "admin",\n  "by": "{interaction.user.name}"\n}}', '');\n"""
        sql_lines.append(sql)

    await interaction.followup.send("```sql\n" + "\n".join(sql_lines) + "```")
