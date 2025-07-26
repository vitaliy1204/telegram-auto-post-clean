import os
import json
import logging
import datetime
import asyncio
from telegram import Bot, InputMediaPhoto, InputMediaVideo
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials

load_dotenv()

TOKEN = os.getenv("TOKEN")
CHANNEL = os.getenv("CHANNEL")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
PHOTO_DIR = "photos"

logging.basicConfig(level=logging.INFO)

def get_today_text():
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
            return None

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

        if idx_date == -1 or idx_text == -1:
            logging.error("Не знайдено обов'язкових колонок 'дата' або 'текст'")
            return None

        lines = []
        for row in records:
            if len(row) <= idx_date:
                continue
            row_date = row[idx_date].strip()
            if row_date != today:
                continue

            text = row[idx_text].strip() if idx_text < len(row) else ""
            extra = row[idx_extra].strip() if idx_extra != -1 and idx_extra < len(row) else ""
            who = row[idx_who].strip() if idx_who != -1 and idx_who < len(row) else ""

            line = " ".join([text, extra, who]).strip()
            lines.append(line)

        if not lines:
            return None

        header = f"*Запорізька гімназія №110*\nДата: {today}"
        full_text = header + "\n\n" + "\n".join(lines).strip()
        return full_text

    except Exception as e:
        logging.error(f"Ошибка при получении текста из таблицы: {e}")
        return None

def load_media(caption):
    media = []
    folder = PHOTO_DIR
    files = sorted([
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if f.lower().endswith(('.jpg', '.jpeg', '.png', '.mp4', '.mov'))
    ])

    first = True
    for file in files:
        if file.lower().endswith(('.mp4', '.mov')):
            media.append(InputMediaVideo(
                media=open(file, 'rb'),
                caption=caption if first else None,
                parse_mode="Markdown" if first else None
            ))
        else:
            media.append(InputMediaPhoto(
                media=open(file, 'rb'),
                caption=caption if first else None,
                parse_mode="Markdown" if first else None
            ))
        first = False
    return media, files

async def main():
    print(f"TOKEN: {TOKEN}")
    print(f"CHANNEL: {CHANNEL}")
    caption = get_today_text()
    if not caption:
        print("📭 Нет текста для", datetime.datetime.today().strftime("%Y-%m-%d"))
        return

    print("📥 Загружаю фото и видео...")
    media, files = load_media(caption)
    bot = Bot(token=TOKEN)

    try:
        for i in range(0, len(media), 10):
            chunk = media[i:i+10]
            if isinstance(chunk[0], (InputMediaPhoto, InputMediaVideo)):
                chunk[0].caption = caption
                chunk[0].parse_mode = "Markdown"
            await bot.send_media_group(chat_id=CHANNEL, media=chunk)
            print(f"✅ Опубликована часть {i//10+1}/{(len(media)-1)//10+1}")
    except Exception as e:
        print(f"❌ Ошибка при публикации: {e}")
        return

    for file in files:
        try:
            os.remove(file)
            print(f"🗑 Удалено: {file}")
        except Exception as e:
            print(f"⚠️ Не удалось удалить {file}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
