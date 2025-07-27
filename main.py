import os
import time
import gspread
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials
from apscheduler.schedulers.background import BackgroundScheduler
from telegram import Bot

# Завантаження .env
load_dotenv()

# Налаштування змінних середовища
BOT_TOKEN = os.getenv("BOT_TOKEN")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Ініціалізація Telegram-бота
bot = Bot(token=BOT_TOKEN)
CHAT_ID = "@your_channel_username"  # Заміни на свій чат або канал

# Підключення до Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDENTIALS, scope)
client = gspread.authorize(credentials)
sheet = client.open_by_key(SPREADSHEET_ID).sheet1

def send_post():
    today = time.strftime("%d.%m.%Y")
    rows = sheet.get_all_values()[1:]  # пропустити заголовки
    text_lines = []
    for row in rows:
        if row and row[0].strip() == today:
            text_lines.append("\n".join(row[1:]))
    if not text_lines:
        print("Сьогодні немає даних для надсилання")
        return
    header = f"*Запорізька гімназія №110*\nДата: {today}\n"
    full_text = header + "\n\n".join(text_lines)
    bot.send_message(chat_id=CHAT_ID, text=full_text, parse_mode='Markdown')
    print("Повідомлення надіслано.")

# Планувальник на 16:00
scheduler = BackgroundScheduler()
scheduler.add_job(send_post, "cron", hour=16, minute=0)
scheduler.start()

print("Бот запущено...")

# Тримати процес живим
while True:
    time.sleep(60)
