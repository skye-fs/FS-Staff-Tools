import discord
from discord import app_commands

@app_commands.command(name="event-details", description="Event instructions / guide")
@app_commands.describe(
    type="Select event type: Trivia / Hide and Seek / Where am I"
)
@app_commands.choices(type=[
    app_commands.Choice(name="Trivia", value="Trivia"),
    app_commands.Choice(name="Hide and Seek", value="Hide and Seek"),
    app_commands.Choice(name="Where am I", value="Where am I")
])
async def event_details(
    interaction: discord.Interaction,
    type: app_commands.Choice[str]
):
    await interaction.response.send_message(f"**{type.value}** selected")
