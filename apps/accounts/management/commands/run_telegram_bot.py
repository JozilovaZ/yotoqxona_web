"""
Telegram bot orqali ro'yxatdan o'tish.
Ishga tushirish: python manage.py run_telegram_bot
"""
import string
import random
import telebot
from telebot import types
from django.core.management.base import BaseCommand
from accounts.models import User


BOT_TOKEN = '8793216108:AAF2bU1jV88RcfA9dJM5FdUN8qkPsLXWaXA'
ADMIN_CHAT_ID = 8618873404


def generate_password(length=8):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


class Command(BaseCommand):
    help = "Telegram bot orqali talabalar ro'yxatdan o'tishi"

    def handle(self, *args, **options):
        bot = telebot.TeleBot(BOT_TOKEN)

        @bot.message_handler(commands=['start'])
        def start(message):
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            btn = types.KeyboardButton(
                text="Telefon raqamni yuborish",
                request_contact=True
            )
            markup.add(btn)
            bot.send_message(
                message.chat.id,
                "Assalomu alaykum! Yotoqxona tizimiga ro'yxatdan o'tish uchun "
                "telefon raqamingizni yuboring.",
                reply_markup=markup
            )

        @bot.message_handler(content_types=['contact'])
        def handle_contact(message):
            if not message.contact:
                bot.send_message(message.chat.id, "Iltimos, telefon raqamingizni yuboring.")
                return

            phone = message.contact.phone_number
            if not phone.startswith('+'):
                phone = '+' + phone

            first_name = message.contact.first_name or ''
            last_name = message.contact.last_name or ''
            telegram_id = message.from_user.id

            # Tekshirish — allaqachon ro'yxatdan o'tganmi
            existing = User.objects.filter(phone=phone).first()
            if existing:
                bot.send_message(
                    message.chat.id,
                    f"Siz allaqachon ro'yxatdan o'tgansiz!\n\n"
                    f"Login: {existing.username}\n"
                    f"Saytga kiring: https://bekendchi.uz/accounts/login/",
                    reply_markup=types.ReplyKeyboardRemove()
                )
                return

            # Yangi parol yaratish
            password = generate_password()

            # Foydalanuvchi yaratish
            user = User.objects.create_user(
                username=phone,
                password=password,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                role=User.Role.APPLICANT,
            )

            # Foydalanuvchiga yuborish
            bot.send_message(
                message.chat.id,
                f"Ro'yxatdan muvaffaqiyatli o'tdingiz!\n\n"
                f"Login: {phone}\n"
                f"Parol: {password}\n\n"
                f"Saytga kiring: https://bekendchi.uz/accounts/login/\n\n"
                f"Parolni yodda saqlang!",
                reply_markup=types.ReplyKeyboardRemove()
            )

            # Adminga xabar
            try:
                bot.send_message(
                    ADMIN_CHAT_ID,
                    f"Yangi ro'yxatdan o'tish:\n"
                    f"Ism: {first_name} {last_name}\n"
                    f"Telefon: {phone}\n"
                    f"Telegram ID: {telegram_id}"
                )
            except Exception:
                pass

        @bot.message_handler(func=lambda m: True)
        def fallback(message):
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            btn = types.KeyboardButton(
                text="Telefon raqamni yuborish",
                request_contact=True
            )
            markup.add(btn)
            bot.send_message(
                message.chat.id,
                "Ro'yxatdan o'tish uchun telefon raqamingizni yuboring:",
                reply_markup=markup
            )

        self.stdout.write(self.style.SUCCESS('Telegram bot ishga tushdi...'))

        # Adminga bot ishga tushganini xabar berish
        try:
            bot_obj = telebot.TeleBot(BOT_TOKEN)
            bot_obj.send_message(ADMIN_CHAT_ID, "Makon bot ishga tushdi!")
        except Exception:
            pass

        bot.infinity_polling()
