import os
from dotenv import load_dotenv
import discord
import tempfile
import logging
from typing import List

load_dotenv()
logging.basicConfig(filename="bot.log", level=logging.INFO)

FIFTY_MB = 50_000_000
intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.reactions = True

client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)


async def _validate_submissions(submissions: List[discord.Attachment]) -> bool:
    total_size = 0

    for s in submissions:
        total_size += s.size

    if total_size > FIFTY_MB:
        return False

    for s in submissions:
        content_type = s.content_type
        if "video" not in content_type and "image" not in content_type:
            return False

    return True


@client.event
async def on_ready():
    await tree.sync()
    logging.info(f"Logged in as {client.user}")


@tree.command(name="submit", description="Submit an entry for the competition")
async def submit(
    interaction: discord.Interaction,
    submission: discord.Attachment,
    additional1: discord.Attachment = None,
    additional2: discord.Attachment = None,
    description: str = "",
):
    await interaction.response.defer(ephemeral=True)
    submisisons: List[discord.Attachment] = [submission]

    if additional1:
        submisisons.append(additional1)

    if additional2:
        submisisons.append(additional2)

    if not await _validate_submissions(submisisons):
        await interaction.followup(
            "Submissions must be less than 50MB and be videos or images (including gifs)"
        )
        return

    channel: discord.TextChannel = discord.utils.get(
        interaction.guild.text_channels, name=os.getenv("COMPETITION_NAME")
    )
    if not channel:
        channel = await interaction.guild.create_text_channel(
            name=os.getenv("COMPETITION_NAME")
        )

    files: List[tempfile.NamedTemporaryFile] = []
    discord_files: List[discord.File] = []
    for s in submisisons:
        file_suffix = s.filename.split(".")[1]
        file = tempfile.NamedTemporaryFile(mode="wb", suffix=f".{file_suffix}")
        data = await s.read()

        file.write(data)
        file.seek(0)
        files.append(file)
        discord_files.append(discord.File(os.path.join("/tmp", file.name)))

    msg = f"Submitted by <@{interaction.user.id}>"
    if description:
        msg += f"\n{description}"
    message: discord.Message = await channel.send(
        mention_author=True,
        content=msg,
        files=discord_files,
    )
    await message.add_reaction(os.getenv("REACT_EMOTE"))

    for f in files:
        f.close()  # temp files are automatically deleted when closed

    await interaction.followup.send("Submitted!", ephemeral=True)


client.run(token=os.getenv("TOKEN"))
