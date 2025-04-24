import discord
import json
from discord import app_commands

def load_account_data():
    try:
        with open('accounts.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"GM": [], "QA": []}

def format_staff_list(staff_list, include_discord=False):
    if not staff_list:
        return "No accounts added (yet!)"

    if include_discord:
        header = "Name       | PlayAcc ID | Discord ID\n"
        divider = "-----------|------------|----------------------\n"
        body = "\n".join(
            f"{s['name']:<10} | {s['id']:<10} | {s.get('discord_id', 'N/A')}" for s in staff_list
        )
    else:
        header = "Name       | PlayAcc ID\n"
        divider = "-----------|------------\n"
        body = "\n".join(
            f"{s['name']:<10} | {s['id']:<10}" for s in staff_list
        )
    return f"```\n{header}{divider}{body}\n```"


@app_commands.command(name="view-staff", description="View all staff members.")
async def view_staff(interaction: discord.Interaction):
    staff_data = load_account_data()
    gm_block = format_staff_list(staff_data["GM"], include_discord=True)
    qa_block = format_staff_list(staff_data["QA"])

    response = f"<:felsong:1364763597770723459> __**GM List**__\n{gm_block}\n<:felsong:1364763597770723459> __**QA List**__\n{qa_block}"
    await interaction.response.send_message(response)
