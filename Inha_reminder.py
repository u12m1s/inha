import asyncio
import logging
import pytz
from datetime import datetime, timedelta
from icalevents.icalevents import events
from aiogram import Bot

# --- НАСТРОЙКИ ---
API_TOKEN = '8795375959:AAFluCJRMzvGv0OEsHJLpceNpUhb8clTsow'
USER_ID = 741521227
ICAL_URL = 'https://eclass.inha.ac.kr/calendar/export_execute.php?userid=3230&authtoken=60b808d52ea64c117167f97d0b1eec59489a950f&preset_what=all&preset_time=recentupcoming'

TASHKENT_TZ = pytz.timezone('Asia/Tashkent')
bot = Bot(token=API_TOKEN)

async def check_deadlines():
    logging.info("Генерация отчета по дедлайнам...")
    try:
        now_tashkent = datetime.now(TASHKENT_TZ)
        # Берем события на ближайшие 7 дней
        upcoming_events = events(url=ICAL_URL, start=now_tashkent, end=now_tashkent + timedelta(days=7))
        
        if not upcoming_events:
            # Если заданий вообще нет, бот может промолчать или написать "Чисто"
            # await bot.send_message(USER_ID, "✅ На ближайшие 7 дней дедлайнов не найдено!")
            return

        message_text = "🔔 <b>АКТУАЛЬНЫЕ ДЕДЛАЙНЫ</b>\n━━━━━━━━━━━━━━━\n"
        
        # Сортируем события по дате, чтобы ближайшие были сверху
        sorted_events = sorted(upcoming_events, key=lambda x: x.start)

        for event in sorted_events:
            dt = event.start
            if dt.tzinfo is None:
                dt = pytz.utc.localize(dt)
            
            # Дедлайн в системе Inha обычно до конца дня
            deadline = datetime(dt.year, dt.month, dt.day, 23, 59, 59, tzinfo=TASHKENT_TZ)
            time_left = deadline - now_tashkent
            
            if time_left.total_seconds() < 0:
                continue

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

        await bot.send_message(USER_ID, message_text, parse_mode="HTML")
        logging.info("Отчет отправлен успешно.")

    except Exception as e:
        logging.error(f"Ошибка при проверке: {e}")

async def scheduler():
    logging.info("Бот запущен в режиме активных напоминаний.")
    while True:
        await check_deadlines()
        # Ставим интервал 4 часа (14400 секунд)
        # Если хочешь раз в 2 часа — поставь 7200
        await asyncio.sleep(14400)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
    asyncio.run(scheduler())
