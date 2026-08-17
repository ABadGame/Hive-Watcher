import os
import requests
import discord
from discord.ext import tasks, commands

intents = discord.Intents.default()
intents.message_content = True  # Required for prefix commands!
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents)

APP_ID = "766370"  # Steam Game ID here
STEAM_API_URL = f"https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid={APP_ID}"

VOICE_CHANNEL_ID = 1538614140224933929
ANNOUNCE_CHANNEL_ID = 1538431540554502204
ROLE_TO_PING_ID = 1538788995960668280

last_player_count = 0
THRESHOLD = 6


def get_steam_player_count():
    try:
        response = requests.get(STEAM_API_URL, timeout=10)
        data = response.json()
        return data["response"].get("player_count", 0)
    except Exception as e:
        print(f"Error fetching Steam API: {e}")
        return None


async def process_player_count(count):
    """Core logic shared between the live Steam loop and manual tests."""
    global last_player_count

    activity = discord.Game(name=f"DL: Bad Blood ({count} online)")
    await bot.change_presence(activity=activity)

    vc_channel = bot.get_channel(VOICE_CHANNEL_ID)
    if vc_channel:
        try:
            await vc_channel.edit(name=f"🔴 DLBB Online: {count}")
        except discord.HTTPException as e:
            print(f"Failed to update voice channel name: {e}")

    if count >= THRESHOLD and last_player_count < THRESHOLD:
        ann_channel = bot.get_channel(ANNOUNCE_CHANNEL_ID)
        if ann_channel:
            ping_target = f"<@&{ROLE_TO_PING_ID}>"
            await ann_channel.send(
                f"🚨 **Critical Mass Reached!** {ping_target}\n"
                f"There are now **{count} players** online in *Dying Light: Bad Blood*!\n"
                f"Jump into the queues or voice channels now!"
            )

    last_player_count = count


@tasks.loop(minutes=10)
async def update_player_count_loop():
    count = get_steam_player_count()
    if count is not None:
        await process_player_count(count)


@update_player_count_loop.before_loop
async def before_update_player_count():
    await bot.wait_until_ready()


# --- SPOOF / TEST COMMAND ---
@bot.command(name="testcount")
@commands.has_permissions(administrator=True)
async def testcount(ctx, fake_count: int):
    """Manually forces the bot to process a fake player count. E.g., !testcount 5"""
    global last_player_count
    last_player_count = 0

    await process_player_count(fake_count)
    await ctx.send(
        f"Successfully simulated player count of **{fake_count}**!", ephemeral=True
    )


@bot.event
async def on_ready():
    print(f"Bot logged in as {bot.user}")
    if not update_player_count_loop.is_running():
        update_player_count_loop.start()


bot.run(os.getenv("DISCORD_TOKEN"))
