import asyncio
import logging
import pytz
import os
from datetime import datetime, timedelta
from icalevents.icalevents import events
from aiogram import Bot

# --- НАСТРОЙКИ ---
API_TOKEN = '8795375959:AAFluCJRMzvGv0OEsHJLpceNpUhb8clTsow'
USER_ID = 741521227
ICAL_URL = 'https://eclass.inha.ac.kr/calendar/export_execute.php?userid=3230&authtoken=60b808d52ea64c117167f97d0b1eec59489a950f&preset_what=all&preset_time=recentupcoming'
DB_FILE = 'sent_deadlines.txt' # Файл для хранения памяти

TASHKENT_TZ = pytz.timezone('Asia/Tashkent')
bot = Bot(token=API_TOKEN)

# Загружаем уже отправленные ID из файла при запуске
def load_sent_events():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            return set(line.strip() for line in f)
    return set()

# Сохраняем новый ID в файл
def save_sent_event(event_id):
    with open(DB_FILE, 'a') as f:
        f.write(f"{event_id}\n")

sent_events = load_sent_events()

async def check_deadlines():
    logging.info("Проверка e-class...")
    try:
        now_tashkent = datetime.now(TASHKENT_TZ)
        upcoming_events = events(url=ICAL_URL, start=now_tashkent - timedelta(days=1), end=now_tashkent + timedelta(days=10))
        
        for event in upcoming_events:
            event_id = f"{event.uid}_{event.start.isoformat()}"
            
            if event_id not in sent_events:
                dt = event.start
                if dt.tzinfo is None:
                    dt = pytz.utc.localize(dt)
                
                deadline = datetime(dt.year, dt.month, dt.day, 23, 59, 59, tzinfo=TASHKENT_TZ)
                time_left = deadline - now_tashkent
                
                if time_left.total_seconds() < 0:
                    continue

                hours_left = time_left.total_seconds() / 3600
                status = "🔥 <b>СРОЧНО!</b>" if hours_left <= 24 else "📅 <b>НОВЫЙ ДЕДЛАЙН</b>"

                days = time_left.days
                h, rem = divmod(time_left.seconds, 3600)
                m, _ = divmod(rem, 60)
                rem_str = f"{days}д. {h}ч. {m}м." if days > 0 else f"{h}ч. {m}м."

                msg = (
                    f"{status}\n━━━━━━━━━━━━━━━\n"
                    f"📝 <b>{event.summary}</b>\n"
                    f"⏰ <b>До:</b> {deadline.strftime('%d.%m (%a) 23:59')}\n"
                    f"⏳ <b>Осталось:</b> {rem_str}\n━━━━━━━━━━━━━━━"
                )
                
                await bot.send_message(USER_ID, msg, parse_mode="HTML")
                
                # Добавляем в память и сразу записываем на диск
                sent_events.add(event_id)
                save_sent_event(event_id)
                logging.info(f"Отправлено и сохранено: {event.summary}")
    except Exception as e:
        logging.error(f"Ошибка: {e}")

async def scheduler():
    logging.info("Бот запущен (интервал: 1 час)")
    while True:
        await check_deadlines()
        await asyncio.sleep(3600)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
    asyncio.run(scheduler())
