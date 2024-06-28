import os
from dotenv import load_dotenv
import discord
import tempfile

load_dotenv()

FIFTY_MB = 50_000_000
intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.reactions = True

client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)


@client.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {client.user}")


@tree.command(name="submit", description="Submit an entry for the competition")
async def submit(interaction: discord.Interaction, submission: discord.Attachment):
    if submission.size > FIFTY_MB:
        await interaction.response.send_message(
            "File size is too big. Must be less than 8MB", ephemeral=True
        )
        return

    channel: discord.TextChannel = discord.utils.get(
        interaction.guild.text_channels, name="wardrobe-warriors"
    )
    if not channel:
        channel = await interaction.guild.create_text_channel(
            name=os.getenv("COMPETITION_NAME")
        )

    file_suffix = submission.filename.split(".")[1]
    with tempfile.NamedTemporaryFile(mode="r+b", suffix=f".{file_suffix}") as file:
        data = await submission.read()
        file.write(data)
        file.seek(0)
        message: discord.Message = await channel.send(
            mention_author=True,
            content=f"Submitted by <@{interaction.user.id}>",
            file=discord.File(os.path.join("/tmp", file.name)),
        )
        await message.add_reaction(os.getenv("REACT_EMOTE"))

    await interaction.response.send_message("Submitted!", ephemeral=True)


client.run(token=os.getenv("TOKEN"))
