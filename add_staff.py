import discord
from discord import app_commands
import json
import os

ACCOUNTS_FILE = "accounts.json"

def load_account_data():
    if not os.path.exists(ACCOUNTS_FILE) or os.path.getsize(ACCOUNTS_FILE) == 0:
        return {"GM": [], "QA": [], "Helper": []}

    with open(ACCOUNTS_FILE, 'r') as f:
        data = json.load(f)

    for key in ["GM", "QA", "Helper"]:
        if key not in data:
            data[key] = []

    return data

def save_account_data(data):
    with open(ACCOUNTS_FILE, 'w') as f:
        json.dump(data, f, indent=4)

@app_commands.command(name="add-staff", description="Add a new staff member.")
@app_commands.describe(
    staff_type="Select the type of staff",
    staff_rank="Select the rank of the staff member",
    name="Enter staff name",
    playacc_id="Enter play acc ID",
    discord_id="Enter the Discord ID of the GM (optional for QA)"
)
@app_commands.choices(staff_type=[
    app_commands.Choice(name="GM", value="GM"),
    app_commands.Choice(name="QA", value="QA"),
    app_commands.Choice(name="Helper", value="Helper")
])

@app_commands.choices(staff_rank=[
    app_commands.Choice(name="Regular QA", value="Regular QA"),
    app_commands.Choice(name="Regular GM", value="Regular GM"),
    app_commands.Choice(name="Senior GM", value="Senior GM"),
    app_commands.Choice(name="Head GM", value="Head GM"),
    app_commands.Choice(name="Server Manager", value="Server Manager"),
    app_commands.Choice(name="Discord Helper", value="Discord Helper")
])

async def add_staff(
    interaction: discord.Interaction,
    staff_type: app_commands.Choice[str],
    staff_rank: app_commands.Choice[str],
    name: str,
    playacc_id: int,
    discord_id: str = None  # optional for QA and Helper
):

    if staff_type.value == "GM" and not discord_id:
        await interaction.response.send_message(
            "❌ You must provide a Discord ID when adding a GM. Please run the command with the `discord_id` field.",
            ephemeral=False
        )
        return

    if discord_id:
        try:
            discord_id = int(discord_id)
        except ValueError:
            await interaction.response.send_message("❌ Please provide a valid Discord ID (integer).", ephemeral=True)
            return

    data = load_account_data()

    new_entry = {"name": name, "id": playacc_id, "rank": staff_rank.value}
    if discord_id:
        new_entry["discord_id"] = discord_id

    data[staff_type.value].append(new_entry)
    save_account_data(data)

    await interaction.response.send_message(
        f"<a:done:1363613944417222788> Added **{name}** (PlayAcc ID: {playacc_id}, Discord ID: {discord_id if discord_id else 'N/A'}) to **{staff_type.value}**."
    )
