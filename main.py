import logging
import os
import requests
from datetime import datetime
from telegram import Update, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Group ID
ALLOWED_GROUP_ID = -1002661209994

# Format timestamp
def format_timestamp(timestamp):
    try:
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%d/%m/%Y, %H:%M:%S")
    except:
        return "N/A"

# Get player info
def get_player_info(uid):
    try:
        url = f"https://gmg-20099-ff-id-info.vercel.app/api/player-info?id={uid}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            basic_info = data.get("data", {}).get("basic_info", {})
            name = basic_info.get("name", "Unknown")
            level = basic_info.get("level", "N/A")
            return name, level
    except Exception as e:
        logger.error(f"Error fetching player info: {e}")
    return "Unknown", "N/A"

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.id != ALLOWED_GROUP_ID:
        await update.message.reply_text("This bot only works in the designated group.")
        return
    await update.message.reply_text(
        "Welcome! Use:\n"
        "/search <player name> - to search for Free Fire players\n"
        "/spam <Free Fire UID> - to send spam requests"
    )

# /search command
async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.id != ALLOWED_GROUP_ID:
        await update.message.reply_text("This bot only works in the designated group.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /search <player name>")
        return

    name = " ".join(context.args)
    msg = await update.message.reply_text("Please wait, searching your name globally...")
    url = f"https://ariflexlabs-search-api.vercel.app/search?name={name}"

    try:
        response = requests.get(url)
        regions = response.json()
        logger.info(f"API Response: {regions}")

        if not regions or not isinstance(regions, list):
            await msg.edit_text("No results found.")
            return

        message = "Search Results by GMG:\n"
        all_players = []

        for region_data in regions:
            players = region_data.get("result", {}).get("player", [])
            for p in players:
                all_players.append({
                    "nickname": p.get("nickname", "N/A"),
                    "uid": p.get("accountId", "N/A"),
                    "region": p.get("region", region_data.get("region", "N/A")).upper(),
                    "level": p.get("level", "N/A"),
                    "lastLogin": format_timestamp(p.get("lastLogin", 0))
                })

        if not all_players:
            await msg.edit_text("No players found.")
            return

        for i, p in enumerate(all_players[:10]):
            prefix = "└─" if i == len(all_players[:10]) - 1 else "├─"
            message += (
                f"\n{prefix} *Nickname:* `{p['nickname']}`\n"
                f"   ├─ *UID:* `{p['uid']}`\n"
                f"   ├─ *Region:* `{p['region']}`\n"
                f"   ├─ *Level:* `{p['level']}`\n"
                f"   └─ *Last Login:* `{p['lastLogin']}`\n"
            )

        await msg.edit_text(message, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error during search: {str(e)}")
        await msg.edit_text("Something went wrong. Please try again later.")

# /spam command
async def spam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.id != ALLOWED_GROUP_ID:
        await update.message.reply_text("This bot only works in the designated group.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("Usage: /spam <Free Fire UID>")
        return

    uid = context.args[0]
    if not uid.isdigit():
        await update.message.reply_text("Invalid UID. Please enter a numeric UID.")
        return

    name, level = get_player_info(uid)
    processing_message = await update.message.reply_text("⏳ Processing your request...")

    spam_url = f"https://spam-ff-gmg.vercel.app/send_requests?uid={uid}"

    try:
        response = requests.get(spam_url)
        if response.status_code == 200:
            data = response.json()
            success = data.get("success_count", 0)

            await processing_message.edit_text(
                f"PLAYER NAME : {name}\n"
                f"✅ SUCCESSFULLY SENT\n"
                f"PLAYER LEVEL : {level}\n"
                f"REQUEST SENT : {success} REQUESTS"
            )
        else:
            await processing_message.edit_text(f"Failed to send request. Status Code: {response.status_code}")
    except Exception as e:
        await processing_message.edit_text(f"Error: {str(e)}")

# Main
if __name__ == "__main__":
    TOKEN = os.getenv("7720805771:AAGnv-0BPJN5TuxjZc1tVPlF-8SYUf7dGzE")
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("search", search_command))
    app.add_handler(CommandHandler("spam", spam))

    async def on_startup(app):
        await app.bot.set_my_commands([
            BotCommand("start", "Start the bot"),
            BotCommand("search", "Search Free Fire player"),
            BotCommand("spam", "Send spam requests")
        ])

    print("Bot is running...")
    app.run_polling(on_startup=on_startup)
