import discord
from discord import app_commands
import json

def load_account_data():
    try:
        with open('accounts.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("accounts.json file not found.")
        return {"GM": [], "QA": []}

def save_account_data(data):
    with open('accounts.json', 'w') as f:
        json.dump(data, f, indent=4)

@app_commands.command(name="remove-staff", description="Remove staff member by type and PlayAcc ID.")
@app_commands.describe(
    staff_type="Select the type of staff member",
    playacc_id="Enter play acc ID"
)
@app_commands.choices(staff_type=[
    app_commands.Choice(name="GM", value="GM"),
    app_commands.Choice(name="QA", value="QA")
])
async def remove_staff(
    interaction: discord.Interaction,
    staff_type: app_commands.Choice[str],
    playacc_id: int
):
    staff_data = load_account_data()

    selected_type = staff_type.value

    staff_list = staff_data[selected_type]
    staff_member = next((staff for staff in staff_list if staff['id'] == playacc_id), None)

    if staff_member:
        staff_data[selected_type] = [staff for staff in staff_list if staff['id'] != playacc_id]
        save_account_data(staff_data)

        await interaction.response.send_message(
            f"<a:done:1363613944417222788> Removed **{staff_member['name']}** (ID: {staff_member['id']}) from **{selected_type}**."
        )
    else:
        await interaction.response.send_message(
            f"❌ No staff member found with ID {playacc_id} in {selected_type}."
        )