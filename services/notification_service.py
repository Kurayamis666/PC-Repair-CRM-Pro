# services/notification_service.py
"""
Сервис уведомлений для PC Repair CRM Pro

✅ Отправка уведомлений через Email и SMS
✅ Шаблоны для разных типов событий
✅ История уведомлений с фильтрацией
✅ Валидация получателей и защита от инъекций
✅ Обработка ошибок и логирование
"""

import re
import smtplib
import html
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field, asdict
from enum import Enum

from core.logger import app_logger
from core.config import Config
from utils.validators import validate_email, validate_phone


# ==================== 🎯 ТИПЫ И КОНСТАНТЫ ====================

class NotificationChannel(Enum):
    """Каналы уведомлений"""
    EMAIL = "email"
    SMS = "sms"
    LOG = "log"  # Только логирование, без внешней отправки


class NotificationType(Enum):
    """Типы уведомлений"""
    REQUEST_CREATED = "request_created"
    REQUEST_UPDATED = "request_updated"
    REQUEST_READY = "request_ready"
    REQUEST_CLOSED = "request_closed"
    LOW_STOCK = "low_stock"
    USER_LOGIN = "user_login"
    SYSTEM_ALERT = "system_alert"


@dataclass
class Notification:
    """Модель уведомления"""
    channel: NotificationChannel
    notification_type: NotificationType
    recipient: str
    subject: str
    body: str
    data: Dict = field(default_factory=dict)
    sent_at: Optional[str] = None
    status: str = "pending"  # pending, sent, failed
    error: Optional[str] = None
    retry_count: int = 0  # ✅ Для будущей реализации retry logic
    
    def to_dict(self) -> Dict[str, any]:
        """Конвертация в словарь для сериализации"""
        return asdict(self)


# 🔧 Конфигурация сервиса
@dataclass
class NotificationServiceConfig:
    """Конфигурация сервиса уведомлений"""
    # Таймауты
    smtp_timeout: int = 30
    sms_timeout: int = 10
    
    # Повторы
    max_retries: int = 3
    retry_delay_seconds: int = 5
    
    # Ограничения
    rate_limit_per_minute: int = 60  # Макс. уведомлений в минуту на один канал
    
    # Часовой пояс для временных меток
    timezone: timezone = timezone.utc
    
    # Флаги
    enable_email: bool = True
    enable_sms: bool = True
    enable_log: bool = True


