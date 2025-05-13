import discord
from discord import app_commands
import asyncio
import json
import os
def load_account_data():
    with open("accounts.json", "r") as f:
        return json.load(f)

@app_commands.command(name="generate-qa-sql", description="Generate SQL statements for QA.")
async def generate_qa_sql(interaction: discord.Interaction):
    await interaction.response.send_message("🗓️ Enter the **month/period** (e.g. `Mar-12 to Apr-15`) for this QA reward distribution:")

    def check_month(m):
        return m.author == interaction.user and m.channel == interaction.channel

    try:
        month_msg = await interaction.client.wait_for("message", timeout=60.0, check=check_month)
        month_str = month_msg.content
        await month_msg.add_reaction("<a:done:1363613944417222788>")

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

            qa_id = len(payout_data["QA"]) + 1

            payout_data["QA"].append({
                "id": qa_id,
                "payout_date": month_str
            })

            with open(payout_file, "w") as f:
                json.dump(payout_data, f, indent=2)

        except Exception as e:
            print(f"Error writing to {payout_file}: {e}")

    except asyncio.TimeoutError:
        await interaction.followup.send("⏰ Timed out waiting for month input.")
        return

    # Load dict
    data = load_account_data()
    qa_staff = data.get("QA", [])
    rewards = {}

    initial_msg = await interaction.followup.send(
        "<:felcoin:1363668083742474290> Adding QA funds...\n" + "\n".join(
            f"{staff['name']} - 0{' 👈' if i == 0 else ''}"
            for i, staff in enumerate(qa_staff)
        )
    )

    for index, staff in enumerate(qa_staff):
        name = staff['name']
        prompt_msg = await interaction.followup.send(f"Enter amount for **{name}**:")

        def check_amount(m):
            return m.author == interaction.user and m.channel == interaction.channel and m.content.isdigit()

        try:
            user_msg = await interaction.client.wait_for("message", timeout=60.0, check=check_amount)
            amount = int(user_msg.content)
            rewards[name] = amount

            await user_msg.delete()
            await prompt_msg.delete()

            updated_text = "<:felcoin:1363668083742474290> Adding QA funds...\n" + "\n".join(
                f"{s['name']} - {rewards.get(s['name'], 0)}{' 👈' if i == index + 1 else ''}"
                for i, s in enumerate(qa_staff)
            )
            await initial_msg.edit(content=updated_text)

        except asyncio.TimeoutError:
            await prompt_msg.delete()
            await interaction.followup.send("⏰ Timed out waiting for input.")
            return

    # Generate SQL block
    sql_lines = []
    for staff in qa_staff:
        name = staff["name"]
        acc_id = staff["id"]
        amount = rewards.get(name, 0)
        if amount > 0:
            sql = f"""INSERT INTO `api_points` (`AccountID`, `Date`, `Points`, `Data`, `reference`) 
VALUES
({acc_id}, NOW(), {amount},
'{{\n  "code": "",\n  "reason": "QA Funds {month_str} {name}",\n  "source": "admin",\n  "by": "{interaction.user.name}"\n}}', '');\n"""
            sql_lines.append(sql)

    final_text = "<a:done:1363613944417222788> **Adding QA funds... done!**\n" + "\n".join(f"- {name} - {rewards[name]}" for name in rewards)
    await initial_msg.edit(content=final_text)

    MAX_MESSAGE_LENGTH = 2000

    def chunk_message(sql_text, prefix="```sql\n", suffix="```"):
        chunks = []
        current = prefix
        for line in sql_text.splitlines(keepends=True):
            if len(current) + len(line) + len(suffix) > MAX_MESSAGE_LENGTH:
                chunks.append(current + suffix)
                current = prefix + line
            else:
                current += line
        chunks.append(current + suffix)
        return chunks

    sql_combined = "\n".join(sql_lines)
    for chunk in chunk_message(sql_combined):
        await interaction.followup.send(chunk)

    # Save to qa_rewards_history.json (FOR VIEWING PAYMENT HISTORY)
    qa_history_file = "qa_rewards_history.json"
    if os.path.exists(qa_history_file):
        with open(qa_history_file, "r") as f:
            try:
                qa_history = json.load(f)
            except json.JSONDecodeError:
                qa_history = {}
    else:
        qa_history = {}

    qa_history[month_str] = rewards

    with open(qa_history_file, "w") as f:
        json.dump(qa_history, f, indent=2)

