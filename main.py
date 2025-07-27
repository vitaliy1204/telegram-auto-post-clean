import os
from dotenv import load_dotenv
from telegram import Bot, InputMediaPhoto, InputMediaVideo
from apscheduler.schedulers.blocking import BlockingScheduler
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GOOGLE_CREDENTIALS = "google_credentials.json"
SPREADSHEET_NAME = os.getenv("SPREADSHEET_NAME")
POST_TIME = os.getenv("POST_TIME", "16:00")

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDENTIALS, scope)
gc = gspread.authorize(credentials)

def create_message():
    today = datetime.now().strftime("%d.%m.%Y")
    header = f"*Запорізька гімназія №110*
Дата: {today}"
    try:
        sheet = gc.open(SPREADSHEET_NAME).sheet1
        rows = sheet.get_all_values()[1:]
        lines = [f"• {row[0]} — {row[1]}" for row in rows if row[0] and row[1]]
        full_text = header + "\n\n" + "\n".join(lines)
        return full_text
    except Exception as e:
        return f"Помилка при читанні таблиці: {e}"

def job():
    bot = Bot(token=TOKEN)
    message = create_message()
    bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")

if __name__ == "__main__":
    job()
