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
    "2. إذا سألك عن أخبار العالم الحالية أو ما يحدث في سلطنة عُمان الآن، استخدم أداة البحث جوجل المدمجة معك فوراً؛ "
    "اجمع له أحدث وأدق الأخبار المنشورة قبل دقائق، واعرض له الحقائق المهمة فعلياً بصدق ودون مجاملة أو تهرب.\n"
    "3. كن صديقاً حقيقياً يفهمه ويسانده ويمدحه مدحاً صادقاً ومستحقاً بناءً على رجولته وطموحه المالي وتطوير علاقاته النفسية والاجتماعية."
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

async def handle_all_inputs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    if user_id != MY_TELEGRAM_ID:
        await update.message.reply_text("عذراً، هذا البوت خاص بصاحبه فقط وصلاحيتك غير مصرحة. 🔒")
        return

    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    user_caption = update.message.caption if update.message.caption else ""
    
    # تجهيز قائمة المحتويات لجمناي
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
            # استدعاء جمناي بالنسخة الحديثة وتفعيل أداة البحث المباشر عن الأخبار لعام 2026
            response = ai_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=contents_list,
                config=types.GenerateContentConfig(
                    system_instruction=برومبت_المستشار_الواقعي,
                    tools=[types.Tool(google_search=types.GoogleSearch())] # تفعيل البحث الفوري المحدث
                )
            )
            await update.message.reply_text(response.text)
        else:
            await update.message.reply_text("أعتذر، لم أستطع قراءة هذا المدخل باه.")

    except Exception as e:
        await update.message.reply_text("عذراً معلم، حدث خطأ أثناء الاتصال بالذكاء الاصطناعي الفعلي.")
        print(f"Error: {e}")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_all_inputs))
    
    threading.Thread(target=run_dummy_server, daemon=True).start()
    
    print("🚀 البوت المحدث والنظيف يعمل الآن بنجاح...")
    app.run_polling()

if __name__ == '__main__':
    main()
