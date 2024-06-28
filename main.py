import os
from dotenv import load_dotenv
import discord
import tempfile
import logging

load_dotenv()
logging.basicConfig(filename="bot.log", level=logging.INFO)

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
    content_type = submission.content_type
    logging.info(content_type)
    if "video" not in content_type and "image" not in content_type:
        await interaction.response.send_message(
            f"File must be an image or video. Got {content_type}", ephemeral=True
        )
        return

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
