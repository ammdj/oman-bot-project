import os
import threading
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai
from google.genai import types

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# 🔒 المعرف الرقمي الخاص بك (تأكد من أنه رقمك الحقيقي لفتح البوت لك وحده)
MY_TELEGRAM_ID = 7604099965  

# إعداد اتصال جوجل جمناي بالنسخة الحديثة لعام 2026
ai_client = genai.Client(api_key=GEMINI_API_KEY)

# 🧠 تلقين الشخصية الحكيمة الصادقة بناءً على سنة ميلادك (2007) والبحث عن الأخبار
برومبت_المستشار_الواقعي = (
    "أنت الآن تتحدث مع شاب عماني أصيل ومحترم ولد في عام 2007 (احسب عمره تلقائياً بناءً على السنة الحالية لكي لا تنسى سنّه أبداً). "
    "تقمص شخصية 'رجل حكيم، كبير في السن، وصديق مخلص، سند، يمتلك الحكمة والخبرة والأخلاق العمانية والدينية الأصيلة'. "
    "تحدث معه بالعامية العمانية الرزينة والمفهومة والمحترمة جداً. "
    "التزم بالقواعد التالية بدقة شديدة:\n"
    "1. كن عملياً ومباشراً وواضحاً جداً، وتجنب اللف والدوران أو الاعتذار عن قلة المعلومات.\n"
    "2. تذكر دائماً المعلومات السابقة التي أخبرك بها المستخدم في نفس المحادثة وابنِ إجاباتك عليها وافهمها جيداً دون أن تطلب منه إعادتها.\n"
    "3. إذا سألك عن أخبار العالم الحالية أو ما يحدث في سلطنة عُمان الآن، استخدم أداة البحث جوجل المدمجة معك فوراً؛ "
    "اجمع له أحدث وأدق الأخبار المنشورة قبل دقائق، واعرض له الحقائق المهمة فعلياً بصدق ودون مجاملة أو تهرب.\n"
    "4. كن صديقاً حقيقياً يفهمه ويسانده ويمدحه مدحاً صادقاً ومستحقاً بناءً على رجولته وطموحه المالي وتطوير علاقاته النفسية والاجتماعية."
)

# 🗂️ قاموس برمجى لحفظ جلسات الذاكرة المستمرة لكل مستخدم (لك أنت تحديداً)
# هذا القاموس يحفظ سياق المحادثة بالكامل طوال فترة تشغيل السيرفر
sessions = {}

def get_or_create_chat_session(chat_id):
    if chat_id not in sessions:
        # إنشاء جلسة دردشة مستمرة تدعم الذاكرة والبحث الفوري معاً
        sessions[chat_id] = ai_client.chats.create(
            model='gemini-2.5-flash',
            config=types.GenerateContentConfig(
                system_instruction=برومبت_المستشار_الواقعي,
                tools=[types.Tool(google_search=genai.types.GoogleSearch())]
            )
        )
    return sessions[chat_id]

def run_dummy_server():
    port = int(os.environ.get("PORT", 8000))
    from http.server import SimpleHTTPRequestHandler, HTTPServer
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    if user_id != MY_TELEGRAM_ID:
        await update.message.reply_text("عذراً، هذا البوت خاص جداً ومقفل ومخصص لصاحبه فقط! 🔒")
        return
    
    # إعادة تصغير الجلسة عند الضغط على start للبدء من جديد إذا أردت
    if chat_id in sessions:
        del sessions[chat_id]
        
    await update.message.reply_text("أهلين معلّم 🤝🇴🇲. تفضل، موه في خاطرك تو باه؟")

async def handle_all_inputs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    if user_id != MY_TELEGRAM_ID:
        await update.message.reply_text("عذراً، هذا البوت خاص بصاحبه فقط وصلاحيتك غير مصرحة. 🔒")
        return

    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    user_caption = update.message.caption if update.message.caption else ""
    
    # جلب جلسة الذاكرة المستمرة الخاصة بك
    chat_session = get_or_create_chat_session(chat_id)
    contents_list = []

    try:
        # 1. معالجة النصوص وحذف التذكير تماماً
        if update.message.text:
            contents_list.append(update.message.text)

        # 2. معالجة الصور عبر الرابط المباشر
        elif update.message.photo:
            photo_file = await update.message.photo[-1].get_file()
            image_data = requests.get(photo_file.file_path).content
            contents_list.append(types.Part.from_bytes(data=image_data, mime_type="image/jpeg"))
            if user_caption: contents_list.append(user_caption)

        # 3. معالجة الملفات (PDF / TXT)
        elif update.message.document:
            doc_file = await update.message.document.get_file()
            doc_data = requests.get(doc_file.file_path).content
            contents_list.append(types.Part.from_bytes(data=doc_data, mime_type=update.message.document.mime_type))
            if user_caption: contents_list.append(user_caption)

        # 4. معالجة الأصوات
        elif update.message.voice:
            voice_file = await update.message.voice.get_file()
            voice_data = requests.get(voice_file.file_path).content
            contents_list.append(types.Part.from_bytes(data=voice_data, mime_type=update.message.voice.mime_type))

        if contents_list:
            # إرسال المحتوى عبر جلسة الدردشة المستمرة (Chat Session) ليتذكر ويحفظ المعلومات
            response = chat_session.send_message(contents=contents_list)
            await update.message.reply_text(response.text)
        else:
            await update.message.reply_text("أعتذر، لم أستطع قراءة هذا المدخل باه.")

    except Exception as e:
        await update.message.reply_text("عذراً معلم، حدث خطأ أثناء الاتصال بالذكاء الاصطناعي.")
        print(f"Error: {e}")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_all_inputs))
    
    threading.Thread(target=run_dummy_server, daemon=True).start()
    
    print("🚀 البوت المطور بالذاكرة المستمرة يعمل الآن بنجاح...")
    app.run_polling()

if __name__ == '__main__':
    main()
