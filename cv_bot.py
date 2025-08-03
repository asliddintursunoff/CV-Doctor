# bot.py
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ContextTypes, ConversationHandler
)
from PyPDF2 import PdfReader
import docx
import os
import asyncio
from telegram.constants import ChatAction
import asyncio
import os
from db_users import init_db, save_user
from gemini_ai import generate_response
from telegram.error import BadRequest
from dotenv import load_dotenv

load_dotenv()




# Conversation states
ASK_PHONE, WAIT_CV, ASK_JOB = range(3)
user_data_store = {}

bot_token = os.getenv("BOT_TOKEN")
from telegram.error import BadRequest, RetryAfter


def clean_gemini_text(text: str) -> str:
    import re
    lines = text.splitlines()
    formatted = []
    for line in lines:
        line = line.strip()

        # Remove Markdown bold/italic markers
        line = re.sub(r"\*\*(.*?)\*\*", r"\1", line)
        line = re.sub(r"\*(.*?)\*", r"\1", line)

        # Replace bullet symbol if needed
        if line.startswith("- ") or line.startswith("* "):
            line = "• " + line[2:]

        formatted.append(line)
    return "\n".join(formatted)



async def fake_typing_animation(context, message_obj):
    dots = ["...", "..", "."]
    i = 0
    last_text = None
    try:
        while True:
            new_text = f"🧠 Tahlil qilinmoqda{dots[i % len(dots)]}"

            if new_text != last_text:
                try:
                    await message_obj.edit_text(new_text)
                    last_text = new_text
                except BadRequest as e:
                    if "Message is not modified" not in str(e):
                        raise
                except RetryAfter as e:
                    print(f"Flood control: waiting {e.retry_after} sec")
                    await asyncio.sleep(e.retry_after)

            # Send typing action less frequently (e.g. every 3s)
            if i % 3 == 0:
                try:
                    await context.bot.send_chat_action(chat_id=message_obj.chat_id, action=ChatAction.TYPING)
                except RetryAfter as e:
                    print(f"Typing action flood limit: waiting {e.retry_after} sec")
                    await asyncio.sleep(e.retry_after)

            await asyncio.sleep(1.5)  # ⬅️ Slightly slower to avoid spam
            i += 1
    except asyncio.CancelledError:
        try:
            await message_obj.delete()
        except Exception:
            pass
        raise




def extract_text_from_docx(file_path):
    doc = docx.Document(file_path)
    return "\n".join([p.text for p in doc.paragraphs])

def extract_text_from_pdf(file_path):
    reader = PdfReader(file_path)
    return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[KeyboardButton("📱 Telefon raqamni yuborish", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(
        "👋 Assalomu alaykum!\n"
        "Bu bot sizga rezyumeni tahrirlashda yordam beradi.\n"
        "Davom etish uchun telefon raqamingizni yuboring:",
        reply_markup=reply_markup
    )
    return ASK_PHONE

async def handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    user = update.message.from_user

    if contact:
        save_user(
            telegram_id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            username=user.username,
            phone=contact.phone_number
        )

        await update.message.reply_text("✅ Raqam qabul qilindi.\nIltimos, rezyumeni yuboring (PDF yoki DOCX formatda).")
        return WAIT_CV
    else:
        await update.message.reply_text("📲 Iltimos, telefon raqamingizni tugma orqali yuboring.")
        return ASK_PHONE

async def handle_cv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    if not document or not (document.file_name.endswith('.pdf') or document.file_name.endswith('.docx')):
        await update.message.reply_text("❗ Faqat PDF yoki DOCX fayllarni yuboring.")
        return WAIT_CV

    file = await context.bot.get_file(document.file_id)
    file_path = f"{update.message.from_user.id}_{document.file_name}"
    await file.download_to_drive(file_path)

    try:
        if document.file_name.endswith('.pdf'):
            text = extract_text_from_pdf(file_path)
        else:
            text = extract_text_from_docx(file_path)
    except Exception as e:
        await update.message.reply_text(f"Xatolik yuz berdi: {str(e)}")
        return WAIT_CV
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

    user_data_store[update.message.from_user.id] = {"cv_text": text}
    await update.message.reply_text("💼 Qaysi ish uchun rezyumeni tayyorlamoqchisiz?")
    return ASK_JOB


async def handle_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
    job_title = update.message.text
    user_id = update.message.from_user.id
    cv_text = user_data_store.get(user_id, {}).get("cv_text", "Matn topilmadi.")

    # Send initial animation message
    loading_msg = await update.message.reply_text("🧠 Tahlil qilinmoqda...")

    # Start animation
    animation_task = asyncio.create_task(fake_typing_animation(context, loading_msg))

    try:
        # Run Gemini in thread executor
        loop = asyncio.get_event_loop()
        gemini_output = await loop.run_in_executor(
            None, lambda: generate_response(cv_text, job_title)
        )

    finally:
        # Cancel animation regardless of error/success
        animation_task.cancel()
        try:
            await animation_task
        except asyncio.CancelledError:
            pass

    # Format the output (remove **, *, etc.)
    formatted_output = clean_gemini_text(gemini_output)

    # Telegram limit = 4096 characters. Send in 4000 chunks to be safe.
    chunk_size = 4000
    for i in range(0, len(formatted_output), chunk_size):
        await update.message.reply_text(formatted_output[i:i + chunk_size])

    await update.message.reply_text("♻️ Iltimos, yana bir rezyumeni yuboring (PDF yoki DOCX):")
    return WAIT_CV



async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Jarayon to'xtatildi. /start buyrug'i orqali qayta boshlang.")
    return ConversationHandler.END

def main():
    init_db()

    app = ApplicationBuilder().token(bot_token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_PHONE: [MessageHandler(filters.CONTACT, handle_phone)],
            WAIT_CV: [MessageHandler(filters.Document.ALL, handle_cv)],
            ASK_JOB: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_job)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    print("✅ Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
