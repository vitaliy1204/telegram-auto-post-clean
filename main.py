
import os
import json
import logging
import datetime
import asyncio
from telegram import InputMediaPhoto, InputMediaVideo
from telegram.ext import ApplicationBuilder
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from apscheduler.schedulers.asyncio import AsyncIOScheduler

load_dotenv()

TOKEN = os.getenv("TOKEN")
CHANNEL = os.getenv("CHANNEL")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")

logging.basicConfig(level=logging.INFO)

def get_today_text_and_photos():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds_json_str = os.getenv("GOOGLE_SHEET_CREDENTIALS")
        creds_info = json.loads(creds_json_str)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SPREADSHEET_ID).sheet1

        today = datetime.datetime.now().strftime("%Y-%m-%d")
        data = sheet.get_all_values()
        if not data or len(data) < 2:
            return None, []

        headers = data[0]
        records = data[1:]

        def find_index(targets):
            for i, h in enumerate(headers):
                h_clean = h.strip().lower()
                if any(target in h_clean for target in targets):
                    return i
            return -1

        idx_date = find_index(["дата", "date"])
        idx_text = find_index(["текст", "post", "текст поста"])
        idx_extra = find_index(["доп", "дополнительно", "extra"])
        idx_who = find_index(["хто", "кто", "who"])
        idx_link = find_index(["посилання", "посил", "link", "drive"])

        if idx_date == -1 or idx_text == -1:
            logging.error("Не знайдено обов'язкових колонок 'дата' або 'текст'")
            return None, []

        lines = []
        photo_links = []

        for row in records:
            if len(row) <= idx_date:
                continue
            row_date = row[idx_date].strip()
            if row_date != today:
                continue

            text = row[idx_text].strip() if idx_text < len(row) else ""
            extra = row[idx_extra].strip() if idx_extra != -1 and idx_extra < len(row) else ""
            who = row[idx_who].strip() if idx_who != -1 and idx_who < len(row) else ""
            link = row[idx_link].strip() if idx_link != -1 and idx_link < len(row) else ""

            line = " ".join([text, extra, who]).strip()
            if line:
                lines.append(line)
            if link:
                photo_links.append(link)

        if not lines:
            return None, []

        full_text = f"*Запорізька гімназія №110*
Дата: {today}

" + "

".join(lines)
        return full_text, photo_links

    except Exception as e:
        logging.error(f"❌ Помилка при отриманні тексту з таблиці: {e}")
        return None, []

async def post_to_telegram(application):
    caption, photo_links = get_today_text_and_photos()
    if not caption:
        print("📭 Немає тексту для сьогоднішньої дати.")
        return

    media = []
    for i, link in enumerate(photo_links):
        file_id = link.split("/")[-2] if "drive.google.com" in link else link
        file_url = f"https://drive.google.com/uc?id={file_id}"
        if file_url.endswith((".mp4", ".mov")):
            media.append(InputMediaVideo(media=file_url, caption=caption if i == 0 else None, parse_mode="Markdown"))
        else:
            media.append(InputMediaPhoto(media=file_url, caption=caption if i == 0 else None, parse_mode="Markdown"))

    try:
        for i in range(0, len(media), 10):
            chunk = media[i:i+10]
            await application.bot.send_media_group(chat_id=CHANNEL, media=chunk)
            print(f"✅ Опубліковано частину {i//10 + 1}")
    except Exception as e:
        print(f"❌ Помилка при публікації: {e}")

async def main():
    application = ApplicationBuilder().token(TOKEN).build()

    scheduler = AsyncIOScheduler()
    scheduler.add_job(lambda: asyncio.create_task(post_to_telegram(application)), "cron", hour=16, minute=0)
    scheduler.start()

    print("🕓 Планувальник запущено. Чекаємо 16:00...")
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
