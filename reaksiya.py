import asyncio
import logging
import sys
from datetime import datetime
from random import choice
from aiogram import Bot, Dispatcher, F, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Message, ReactionTypeEmoji, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest

# Bot token
TOKEN = '8076980894:AAGzEbZ7w7PxAZlyjQuI2ELb2RfyqW71W8A'

# Admin configuration
ADMIN_CHAT_ID = 7871012050  # Replace with your admin ID
ADMIN_USERNAME = "@admin_username"  # Replace with admin username
ADMIN_IDS = [ADMIN_CHAT_ID]  # Can add multiple admin IDs

# Initialize bot and dispatcher
dp = Dispatcher()
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

# Database to store channel information
channels_db = {}
# Database to store user information
users_db = {}

# Positive reactions only
POSITIVE_REACTIONS = [
    "👍", "❤", "🔥", "🥰", "👏", "😁", "🎉", "🤩", 
    "🙏", "👌", "😍", "💯", "🤣", "🏆", "🎄", "💅",
    "🆒", "😘", "😎", "🎃", "😇", "🤗", "🫡", "🤝",
    "✍", "💋", "💘", "🦄", "😊", "🌟", "✨", "🙌"
]

# Special reactions for stickers
STICKER_REACTIONS = ["👍", "❤", "😍", "🤩", "🎉", "👏", "🔥"]

