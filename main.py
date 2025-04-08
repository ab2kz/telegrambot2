import os
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from tinydb import TinyDB, Query

BOT_TOKEN = os.getenv("BOT_TOKEN")
DOWNLOAD_LIMIT = 100

db = TinyDB("users.json")
User = Query()

def generate_filename():
    import random, string
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8)) + '.mp4'

def download_video(url):
    filename = generate_filename()
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'merge_output_format': 'mp4',
        'outtmpl': filename,
        'quiet': True,
        'noplaylist': True,
        'no_warnings': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
            if not info or not os.path.exists(filename):
                raise Exception("Download failed or file not found.")
            return filename
        except Exception as e:
            raise Exception(f"yt-dlp error: {str(e)}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    url = update.message.text

    user_data = db.get(User.id == user_id)
    download_count = user_data['downloads'] if user_data else 0

    if user_data and user_data.get('premium'):
        pass
    elif download_count >= DOWNLOAD_LIMIT:
        await update.message.reply_text(
            f"🚫 You have reached your {DOWNLOAD_LIMIT} free downloads. Subscribe to continue.")
        return

    try:
        await update.message.reply_text("⏬ Downloading your video, please wait...")
        file_path = download_video(url)

        with open(file_path, 'rb') as video:
            await update.message.reply_video(video)

        os.remove(file_path)

        if user_data:
            db.update({'downloads': download_count + 1}, User.id == user_id)
        else:
            db.insert({'id': user_id, 'downloads': 1, 'premium': False})

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"👋 Welcome! Send me any social media video link to download. You have {DOWNLOAD_LIMIT} free downloads."
    )

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot is running...")
    app.run_polling()
