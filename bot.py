import os
import re
import asyncio
import tempfile
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import yt_dlp

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
SUPPORT_SERVER_INVITE = os.getenv("SUPPORT_SERVER_INVITE", "https://discord.gg/")

# Discord Intents: Message Content Intent is required to read message links
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# URL matching regex
URL_REGEX = re.compile(r"https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b[-a-zA-Z0-9()@:%_\+.~#?&//=]*")

# Discord file size limits: 25MB default for standard bots/servers
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024

def download_media(url: str, output_dir: str, mode: str = "mp4"):
    """
    Downloads media using yt-dlp in the specified mode (mp4 or mp3).
    Returns the file path of the downloaded file.
    """
    outtmpl = os.path.join(output_dir, "%(title).80s.%(ext)s")

    if mode == "mp3":
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": outtmpl,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "320",
            }],
            "quiet": True,
            "no_warnings": True,
        }
    else:  # mp4
        ydl_opts = {
            # Highest quality video + audio merged into mp4
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "outtmpl": outtmpl,
            "merge_output_format": "mp4",
            "quiet": True,
            "no_warnings": True,
        }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)

        if mode == "mp3":
            base, _ = os.path.splitext(filename)
            filename = f"{base}.mp3"
        elif not os.path.exists(filename):
            base, _ = os.path.splitext(filename)
            filename = f"{base}.mp4"

        return filename, info.get("title", "media")


async def process_and_send(ctx_or_interaction, url: str, mode: str):
    """Handles downloading and uploading to Discord with size checks and error handling."""
    is_interaction = isinstance(ctx_or_interaction, discord.Interaction)

    # Inform user that download is starting
    status_msg = f"⏳ Downloading highest quality **{mode.upper()}** from link...\nPlease wait."
    if is_interaction:
        await ctx_or_interaction.followup.send(status_msg)
    else:
        status = await ctx_or_interaction.reply(status_msg)

    # Use a temporary directory so downloaded files are safely removed after sending
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            # yt-dlp runs synchronously, run in worker thread to prevent freezing the bot
            file_path, title = await asyncio.to_thread(download_media, url, tmpdir, mode)

            if not os.path.exists(file_path):
                raise FileNotFoundError("Downloaded file could not be located.")

            file_size = os.path.getsize(file_path)

            if file_size > MAX_FILE_SIZE_BYTES:
                size_mb = file_size / (1024 * 1024)
                err_text = (
                    f"⚠️ **File too large for Discord!**\n"
                    f"Title: `{title}`\n"
                    f"Size: `{size_mb:.2f} MB` (Discord limit is ~25 MB without server boost).\n"
                    f"Try downloading as MP3 instead or use a shorter video."
                )
                if is_interaction:
                    await ctx_or_interaction.followup.send(err_text)
                else:
                    await status.edit(content=err_text)
                return

            # Upload the file
            discord_file = discord.File(file_path, filename=os.path.basename(file_path))
            success_text = f"✅ **{title}** ({mode.upper()})"

            if is_interaction:
                await ctx_or_interaction.followup.send(content=success_text, file=discord_file)
            else:
                await ctx_or_interaction.reply(content=success_text, file=discord_file)
                await status.delete()

        except Exception as e:
            err_msg = f"❌ **Failed to download media:** {str(e)[:500]}"
            if is_interaction:
                await ctx_or_interaction.followup.send(err_msg)
            else:
                await status.edit(content=err_msg)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash command(s).")
    except Exception as e:
        print(f"Error syncing slash commands: {e}")


def get_bot_invite_url():
    """Generates a public bot invite link with Administrator permissions and slash commands scope."""
    return discord.utils.oauth_url(
        bot.user.id,
        permissions=discord.Permissions(administrator=True),
        scopes=("bot", "applications.commands")
    )


# --- Slash Commands ---

@bot.tree.command(name="invite", description="Get an invite link to add this bot to any server")
async def slash_invite(interaction: discord.Interaction):
    invite_url = get_bot_invite_url()
    embed = discord.Embed(
        title="🤖 Add Bot to Any Server",
        description=(
            f"This bot can be added to **any Discord server**!\n\n"
            f"👉 **[Click Here to Invite the Bot to Your Server]({invite_url})**"
        ),
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="mp4", description="Download highest quality MP4 video from a link")
@app_commands.describe(url="URL of the video to download")
async def slash_mp4(interaction: discord.Interaction, url: str):
    await interaction.response.defer()
    await process_and_send(interaction, url, mode="mp4")


@bot.tree.command(name="mp3", description="Download highest quality MP3 audio from a link")
@app_commands.describe(url="URL of the audio/video to extract as MP3")
async def slash_mp3(interaction: discord.Interaction, url: str):
    await interaction.response.defer()
    await process_and_send(interaction, url, mode="mp3")


@bot.tree.command(name="support", description="Get an invite to the Bot Support Server")
async def slash_support(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Need Help or Found a Bug?",
        description=f"Join our official support server for updates and assistance:\n👉 [Join Support Server]({SUPPORT_SERVER_INVITE})",
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed)


# --- Prefix Commands ---

@bot.command(name="invite")
async def cmd_invite(ctx):
    """Command: !invite"""
    invite_url = get_bot_invite_url()
    embed = discord.Embed(
        title="🤖 Add Bot to Any Server",
        description=(
            f"This bot can be added to **any Discord server**!\n\n"
            f"👉 **[Click Here to Invite the Bot to Your Server]({invite_url})**"
        ),
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)


@bot.command(name="mp4")
async def cmd_mp4(ctx, url: str):
    """Command: !mp4 <url>"""
    await process_and_send(ctx, url, mode="mp4")


@bot.command(name="mp3")
async def cmd_mp3(ctx, url: str):
    """Command: !mp3 <url>"""
    await process_and_send(ctx, url, mode="mp3")


@bot.command(name="support")
async def cmd_support(ctx):
    """Command: !support"""
    embed = discord.Embed(
        title="Need Help or Found a Bug?",
        description=f"Join our official support server for updates and assistance:\n👉 [Join Support Server]({SUPPORT_SERVER_INVITE})",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)


# --- Automatic Link Detection (Optional) ---
@bot.event
async def on_message(message: discord.Message):
    # Ignore messages sent by bots
    if message.author.bot:
        return

    # Process standard ! prefix commands first
    await bot.process_commands(message)


if __name__ == "__main__":
    if not TOKEN or TOKEN == "your_discord_bot_token_here":
        print("Error: DISCORD_TOKEN is not set in .env file.")
    else:
        bot.run(TOKEN)
