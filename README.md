# Discord Media Downloader Bot

A high-performance Discord bot that downloads video and audio from web links in high quality (MP4 / 320kbps MP3) and sends them to Discord channels.

---

## 1. Prerequisites

1. **Python 3.10+**: Make sure Python is installed.
2. **FFmpeg**: Required by `yt-dlp` to merge high-resolution video streams with audio and convert audio to MP3.
   - **Windows**: Download from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) or run:
     ```powershell
     winget install Gyan.FFmpeg
     ```
   - Verify in terminal with `ffmpeg -version`.

---

## 2. Discord Developer Portal Setup

1. Open the [Discord Developer Portal](https://discord.com/developers/applications).
2. Click **New Application** and give your bot a name.
3. Go to the **Bot** tab on the left:
   - Click **Reset Token** and copy your token.
   - **Crucial for Multi-Server / Public Access**:
     - Ensure **Public Bot** is checked/enabled ✅ (This allows anyone, not just you, to add the bot to any server).
   - Scroll down to **Privileged Gateway Intents** and enable:
     - ✅ **Message Content Intent** (Required to detect links and commands).
4. Go to **Installation** (or **OAuth2 -> URL Generator**):
   - Under **Installation Contexts** / **User Install**:
     - Ensure **Guild Install** is checked.
   - **Scopes**: Check `bot` and `applications.commands`.
   - **Bot Permissions**: Check `Administrator` (or individually: *Send Messages, Attach Files, Read Message History, Embed Links*).
   - Copy the generated invite link to invite the bot to any server.

---

## 3. Creating the Support Server

1. In Discord, click **Add a Server (`+`)** -> **Create My Own**.
2. Name it (e.g., `My Bot Support`).
3. Set up recommended channels:
   - `#announcements` (updates, downtime notices)
   - `#commands-guide` (instructions on how to use `!mp4` and `!mp3`)
   - `#support-tickets` or `#help` (for questions/issues)
4. Right-click the server name -> **Invite People** -> check **Set this link to never expire** -> copy the link.
5. In your Discord Developer Portal application settings:
   - Paste this invite link into the **Support Server** field under **General Information**.
   - Paste it into your bot's `.env` as `SUPPORT_SERVER_INVITE`.

---

## 4. Bot Setup & Execution

1. Open a terminal in this directory:
   ```powershell
   cd C:\Users\ADMIN\.gemini\antigravity\scratch\discord_media_bot
   ```
2. Install Python dependencies (using Python launcher `py`):
   ```powershell
   py -m pip install -r requirements.txt
   ```
3. Create your `.env` file from `.env.example`:
   ```powershell
   copy .env.example .env
   ```
   Open `.env` and fill in:
   ```env
   DISCORD_TOKEN=your_copied_bot_token
   SUPPORT_SERVER_INVITE=https://discord.gg/your_invite_code
   ```
4. Run the bot:
   ```powershell
   py bot.py
   ```

---

## 5. Usage in Discord

- **Slash commands**:
  - `/invite` - Generates a public invite link so anyone can add the bot to other servers.
  - `/mp4 url:<link>` - Downloads highest quality MP4 video.
  - `/mp3 url:<link>` - Extracts 320kbps MP3 audio.
  - `/support` - Displays link to the support server.
- **Prefix commands**:
  - `!invite`
  - `!mp4 <link>`
  - `!mp3 <link>`
  - `!support`

### Note on File Size:
Standard Discord servers have a **25 MB** file upload limit (unless boosted). If a downloaded 4K/1080p video exceeds 25 MB, the bot will warn the user and suggest downloading as MP3 or a shorter clip.

---

## 6. 24/7 Cloud Hosting Options

Because this bot requires **FFmpeg** and temporary disk storage to process high-definition video/audio, the best 24/7 hosting options are:

1. **Option A: Railway.app / Fly.io (Easiest)**
   - Connect your GitHub repository containing this folder.
   - The included `Dockerfile` automatically installs Python, FFmpeg, and dependencies.
   - Add your `DISCORD_TOKEN` in the platform's Environment Variables dashboard.

2. **Option B: Cloud VPS (Oracle Cloud Always-Free / DigitalOcean / Hetzner)**
   - Upload this project directory to `/opt/discord_media_bot`.
   - Run via Docker: `docker compose up -d`
   - Or install natively:
     ```bash
     sudo apt update && sudo apt install -y python3-pip ffmpeg
     pip3 install -r requirements.txt
     sudo cp discord-bot.service /etc/systemd/system/
     sudo systemctl enable --now discord-bot
     ```

