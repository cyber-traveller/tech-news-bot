from flask import Flask, request
import json, os, time, requests
from bs4 import BeautifulSoup
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler
from telegram.ext.dispatcher import run_async

# Your Telegram Bot Token
TOKEN = "7415201454:AAHxyKubypsIg-mPvjpI-itGDWw5nFJDQuU"

# Initialize bot and Flask app
bot = Bot(token=TOKEN)
app = Flask(__name__)
dispatcher = Dispatcher(bot, None, workers=1)  # Use at least 1 worker

# File to store subscribed users
USER_DB_FILE = "user_ids.json"

# News source
NEWS_URL = "https://thehackernews.com/"
HEADERS = {"User-Agent": "Mozilla/5.0"}

# Load user IDs from file
def load_users():
    if os.path.exists(USER_DB_FILE):
        with open(USER_DB_FILE, "r") as f:
            return set(json.load(f))
    return set()

# Save user IDs to file
def save_users(user_ids):
    with open(USER_DB_FILE, "w") as f:
        json.dump(list(user_ids), f)

# /start command handler
@run_async
def start(update, context):
    user_id = update.message.chat_id
    user_ids = load_users()
    if user_id not in user_ids:
        user_ids.add(user_id)
        save_users(user_ids)
    context.bot.send_message(chat_id=user_id, text="✅ Subscribed to tech/breach news updates!")

# Function to scrape latest 5 news from TheHackerNews
def scrape_news():
    response = requests.get(NEWS_URL, headers=HEADERS)
    soup = BeautifulSoup(response.content, "html.parser")
    articles = soup.find_all("div", class_="body-post")
    news_items = []
    for article in articles[:5]:
        title = article.find("h2", class_="home-title").text.strip()
        link = article.find("a")["href"]
        summary = article.find("div", class_="home-desc").text.strip()
        news_items.append((title, link, summary))
    return news_items

# Manual broadcast endpoint
@app.route("/broadcast", methods=["GET"])
def broadcast():
    user_ids = load_users()
    news = scrape_news()
    for uid in user_ids:
        for title, link, summary in news:
            msg = f"*{title}*\n{summary}\n[Read more]({link})"
            bot.send_message(chat_id=uid, text=msg, parse_mode="Markdown")
            time.sleep(1)  # Delay to avoid hitting rate limits
    return "✅ Broadcast sent"

# Webhook endpoint for Telegram
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

# Root endpoint for health check
@app.route("/", methods=["GET"])
def index():
    return "🤖 Bot is running"

# Register the start command
dispatcher.add_handler(CommandHandler("start", start))

# Run app with dynamic port for Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render sets the PORT variable
    app.run(host="0.0.0.0", port=port)
