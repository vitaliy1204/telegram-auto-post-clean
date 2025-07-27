import os
from datetime import datetime
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Bot, InputMediaPhoto
from apscheduler.schedulers.blocking import BlockingScheduler

load_dotenv()

GOOGLE_CREDENTIALS = "google_credentials.json"
SPREADSHEET_NAME = os.getenv("SPREADSHEET_NAME")
SHEET_NAME = os.getenv("SHEET_NAME")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDENTIALS, scope)
client = gspread.authorize(credentials)

def get_data():
    sheet = client.open(SPREADSHEET_NAME).worksheet(SHEET_NAME)
    records = sheet.get_all_records()
    today = datetime.now().strftime('%d.%m.%Y')
    for row in records:
        if row.get("Дата") == today:
            return row
    return None

def post_to_telegram():
    data = get_data()
    if not data:
        print("No data for today")
        return
    
    today = datetime.now()
    header = f"""*Запорізька гімназія N110*
Дата: {today.strftime('%d.%m.%Y')}
Автор: {data.get("Автор", "Невідомо")}
"""
    description = data.get("Опис", "")
    photo_url = data.get("Фото", "")

    bot = Bot(token=TELEGRAM_TOKEN)
    if photo_url:
        bot.send_photo(chat_id=TELEGRAM_CHAT_ID, photo=photo_url, caption=header + description, parse_mode='Markdown')
    else:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=header + description, parse_mode='Markdown')

if __name__ == "__main__":
    post_to_telegram()