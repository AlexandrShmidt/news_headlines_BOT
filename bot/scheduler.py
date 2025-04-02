from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from bot.database import Session, News, Subscription
import logging
from sqlalchemy import or_, extract

logger = logging.getLogger(__name__)

def send_news_to_subscribers(bot):
    """Отправляет свежие новости подписчикам"""
    with Session() as session:
        # Получаем новости за последний час
        news = session.query(News).filter(
            News.published_at >= datetime.utcnow() - timedelta(hours=1)
        ).order_by(News.published_at.desc()).limit(5).all()
        
        if not news:
            logger.info("Нет новых новостей за последний час")
            return

        # Форматируем сообщение
        news_text = "🕒 *Ежечасный дайджест*\n\n" + "\n".join(
            f"• [{n.title}]({n.url}) ({n.published_at.strftime('%H:%M')})" 
            for n in news
        )

        # Получаем активных подписчиков, которым не отправляли в этот час
        subscribers = session.query(Subscription).filter(
            Subscription.is_active == True,
            or_(
                Subscription.last_sent_at == None,
                Subscription.last_sent_at < datetime.utcnow() - timedelta(hours=1)
            )
        ).all()
        
        success_count = 0
        for sub in subscribers:
            try:
                bot.send_message(
                    sub.user_id,
                    news_text,
                    parse_mode="Markdown",
                    disable_web_page_preview=True
                )
                sub.last_sent_at = datetime.utcnow()
                success_count += 1
            except Exception as e:
                logger.error(f"Ошибка отправки для {sub.user_id}: {e}")
                # Если ошибка "чат не найден" - отписываем пользователя
                if "chat not found" in str(e).lower():
                    sub.is_active = False
                
        session.commit()
        logger.info(f"Рассылка завершена. Отправлено: {success_count}/{len(subscribers)}")

def start_scheduler(bot):
    """Запускает планировщик с ежечасной рассылкой"""
    scheduler = BackgroundScheduler()
    
    # Настройка ежечасной рассылки
    scheduler.add_job(
        lambda: send_news_to_subscribers(bot),
        'interval',
        hours=1,  # Интервал в часах
        next_run_time=datetime.now() + timedelta(seconds=10),  # Первый запуск через 10 сек
        misfire_grace_time=300,  # Допустимое время задержки
        coalesce=True  # Объединять пропущенные задания
    )
    
    scheduler.start()
    logger.info("Планировщик запущен в режиме ежечасной рассылки")