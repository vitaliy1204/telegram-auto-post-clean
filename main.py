import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

сьогодні = datetime.now().strftime('%d.%m.%Y')

header = f"*Запорізька гімназія №110*\nДата: {сьогодні}"

print(header)