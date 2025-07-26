import os
import io
import re
import json
import logging
import datetime
import asyncio
from dotenv import load_dotenv
from telegram import Bot, InputMediaPhoto
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

load_dotenv()

TOKEN = os.getenv("TOKEN")
CHANNEL = os.getenv("CHANNEL")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
PHOTO_DIR = "photos"

logging.basicConfig(level=logging.INFO)


def parse_google_drive_file_id(url):
    match = re.search(r"/d/([a-zA-Z0-9_-]+)", url)
    return match.group(1) if match else None


def download_drive_file(file_id, creds_info, filename):
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, ["https://www.googleapis.com/auth/drive.readonly"])
    service = build("drive", "v3", credentials=creds)
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    with open(filename, "wb") as f:
        f.write(fh.getvalue())
    return filename


def get_today_text_and_photos():
    try:
        creds_info = json.loads(os.getenv("GOOGLE_SHEET_CREDENTIALS"))
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
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
                if any(t in h.strip().lower() for t in targets):
                    return i
            return -1

        idx_date = find_index(["дата", "date"])
        idx_text = find_index(["текст", "post", "текст поста"])
        idx_photo = find_index(["фото", "photo", "drive"])

        if idx_date == -1 or idx_text == -1:
            logging.error("❌ Не знайдено обов'язкових колонок")
            return None, []

        lines = []
        photo_links = []
        for row in records:
            if len(row) <= idx_date:
                continue
            if row[idx_date].strip() != today:
                continue

            text = row[idx_text].strip() if idx_text < len(row) else ""
            photo = row[idx_photo].strip() if idx_photo != -1 and idx_photo < len(row) else ""
            lines.append(text)
            if photo:
                photo_links.append(photo)

        if not lines:
            return None, []

        full_text = f"*Запорізька гімназія №110*"
Дата: {today}

" + "

".join(lines)
        return full_text, photo_links

    except Exception as e:
        logging.error(f"❌ Помилка при отриманні тексту/фото: {e}")
        return None, []


def download_all_photos(photo_links):
    os.makedirs(PHOTO_DIR, exist_ok=True)
    creds_info = json.loads(os.getenv("GOOGLE_SHEET_CREDENTIALS"))
    paths = []

    for link in photo_links:
        file_id = parse_google_drive_file_id(link)
        if file_id:
            filename = os.path.join(PHOTO_DIR, f"{file_id}.jpg")
            try:
                download_drive_file(file_id, creds_info, filename)
                paths.append(filename)
                logging.info(f"✅ Завантажено: {filename}")
            except Exception as e:
                logging.error(f"❌ Не вдалося завантажити {link}: {e}")
    return paths


def build_media_group(caption, photo_paths):
    media = []
    first = True
    for path in photo_paths:
        media.append(InputMediaPhoto(
            media=open(path, 'rb'),
            caption=caption if first else None,
            parse_mode="Markdown" if first else None
        ))
        first = False
    return media


async def send_post():
    logging.info("🚀 Запуск публікації...")
    caption, photo_links = get_today_text_and_photos()
    if not caption:
        logging.info("📭 Немає тексту для сьогоднішньої публікації.")
        return

    photo_paths = download_all_photos(photo_links)
    if not photo_paths:
        logging.info("📭 Немає фото для публікації.")
        return

    bot = Bot(token=TOKEN)
    media = build_media_group(caption, photo_paths)

    try:
        for i in range(0, len(media), 10):
            await bot.send_media_group(chat_id=CHANNEL, media=media[i:i + 10])
        logging.info("✅ Пост опубліковано")
    except Exception as e:
        logging.error(f"❌ Помилка під час публікації: {e}")

    for f in photo_paths:
        try:
            os.remove(f)
        except Exception:
            pass


def schedule_daily_post():
    scheduler = AsyncIOScheduler(timezone="Europe/Kyiv")
    scheduler.add_job(send_post, "cron", hour=16, minute=0)
    scheduler.start()
    logging.info("🕓 Планувальник запущено (щодня о 16:00)")


if __name__ == "__main__":
    schedule_daily_post()
    asyncio.get_event_loop().run_forever()
