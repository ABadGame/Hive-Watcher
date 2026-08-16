import os
import requests
import discord
from discord.ext import tasks, commands

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

APP_ID = "766370"  # Steam Game ID here
STEAM_API_URL = f"https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid={APP_ID}"
CHANNEL_ID = 1538614140224933929  # Replace with your Voice Channel ID


def get_steam_player_count():
    try:
        response = requests.get(STEAM_API_URL, timeout=10)
        data = response.json()
        return data["response"].get("player_count", 0)
    except Exception as e:
        print(f"Error fetching Steam API: {e}")
        return None

@tasks.loop(minutes=10)
async def update_player_count():
    count = get_steam_player_count()
    if count is not None:
        activity = discord.Game(name=f"DL: Bad Blood ({count} online)")
        await bot.change_presence(activity=activity)
        channel = bot.get_channel(CHANNEL_ID)
        if channel:
            await channel.edit(name=f"🔴 DLBB Online: {count}")

@bot.event
async def on_ready():
    print(f"Bot logged in as {bot.user}")
    update_player_count.start()


bot.run(os.getenv("DISCORD_TOKEN"))
