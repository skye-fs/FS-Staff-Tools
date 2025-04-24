import discord
from discord import app_commands
import json
import os

def load_payout_data():
    payout_file = "payout_dates.json"
    if not os.path.exists(payout_file):
        return {"GM": [], "QA": []}
    with open(payout_file, "r") as f:
        return json.load(f)

@app_commands.command(name="payout-dates", description="View payout dates for GM and QA.")
async def payout_dates(interaction: discord.Interaction):
    payout_data = load_payout_data()

    gm_list = payout_data.get("GM", [])
    qa_list = payout_data.get("QA", [])

    gm_dates = "\n".join(
        f"<a:arrow:1363871420454535168> {entry['payout_date']} (LATEST)" if i == len(gm_list) - 1 else f"{entry['payout_date']}"
        for i, entry in enumerate(gm_list)
    )

    qa_dates = "\n".join(
        f"<a:arrow:1363871420454535168> {entry['payout_date']} (LATEST)" if i == len(qa_list) - 1 else f"{entry['payout_date']}"
        for i, entry in enumerate(qa_list)
    )

    response_message = (
        f"<:felcoin:1363668083742474290> **Payout Dates Overview**\n\n"
        f"**GM Payout Dates:**\n{gm_dates if gm_dates else 'No GM payout dates recorded.'}\n\n"
        f"**QA Payout Dates:**\n{qa_dates if qa_dates else 'No QA payout dates recorded.'}"
    )

    await interaction.response.send_message(response_message)