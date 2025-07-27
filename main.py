import os
import json
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials
import gspread
from apscheduler.schedulers.blocking import BlockingScheduler
from telegram import Bot, InputMediaPhoto, InputMediaVideo

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")
SPREADSHEET_NAME = os.getenv("SPREADSHEET_NAME")

if not GOOGLE_CREDENTIALS:
    raise ValueError("GOOGLE_CREDENTIALS не вказано у .env файлі")

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDENTIALS, scope)
client = gspread.authorize(credentials)
sheet = client.open(SPREADSHEET_NAME).sheet1

bot = Bot(token=BOT_TOKEN)

def post_from_sheet():
    data = sheet.get_all_records()
    for row in data:
        if not row.get("Опубліковано"):
            text = row.get("Текст", "")
            image = row.get("Зображення", "")
            video = row.get("Відео", "")

            media = []
            if image:
                media.append(InputMediaPhoto(media=image, caption=text))
            elif video:
                media.append(InputMediaVideo(media=video, caption=text))
            else:
                bot.send_message(chat_id=CHAT_ID, text=text)
                sheet.update_cell(data.index(row)+2, len(row)+1, "Так")
                continue

            bot.send_media_group(chat_id=CHAT_ID, media=media)
            sheet.update_cell(data.index(row)+2, len(row)+1, "Так")

scheduler = BlockingScheduler()
scheduler.add_job(post_from_sheet, 'interval', minutes=30)
scheduler.start()