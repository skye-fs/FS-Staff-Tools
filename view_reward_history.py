import discord
from discord import app_commands
import json
import os

def load_reward_history(role: str):
    filename = f"{role.lower()}_rewards_history.json"
    if not os.path.exists(filename):
        return {}
    with open(filename, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

@app_commands.command(name="view-reward-history", description="View past reward history.")
@app_commands.describe(role="Select staff type")
async def view_reward_history(interaction: discord.Interaction, role: str):
    role = role.upper()
    if role not in ["GM", "QA", "HELPER"]:
        await interaction.response.send_message("Invalid role. Choose either GM, QA or Helper", ephemeral=True)
        return

    history = load_reward_history(role)
    if not history:
        await interaction.response.send_message(f"No reward history found for {role}.", ephemeral=True)
        return

    class DateDropdown(discord.ui.Select):
        def __init__(self):
            options = [
                discord.SelectOption(label=key, description=f"{role} payout") for key in history.keys()
            ]
            super().__init__(placeholder=f"Select a {role} payout period", min_values=1, max_values=1, options=options)

        async def callback(self, interaction2: discord.Interaction):
            selected_date = self.values[0]
            entries = history[selected_date]
            result_lines = [f"<:felcoin:1363668083742474290> **{role} Rewards – {selected_date}**\n"]

            for entry in entries:
                if role == "GM":
                    result_lines.append(
                        f"**{entry['name']}**\n"
                        f"Tickets: `{entry.get('ticket_count', 0)}`\n"
                        f"Support Messages: `{entry.get('support_message', 0)}`\n"
                        f"Chat Messages: `{entry.get('chat_message', 0)}`\n"
                        f"Quota Bonus: `{entry.get('quota_bonus', 0)}`\n"
                        f"Shop Bonus: `{entry.get('shop_ticket_bonus', 0)}`\n"
                        f"Extra Work Bonus: `{entry.get('extra_work_bonus', 0)}`\n"
                        f"Rank Bonus: `{entry.get('base_amount', 0)}`\n"
                        f"Total: `{entry['total']}`\n"
                    )
                else:  # QA
                    result_lines.append(
                        f"**{entry['name']}** – `{entry.get('total', 0)}`"
                    )

            await interaction2.response.send_message("\n".join(result_lines), ephemeral=False)

    class DropdownView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=60)
            self.add_item(DateDropdown())

    await interaction.response.send_message(f"Select a {role} payout period to view rewards:", view=DropdownView(), ephemeral=False)
