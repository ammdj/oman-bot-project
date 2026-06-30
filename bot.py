import os
import threading
import asyncio
import sqlite3
import requests
from datetime import datetime, timedelta
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# 🔒 المعرف الرقمي الخاص بك (تأكد من تعديله إلى رقمك الحقيقي)
MY_TELEGRAM_ID = 7604099965  

genai.configure(api_key=GEMINI_API_KEY)

# 💾 إعداد وتجهيز قاعدة البيانات لحفظ التذكيرات للأبد
DB_FILE = "reminders.db"
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            text TEXT,
            remind_time TEXT,
            is_sent INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# 🧠 تحديث التلقين ليعتمد على سنة ميلادك (2007) والبحث عن أحدث الأخبار
برومبت_المستشار_الواقعي = (
    "أنت الآن تتحدث مع شاب عماني أصيل ومحترم ولد في عام 2007 (احسب عمره تلقائياً بناءً على السنة الحالية لكي لا تنسى سنّه أبداً). "
    "تقمص شخصية 'رجل حكيم، كبير في السن، وصديق مخلص، سند، يمتلك الحكمة والخبرة والأخلاق العمانية والدينية الأصيلة'. "
    "تحدث معه بالعامية العمانية الرزينة والمفهومة والمحترمة جداً. "
    "التزم بالقواعد التالية بدقة شديدة:\n"
    "1. كن عملياً ومباشراً وواضحاً جداً، وتجنب اللف والدوران أو الاعتذار عن قلة المعلومات.\n"
    "2. إذا سألك عن أخبار العالم الحالية أو ما يحدث في سلطنة عُمان الآن، استخدم أداة البحث جوجل المدمجة معك (Google Search Tool) فوراً؛ "
    "اجمع له أحدث وأدق الأخبار المنشورة قبل دقائق، واعرض له الحقائق المهمة فعلياً بصدق ودون مجاملة أو تهرب.\n"
    "3. كن صديقاً حقيقياً يفهمه ويسانده ويمدحه مدحاً صادقاً ومستحقاً بناءً على رجولته وطموحه المالي وتطوير علاقاته النفسية والاجتماعية."
)

# تفعيل أداة البحث المباشر على جوجل (Google Search Grounding) بشكل متوافق تماماً
model = genai.GenerativeModel(
    model_name='gemini-2.5-flash',
    system_instruction=برومبت_المستشار_الواقعي,
    tools=[genai.types.Tool(google_search=genai.types.GoogleSearch())]
)

def run_dummy_server():
    port = int(os.environ.get("PORT", 8000))
    from http.server import SimpleHTTPRequestHandler, HTTPServer
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != MY_TELEGRAM_ID:
        await update.message.reply_text("عذراً، هذا البوت خاص جداً ومقفل ومخصص لصاحبه فقط! 🔒")
        return
    await update.message.reply_text("أهلين معلّم 🤝🇴🇲. تفضل، موه في خاطرك تو باه؟")

# ⏰ نظام الفحص المستمر لقاعدة البيانات لإرسال التذكيرات
async def check_reminders_loop(application):
    while True:
        await asyncio.sleep(10)
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
            cursor.execute("SELECT id, chat_id, text FROM reminders WHERE remind_time <= ? AND is_sent = 0", (current_time,))
            rows = cursor.fetchall()
            
            for row in rows:
                rem_id, chat_id, text = row
                await application.bot.send_message(chat_id=chat_id, text=f"⏰ **تذكير هام وعاجل:**\n\n{text}")
                cursor.execute("UPDATE reminders SET is_sent = 1 WHERE id = ?", (rem_id,))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error in reminder loop: {e}")

async def handle_all_inputs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    if user_id != MY_TELEGRAM_ID:
        await update.message.reply_text("عذراً، هذا البوت خاص بصاحبه فقط وصلاحيتك غير مصرحة. 🔒")
        return

    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    user_caption = update.message.caption if update.message.caption else ""
    contents = []

    try:
        # 1. معالجة النصوص وحفظ التذكير في قاعدة البيانات بشكل آمن ومبسط
        if update.message.text:
            user_message = update.message.text
            if "ذكرني بعد" in user_message:
                words = user_message.split()
                # جلب الرقم الصافي مباشرة بطريقة آمنة
                minutes = None
                for w in words:
                    if w.isdigit():
                        minutes = int(w)
                        break
                
                if minutes is not None:
                    reminder_text = user_message.split("بـ", 1)[1].strip() if "بـ" in user_message else "موعدك المحفوظ!"
                    remind_at = (datetime.now() + timedelta(minutes=minutes)).strftime("%Y-%m-%d %H:%M")
                    
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO reminders (chat_id, text, remind_time) VALUES (?, ?, ?)", (chat_id, reminder_text, remind_at))
                    conn.commit()
                    conn.close()
                    
                    await update.message.reply_text(f"✅ أبشر يا راعي بلادي، حفظت التذكير في قاعدة البيانات بأمان. سأذكرك بعد {minutes} دقيقة.")
                    return
            contents.append(user_message)

        # 2. معالجة الصور عبر الرابط المباشر
        elif update.message.photo:
            photo_file = await update.message.photo[-1].get_file()
            image_data = requests.get(photo_file.file_path).content
            contents.append({"mime_type": "image/jpeg", "data": image_data})
            if user_caption: contents.append(user_caption)

        # 3. معالجة الملفات (PDF / TXT)
        elif update.message.document:
            doc_file = await update.message.document.get_file()
            doc_data = requests.get(doc_file.file_path).content
            contents.append({"mime_type": update.message.document.mime_type, "data": doc_data})
            if user_caption: contents.append(user_caption)

        # 4. معالجة الأصوات
        elif update.message.voice:
            voice_file = await update.message.voice.get_file()
            voice_data = requests.get(voice_file.file_path).content
            contents.append({"mime_type": update.message.voice.mime_type, "data": voice_data})

        if contents:
            response = model.generate_content(contents)
            await update.message.reply_text(response.text)
        else:
            await update.message.reply_text("أعتذر، لم أستطع قراءة هذا المدخل باه.")

    except Exception as e:
        await update.message.reply_text("عذراً معلم، حدث خطأ أثناء قراءة البيانات.")
        print(f"Error: {e}")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_all_inputs))
    
    threading.Thread(target=run_dummy_server, daemon=True).start()
    
    loop = asyncio.get_event_loop()
    loop.create_task(check_reminders_loop(app))
    
    print("🚀 البوت يعمل الآن بنجاح...")
    app.run_polling()

if __name__ == '__main__':
    main()
