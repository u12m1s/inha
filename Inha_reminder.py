import asyncio
import logging
import pytz
from datetime import datetime, timedelta
from icalevents.icalevents import events
from aiogram import Bot

# --- НАСТРОЙКИ ---
API_TOKEN = '8795375959:AAFluCJRMzvGv0OEsHJLpceNpUhb8clTsow'
USER_ID = 741521227  # Ваш ID (числом)
ICAL_URL = 'https://eclass.inha.ac.kr/calendar/export_execute.php?userid=3230&authtoken=60b808d52ea64c117167f97d0b1eec59489a950f&preset_what=all&preset_time=recentupcoming'

TASHKENT_TZ = pytz.timezone('Asia/Tashkent')
bot = Bot(token=API_TOKEN)

async def check_deadlines():
    logging.info("Генерация отчета по дедлайнам...")
    try:
        now_tashkent = datetime.now(TASHKENT_TZ)
        # Загружаем события на ближайшие 10 дней
        upcoming_events = events(url=ICAL_URL, start=now_tashkent, end=now_tashkent + timedelta(days=10))
        
        if not upcoming_events:
            logging.info("Дедлайнов не найдено.")
            return

        # Фильтры для чистоты списка
        STOP_WORDS = ['ppt', 'pptx', 'pdf', 'slides', 'material', 'lecture', '교시', 'viedo', 'viewing']
        WHITE_LIST = ['assignment', 'homework', 'task', 'quiz', 'project', 'lab', 'test']

        # Сортировка по времени
        sorted_events = sorted(upcoming_events, key=lambda x: x.start)

        message_text = "🔔 <b>АКТУАЛЬНЫЕ ДЕДЛАЙНЫ</b>\n━━━━━━━━━━━━━━━\n"
        tasks_found = False

        for event in sorted_events:
            title = event.summary.lower()
            
            # Логика фильтрации
            is_real_task = any(word in title for word in WHITE_LIST)
            is_material = any(word in title for word in STOP_WORDS)

            # Пропускаем, если это материал и в нем нет ключевых слов задания
            if is_material and not is_real_task:
                logging.info(f"Пропущено (материал): {event.summary}")
                continue

            dt = event.start
            if dt.tzinfo is None:
                dt = pytz.utc.localize(dt)
            
            # Устанавливаем дедлайн (обычно до конца указанного дня)
            deadline = datetime(dt.year, dt.month, dt.day, 23, 59, 59, tzinfo=TASHKENT_TZ)
            time_left = deadline - now_tashkent
            
            if time_left.total_seconds() < 0:
                continue

            tasks_found = True
            days = time_left.days
            h, rem = divmod(time_left.seconds, 3600)
            m, _ = divmod(rem, 60)
            
            status = "🔥" if days == 0 else "⏳"
            rem_str = f"{days}д. {h}ч." if days > 0 else f"{h}ч. {m}м."

            message_text += (
                f"{status} <b>{event.summary}</b>\n"
                f"📅 До: {deadline.strftime('%d.%m (%a) 23:59')}\n"
                f"🕒 Осталось: <b>{rem_str}</b>\n"
                f"────────────────\n"
            )

        if tasks_found:
            await bot.send_message(USER_ID, message_text, parse_mode="HTML")
            logging.info("Отчет успешно отправлен.")
        else:
            logging.info("После фильтрации заданий не осталось.")

    except Exception as e:
        logging.error(f"Ошибка при проверке: {e}")

async def scheduler():
    logging.info("Бот запущен. Режим: Активные напоминания (4 часа).")
    while True:
        await check_deadlines()
        # Интервал 4 часа = 14400 секунд
        await asyncio.sleep(14400)

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    asyncio.run(scheduler())