class NotificationService:
    """
    Сервис отправки уведомлений клиентам и сотрудникам
    
    ✅ Поддержка Email (SMTP) и SMS (заглушка для интеграции)
    ✅ Шаблоны уведомлений с экранированием пользовательских данных
    ✅ Валидация email/phone перед отправкой
    ✅ История уведомлений в памяти (с возможностью расширения на БД)
    ✅ Обработка ошибок с логированием
    
    ⚠️ Ограничения:
    - История хранится в памяти и теряется при перезапуске
    - Нет встроенной очереди/фоновой обработки (вызывайте из background task)
    - SMS-интеграция требует реализации под конкретного провайдера
    
    Пример использования:
        >>> service = NotificationService()
        >>> result = service.notify_client(
        ...     client_data={"email": "user@example.com", "name": "Иван"},
        ...     request_data={"id": 123, "status": "ready"},
        ...     notification_type=NotificationType.REQUEST_READY
        ... )
        >>> print(result)  # {'email': True}
    """
    
    def __init__(
        self,
        smtp_config: Optional[Dict] = None,
        sms_config: Optional[Dict] = None,
        config: Optional[NotificationServiceConfig] = None,
    ):
        """
        Инициализация сервиса
        
        Args:
            smtp_config: Настройки SMTP сервера (из Config.SMTP_CONFIG по умолчанию)
            sms_config: Настройки SMS API (из Config.SMS_CONFIG по умолчанию)
            config: Расширенная конфигурация сервиса
        """
        self.smtp_config = smtp_config or getattr(Config, 'SMTP_CONFIG', {})
        self.sms_config = sms_config or getattr(Config, 'SMS_CONFIG', {})
        self.config = config or NotificationServiceConfig()
        
        self.notification_history: List[Notification] = []
        self._rate_limit_tracker: Dict[str, List[float]] = {}  # Для простого rate limiting
        
        app_logger.info("📧 NotificationService initialized")
    
    # ==================== 📤 ОТПРАВКА УВЕДОМЛЕНИЙ ====================
    
    def notify_client(
        self,
        client_data: Dict[str, str],
        request_data: Dict[str, Union[str, int, float]],
        notification_type: NotificationType,
        channels: Optional[List[NotificationChannel]] = None,
    ) -> Dict[str, bool]:
        """
        Отправка уведомления клиенту
        
        ✅ Валидация email/phone перед отправкой
        ✅ Экранирование пользовательских данных в шаблонах
        ✅ Обработка ошибок без падения всего сервиса
        
        Args:
            client_data: Данные клиента ({'email': ..., 'phone': ..., 'name': ...})
            request_data: Данные заявки ({'id': ..., 'status': ..., 'total_cost': ...})
            notification_type: Тип уведомления
            channels: Каналы для отправки (по умолчанию EMAIL + SMS если настроены)
            
        Returns:
            Dict[str, bool]: Результат по каждому каналу {'email': True, 'sms': False}
        """
        # ✅ Определяем каналы по умолчанию
        if channels is None:
            channels = []
            if self.config.enable_email and self.smtp_config:
                channels.append(NotificationChannel.EMAIL)
            if self.config.enable_sms and self.sms_config:
                channels.append(NotificationChannel.SMS)
            if self.config.enable_log:
                channels.append(NotificationChannel.LOG)
        
        results: Dict[str, bool] = {}
        client_name = client_data.get("name", "Клиент")
        
        # ✅ Подготовка шаблонов с экранированием
        templates = self._get_notification_templates(
            notification_type, client_data, request_data
        )
        
        for channel in channels:
            # ✅ Проверка лимитов
            if not self._check_rate_limit(channel.value):
                app_logger.warning(f"⚠️ Rate limit exceeded for {channel.value}")
                results[channel.value] = False
                continue
            
            try:
                if channel == NotificationChannel.EMAIL:
                    email = client_data.get("email", "").strip()
                    if not email or not validate_email(email)[0]:
                        app_logger.warning(f"⚠️ Invalid email for notification: {email}")
                        results["email"] = False
                        continue
                    
                    results["email"] = self._send_email(
                        to_email=email,
                        subject=templates["email_subject"],
                        body=templates["email_body"],
                        is_html=True,
                    )
                    
                elif channel == NotificationChannel.SMS:
                    phone = client_data.get("phone", "").strip()
                    if not phone or not validate_phone(phone, "ru")[0]:
                        app_logger.warning(f"⚠️ Invalid phone for notification: {phone}")
                        results["sms"] = False
                        continue
                    
                    results["sms"] = self._send_sms(
                        to_phone=phone,
                        message=templates["sms_body"],
                    )
                    
                elif channel == NotificationChannel.LOG:
                    self._log_notification(notification_type, client_data, request_data)
                    results["log"] = True
                    
            except Exception as e:
                app_logger.exception(f"❌ Failed to send {channel.value} notification: {e}")
                results[channel.value] = False
                
                # ✅ Записываем ошибку в историю
                self._add_to_history(
                    channel=channel,
                    notification_type=notification_type,
                    recipient=client_data.get("email") or client_data.get("phone", ""),
                    subject=templates.get("email_subject", ""),
                    body=templates.get("email_body", "")[:200],
                    status="failed",
                    error=str(e),
                )
        
        return results
    
    def _check_rate_limit(self, channel: str) -> bool:
        """
        Простая проверка rate limiting
        
        ✅ Возвращает False если превышен лимит уведомлений в минуту
        """
        now = datetime.now(self.config.timezone).timestamp()
        window_start = now - 60  # 1 минута
        
        # Очищаем старые записи
        if channel not in self._rate_limit_tracker:
            self._rate_limit_tracker[channel] = []
        self._rate_limit_tracker[channel] = [
            t for t in self._rate_limit_tracker[channel] if t > window_start
        ]
        
        # Проверяем лимит
        if len(self._rate_limit_tracker[channel]) >= self.config.rate_limit_per_minute:
            return False
        
        # Добавляем текущий запрос
        self._rate_limit_tracker[channel].append(now)
        return True
    
    # ==================== 📋 ШАБЛОНЫ УВЕДОМЛЕНИЙ ====================
    
    def _get_notification_templates(
        self, 
        notification_type: NotificationType, 
        client_data: Dict, 
        request_data: Dict
    ) -> Dict[str, str]:
        """
        Получение шаблонов уведомления с экранированием данных
        
        ✅ html.escape() для защиты от XSS в HTML-шаблонах
        ✅ Fallback шаблон для неизвестных типов уведомлений
        """
        # ✅ Безопасное получение данных с дефолтами
        client_name = html.escape(str(client_data.get("name", "Клиент")))
        request_id = html.escape(str(request_data.get("id", "?")))
        status = html.escape(str(request_data.get("status", "")))
        cost = request_data.get("total_cost", 0)
        cost_formatted = f"{cost:.2f}" if isinstance(cost, (int, float)) else str(cost)
        
        templates = {
            NotificationType.REQUEST_CREATED: {
                "email_subject": f"Заявка #{request_id} принята в работу",
                "email_body": f"""
                <h2>Здравствуйте, {client_name}!</h2>
                <p>Ваша заявка #{request_id} принята в работу.</p>
                <p><strong>Статус:</strong> {status}</p>
                <p><strong>Предварительная стоимость:</strong> {cost_formatted} ₽</p>
                <p>Мы свяжемся с вами для уточнения деталей.</p>
                <hr>
                <small>PC Repair CRM Pro</small>
                """,
                "sms_body": f"Заявка #{request_id} принята. Статус: {status}. PC Repair",
            },
            NotificationType.REQUEST_UPDATED: {
                "email_subject": f"Обновление по заявке #{request_id}",
                "email_body": f"""
                <h2>Здравствуйте, {client_name}!</h2>
                <p>Статус вашей заявки #{request_id} обновлён.</p>
                <p><strong>Новый статус:</strong> {status}</p>
                <p>Актуальная информация доступна в личном кабинете.</p>
                <hr>
                <small>PC Repair CRM Pro</small>
                """,
                "sms_body": f"Заявка #{request_id}: новый статус - {status}. PC Repair",
            },
            NotificationType.REQUEST_READY: {
                "email_subject": f"Заявка #{request_id} выполнена!",
                "email_body": f"""
                <h2>Здравствуйте, {client_name}!</h2>
                <p>🎉 Ваша заявка #{request_id} выполнена и готова к выдаче!</p>
                <p><strong>Итоговая стоимость:</strong> {cost_formatted} ₽</p>
                <p>Пожалуйста, посетите наш сервисный центр для получения устройства.</p>
                <p><em>Режим работы: Пн-Пт 9:00-19:00, Сб 10:00-16:00</em></p>
                <hr>
                <small>PC Repair CRM Pro</small>
                """,
                "sms_body": f"✅ Заявка #{request_id} готова! Сумма: {cost_formatted}₽. Ждём вас. PC Repair",
            },
            NotificationType.REQUEST_CLOSED: {
                "email_subject": f"Заявка #{request_id} закрыта",
                "email_body": f"""
                <h2>Здравствуйте, {client_name}!</h2>
                <p>Ваша заявка #{request_id} успешно закрыта.</p>
                <p>Спасибо что выбрали наш сервис!</p>
                <hr>
                <small>PC Repair CRM Pro</small>
                """,
                "sms_body": f"Заявка #{request_id} закрыта. Спасибо за выбор PC Repair!",
            },
            NotificationType.LOW_STOCK: {
                "email_subject": f"⚠️ Низкий остаток: {html.escape(str(request_data.get('part_name', 'Запчасть')))}",
                "email_body": f"""
                <h2>Предупреждение о запасах</h2>
                <p>Запчасть "{html.escape(str(request_data.get('part_name', '')))}" имеет низкий остаток.</p>
                <p><strong>Текущий остаток:</strong> {request_data.get('quantity', 0)}</p>
                <p><strong>Минимальный порог:</strong> {request_data.get('min_stock', 5)}</p>
                <p>Рекомендуется оформить заказ у поставщика.</p>
                """,
                "sms_body": f"⚠️ Низкий остаток: {request_data.get('part_name', '')} ({request_data.get('quantity', 0)} шт.)",
            },
        }
        
        # ✅ Fallback для неизвестных типов
        default_templates = {
            "email_subject": f"Уведомление от PC Repair CRM",
            "email_body": f"<p>Уведомление для {client_name}</p><p>{html.escape(str(request_data))}</p>",
            "sms_body": f"PC Repair: {str(request_data)[:100]}",
        }
        
        return templates.get(notification_type, default_templates)
    
    # ==================== 📧 EMAIL ОТПРАВКА ====================
    
    def _send_email(
        self, 
        to_email: str, 
        subject: str, 
        body: str, 
        is_html: bool = True,
        retry_count: int = 0,
    ) -> bool:
        """
        Отправка email через SMTP с обработкой ошибок и повторами
        
        ✅ Валидация конфига перед подключением
        ✅ Корректное использование smtp_config (не sms_config!)
        ✅ Обработка специфичных SMTP ошибок
        
        Args:
            to_email: Email получателя
            subject: Тема письма
            body: Тело письма
            is_html: Использовать HTML-форматирование
            retry_count: Текущая попытка (для внутренней рекурсии)
            
        Returns:
            bool: True если отправка успешна
        """
        # ✅ Проверка конфигурации
        if not self.smtp_config or not self.config.enable_email:
            app_logger.warning("⚠️ Email notifications disabled or not configured")
            return False
        
        if not validate_email(to_email)[0]:
            app_logger.error(f"❌ Invalid email address: {to_email}")
            return False
        
        try:
            # ✅ Создание MIME-сообщения
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.smtp_config.get("from_email", "noreply@pcrepair.local")
            msg["To"] = to_email
            msg["Date"] = datetime.now(self.config.timezone).strftime("%a, %d %b %Y %H:%M:%S %z")
            
            # ✅ Добавление тела письма
            if is_html:
                msg.attach(MIMEText(body, "html", "utf-8"))
            else:
                # ✅ Очистка от HTML тегов для text/plain
                text_body = re.sub(r"<[^>]+>", "", body)
                msg.attach(MIMEText(text_body, "plain", "utf-8"))
            
            # ✅ Подключение к SMTP серверу
            host = self.smtp_config.get("host")
            port = self.smtp_config.get("port", 465 if self.smtp_config.get("use_tls") else 587)
            use_tls = self.smtp_config.get("use_tls", True)
            
            if not host:
                raise ValueError("SMTP host not configured")
            
            if use_tls:
                server = smtplib.SMTP_SSL(host, port, timeout=self.config.smtp_timeout)
            else:
                server = smtplib.SMTP(host, port, timeout=self.config.smtp_timeout)
                server.starttls()
            
            # ✅ Аутентификация
            # 🔧 ИСПРАВЛЕНО: smtp_config вместо sms_config!
            username = self.smtp_config.get("username")
            password = self.smtp_config.get("password")
            
            if username and password:
                server.login(username, password)  # ✅ ИСПРАВЛЕНО: smtp_config["password"]
            
            # ✅ Отправка
            server.send_message(msg)
            server.quit()
            
            app_logger.info(f"📧 Email sent to {to_email}: {subject}")
            
            # ✅ Запись в историю
            self._add_to_history(
                channel=NotificationChannel.EMAIL,
                notification_type=NotificationType.SYSTEM_ALERT,
                recipient=to_email,
                subject=subject,
                body=body[:200] + "...",
                status="sent",
            )
            
            return True
            
        except smtplib.SMTPAuthenticationError:
            app_logger.error("❌ SMTP authentication failed: check username/password")
            return False
        except smtplib.SMTPConnectError as e:
            app_logger.error(f"❌ SMTP connection failed: {e}")
            return False
        except smtplib.SMTPException as e:
            # ✅ Retry logic для временных ошибок
            if retry_count < self.config.max_retries:
                import time
                delay = self.config.retry_delay_seconds * (2 ** retry_count)
                app_logger.warning(f"⚠️ SMTP error, retrying in {delay}s (attempt {retry_count + 1})")
                time.sleep(delay)
                return self._send_email(to_email, subject, body, is_html, retry_count + 1)
            
            app_logger.error(f"❌ SMTP error after {self.config.max_retries} retries: {e}")
            return False
        except Exception as e:
            app_logger.exception(f"❌ Unexpected email error: {e}")
            return False
    
    # ==================== 📱 SMS ОТПРАВКА ====================
    
    def _send_sms(self, to_phone: str, message: str, retry_count: int = 0) -> bool:
        """
        Отправка SMS через внешний API
        
        ⚠️ Заглушка: требуется интеграция с реальным провайдером (SMS.ru, Twilio, etc.)
        
        Args:
            to_phone: Номер телефона в международном формате (+7...)
            message: Текст сообщения (до 160 символов для одного SMS)
            retry_count: Текущая попытка (для внутренней рекурсии)
            
        Returns:
            bool: True если отправка успешна (в заглушке — всегда)
        """
        # ✅ Проверка конфигурации
        if not self.sms_config or not self.config.enable_sms:
            app_logger.warning("⚠️ SMS notifications disabled or not configured")
            return False
        
        # ✅ Валидация телефона
        valid, error = validate_phone(to_phone, "ru")
        if not valid:
            app_logger.error(f"❌ Invalid phone number: {to_phone} ({error})")
            return False
        
        # ✅ Ограничение длины сообщения
        if len(message) > 160:
            app_logger.warning(f"⚠️ SMS message truncated from {len(message)} to 160 chars")
            message = message[:160]
        
        try:
            # 🔧 ЗАГЛУШКА: Здесь должна быть интеграция с реальным SMS API
            # Пример для SMS.ru:
            #
            # import requests
            # response = requests.post(
            #     "https://sms.ru/sms/send",
            #     data={
            #         "api_id": self.sms_config.get("api_key"),
            #         "to": to_phone,
            #         "msg": message,
            #         "from": self.sms_config.get("sender_name", "PCRepair"),
            #         "json": 1,
            #     },
            #     timeout=self.config.sms_timeout,
            # )
            # result = response.json()
            # return result.get("status_code") == 100
            
            # ✅ Демо-режим: логирование без реальной отправки
            app_logger.info(f"📱 [SMS DEMO] Would send to {to_phone}: {message}")
            
            # ✅ Запись в историю (в демо-режиме считаем успешным)
            self._add_to_history(
                channel=NotificationChannel.SMS,
                notification_type=NotificationType.SYSTEM_ALERT,
                recipient=to_phone,
                subject="",
                body=message,
                status="sent",  # ⚠️ В продакшене — только после подтверждения от API
            )
            
            return True  # ⚠️ В продакшене — возврат результата от API
            
        except Exception as e:
            # ✅ Retry logic для временных ошибок сети
            if retry_count < self.config.max_retries:
                import time
                delay = self.config.retry_delay_seconds * (2 ** retry_count)
                app_logger.warning(f"⚠️ SMS error, retrying in {delay}s (attempt {retry_count + 1})")
                time.sleep(delay)
                return self._send_sms(to_phone, message, retry_count + 1)
            
            app_logger.exception(f"❌ SMS sending error after retries: {e}")
            return False
    
    # ==================== 📋 ИСТОРИЯ И ЛОГИРОВАНИЕ ====================
    
    def _add_to_history(
        self,
        channel: NotificationChannel,
        notification_type: NotificationType,
        recipient: str,
        subject: str,
        body: str,
        status: str,
        error: Optional[str] = None,
        data: Optional[Dict] = None,
    ) -> None:
        """Добавление уведомления в историю"""
        notification = Notification(
            channel=channel,
            notification_type=notification_type,
            recipient=recipient,
            subject=subject,
            body=body,
            data=data or {},
            sent_at=datetime.now(self.config.timezone).isoformat(),
            status=status,
            error=error,
        )
        self.notification_history.append(notification)
    
    def _log_notification(
        self, 
        notification_type: NotificationType, 
        client_data: Dict, 
        request_data: Dict
    ) -> None:
        """Логирование уведомления (канал LOG)"""
        app_logger.info(
            f"🔔 Notification [{notification_type.value}] for {client_data.get('name')}: {request_data}"
        )
    
    def log_user_login(self, username: str, user_agent: Optional[str] = None) -> None:
        """Логирование входа пользователя"""
        ua_info = f" ({user_agent[:50]}...)" if user_agent and len(user_agent) > 50 else (f" ({user_agent})" if user_agent else "")
        app_logger.info(f"🔐 User login: {username}{ua_info}")
    
    def get_notification_history(
        self,
        limit: int = 50,
        channel: Optional[NotificationChannel] = None,
        status: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, any]]:
        """
        Получение истории уведомлений с фильтрацией
        
        Args:
            limit: Максимальное количество записей
            channel: Фильтр по каналу
            status: Фильтр по статусу (pending/sent/failed)
            start_date: Фильтр по дате начала (ISO format)
            end_date: Фильтр по дате окончания (ISO format)
            
        Returns:
            List[Dict]: Список уведомлений в виде словарей
        """
        history = self.notification_history.copy()
        
        # ✅ Фильтрация
        if channel:
            history = [n for n in history if n.channel == channel]
        if status:
            history = [n for n in history if n.status == status]
        if start_date:
            history = [n for n in history if n.sent_at and n.sent_at >= start_date]
        if end_date:
            history = [n for n in history if n.sent_at and n.sent_at <= end_date]
        
        # ✅ Сортировка: новые сначала (безопасная сортировка с None)
        history.sort(key=lambda x: x.sent_at or "", reverse=True)
        
        # ✅ Конвертация в dict + ограничение
        return [n.to_dict() for n in history[:limit]]
    
    def clear_history(self, older_than_days: int = 30) -> int:
        """
        Очистка старой истории уведомлений
        
        ⚠️ Внимание: история хранится в памяти и теряется при перезапуске
        
        Args:
            older_than_days: Удалять уведомления старше этого количества дней
            
        Returns:
            int: Количество удалённых записей
        """
        cutoff = datetime.now(self.config.timezone) - timedelta(days=older_than_days)
        cutoff_str = cutoff.isoformat()
        
        original_count = len(self.notification_history)
        self.notification_history = [
            n for n in self.notification_history 
            if n.sent_at and n.sent_at > cutoff_str
        ]
        
        removed = original_count - len(self.notification_history)
        if removed > 0:
            app_logger.info(f"🧹 Cleared {removed} old notifications from history")
        
        return removed
    
    def get_statistics(self) -> Dict[str, any]:
        """
        Статистика по отправленным уведомлениям
        
        Returns:
            Dict: Статистика по каналам и статусам
        """
        stats = {
            "total": len(self.notification_history),
            "by_channel": {},
            "by_status": {},
            "by_type": {},
        }
        
        for notification in self.notification_history:
            # По каналам
            channel_key = notification.channel.value
            stats["by_channel"][channel_key] = stats["by_channel"].get(channel_key, 0) + 1
            
            # По статусам
            status_key = notification.status
            stats["by_status"][status_key] = stats["by_status"].get(status_key, 0) + 1
            
            # По типам
            type_key = notification.notification_type.value
            stats["by_type"][type_key] = stats["by_type"].get(type_key, 0) + 1
        
        return stats