# Start command handler
@dp.message(Command("start"))
async def start_command(message: Message):
    # Save user to database
    users_db[message.from_user.id] = {
        'user_id': message.from_user.id,
        'username': message.from_user.username,
        'full_name': message.from_user.full_name,
        'added_date': datetime.now()
    }
    
    buttons = [
        [KeyboardButton(text="📞 Adminga murojaat")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    await message.answer(
        "Salom! Men kanal postlariga avtomatik yaxshi reaksiyalar qo'yuvchi botman.\n\n"
        "Agar savolingiz bo'lsa, quyidagi tugma orqali admin bilan bog'lanishingiz mumkin.",
        reply_markup=reply_markup
    )
# Contact admin handler
@dp.message(F.text == "📞 Adminga murojaat")
async def contact_admin(message: Message):
    await message.answer(
        "✍️ Adminga xabar yuborish uchun matn, rasm, video yoki fayl yuboring.\n\n"
        "Yoki to'g'ridan-to'g'ri @admin ga yozishingiz mumkin.",
        reply_markup=types.ReplyKeyboardRemove()
    )

# User to admin message handler
@dp.message(F.chat.type == "private", ~F.from_user.id.in_(ADMIN_IDS))
async def user_to_admin(message: Message):
    try:
        # Format user info
        user_info = (
            f"👤 Foydalanuvchi: {message.from_user.full_name}\n"
            f"🆔 ID: {message.from_user.id}\n"
            f"📅 Sana: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        )
        
        # Forward different message types to admin
        if message.text:
            caption = f"{user_info}📝 Xabar: {message.text}"
            for admin_id in ADMIN_IDS:
                await bot.send_message(admin_id, caption, reply_markup=types.ForceReply())
        
        elif message.photo:
            caption = f"{user_info}📷 Rasm"
            for admin_id in ADMIN_IDS:
                await bot.send_photo(admin_id, message.photo[-1].file_id, 
                                   caption=caption, 
                                   reply_markup=types.ForceReply())
        
        elif message.video:
            caption = f"{user_info}🎥 Video"
            for admin_id in ADMIN_IDS:
                await bot.send_video(admin_id, message.video.file_id, 
                                   caption=caption, 
                                   reply_markup=types.ForceReply())
        
        elif message.document:
            caption = f"{user_info}📄 Fayl: {message.document.file_name}"
            for admin_id in ADMIN_IDS:
                await bot.send_document(admin_id, message.document.file_id, 
                                      caption=caption, 
                                      reply_markup=types.ForceReply())
        
        await message.answer("✅ Xabaringiz adminlarga yuborildi. Javobni kuting.")
    
    except Exception as e:
        logging.error(f"Xabar yuborishda xato: {e}")
        await message.answer("❌ Xabar yuborishda xatolik yuz berdi. Iltimos, keyinroq urunib ko'ring.")

# Admin reply handler
@dp.message(F.reply_to_message, F.from_user.id.in_(ADMIN_IDS))
async def admin_to_user(message: Message):
    try:
        # Extract original message text
        original_msg = message.reply_to_message.text or message.reply_to_message.caption
        
        if original_msg and "👤 Foydalanuvchi:" in original_msg:
            # Extract user ID
            user_id_line = next(line for line in original_msg.split('\n') if "🆔 ID:" in line)
            user_id = int(user_id_line.split(":")[1].strip())
            
            # Send reply to user
            reply_text = (
                "📩 Admin javobi:\n\n"
                f"{message.text}\n\n"
                "💬 Savolingiz bo'lsa, yana yozishingiz mumkin."
            )
            await bot.send_message(user_id, reply_text)
            await message.answer("✅ Javob foydalanuvchiga yuborildi.")
    
    except Exception as e:
        logging.error(f"Javob yuborishda xato: {e}")
        await message.answer("❌ Javob yuborishda xatolik. Foydalanuvchi ID topilmadi.")


# Admin panel handler
@dp.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id in ADMIN_IDS:
        buttons = [
            [KeyboardButton(text="📊 Statistika")],
            [KeyboardButton(text="📢 Reklama yuborish")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
        await message.answer("👨‍💻 Admin paneliga xush kelibsiz!", reply_markup=reply_markup)

# Statistics handler
@dp.message(F.text == "📊 Statistika")
async def show_statistics(message: Message):
    if message.from_user.id in ADMIN_IDS:
        total_channels = len(channels_db)
        active_channels = sum(1 for data in channels_db.values() if data.get('active', True))
        total_users = len(users_db)
        
        last_active = "Yo'q"
        last_added = "Yo'q"
        
        if channels_db:
            last_active = max(channels_db.values(), key=lambda x: x['last_post'])['last_post'].strftime('%Y-%m-%d %H:%M')
            last_added = max(channels_db.values(), key=lambda x: x['added_date'])['title']
        
        stats_msg = (
            "📊 Bot statistikasi:\n\n"
            f"• 📌 Jami kanallar: {total_channels}\n"
            f"• ✅ Faol kanallar: {active_channels}\n"
            f"• 👥 Foydalanuvchilar: {total_users}\n"
            f"• 📅 Oxirgi aktivlik: {last_active}\n"
            f"• 🆕 Oxirgi qo'shilgan: {last_added}"
        )
        await message.answer(stats_msg)


# 📢 Reklama boshlash
@dp.message(F.text == "📢 Reklama yuborish")
async def start_advertisement(message: Message, state: FSMContext):
    if message.from_user.id in ADMIN_IDS:
        await message.answer(
            "Reklama matnini yuboring. Ushbu reklama:\n"
            "- Barcha faol kanallarga\n"
            "- Botdan foydalanayotgan barcha foydalanuvchilarga\n"
            "yuboriladi.",
            reply_markup=types.ForceReply()
        )
        await state.set_state(Advertisement.waiting_for_text)


# 📢 Reklama jarayoni
@dp.message(Advertisement.waiting_for_text)
async def process_advertisement(message: Message, state: FSMContext):
    if message.from_user.id in ADMIN_IDS:
        ad_text = message.text
        await state.clear()

        success_channels, failed_channels = 0, 0
        success_users, failed_users = 0, 0

        # 📨 Kanallarga reklama yuborish
        async def send_to_channel(channel_id):
            nonlocal success_channels, failed_channels
            try:
                await bot.send_message(channel_id, f"📢 Reklama:\n\n{ad_text}")
                success_channels += 1
            except Exception as e:
                logging.error(f"Kanalga reklama yuborishda xato: {e}")
                failed_channels += 1
                channels_db[channel_id]['active'] = False

        await asyncio.gather(*[send_to_channel(channel) for channel in channels_db if channels_db[channel].get('active', True)])

        # 👥 Foydalanuvchilarga reklama yuborish
        async def send_to_user(user_id):
            nonlocal success_users, failed_users
            try:
                await bot.send_message(user_id, f"📢 Reklama:\n\n{ad_text}")
                success_users += 1
            except Exception as e:
                logging.error(f"Foydalanuvchiga reklama yuborishda xato: {e}")
                failed_users += 1
                users_db.discard(user_id)  # Noaktiv foydalanuvchini o‘chirish

        await asyncio.gather(*[send_to_user(user) for user in users_db])

        # 📊 Hisobot yuborish
        report = (
            "📊 Reklama natijalari:\n\n"
            f"📢 Kanallarga:\n"
            f"✅ Muvaffaqiyatli: {success_channels}\n"
            f"❌ Xatoliklar: {failed_channels}\n\n"
            f"👥 Foydalanuvchilarga:\n"
            f"✅ Muvaffaqiyatli: {success_users}\n"
            f"❌ Xatoliklar: {failed_users}"
        )

        await message.answer(report)


# 📌 Kanalga post tashlanganida avtomatik reaksiya qo‘yish
@dp.channel_post()
async def react_to_channel_post(post: types.Message):
    channel_id = post.chat.id

    # Kanal ma'lumotlarini yangilash yoki qo'shish
    if channel_id not in channels_db:
        channels_db[channel_id] = {
            'channel_id': channel_id,
            'title': post.chat.title,
            'added_date': datetime.now(),
            'active': True,
            'post_count': 1,
            'last_post': datetime.now()
        }
    else:
        channels_db[channel_id]['post_count'] += 1
        channels_db[channel_id]['last_post'] = datetime.now()

    # Reaksiya qo‘shish
    try:
        reaction = choice(STICKER_REACTIONS if post.sticker else POSITIVE_REACTIONS)
        await bot.set_message_reaction(
            chat_id=channel_id,
            message_id=post.message_id,
            reaction=[types.ReactionTypeEmoji(type='emoji', emoji=reaction)],
            is_big=True
        )
    except types.TelegramBadRequest as e:
        if "not enough rights" in str(e).lower():
            channels_db[channel_id]['active'] = False
            logging.warning(f"Kanalda reaksiya qo'yish huquqi yo'q: {channel_id}")
    except Exception as e:
        logging.error(f"Reaksiya qo'yishda xato: {e}")
        
async def main() -> None:
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        stream=sys.stdout
    )
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot to'xtatildi.")
