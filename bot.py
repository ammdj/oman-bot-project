import os
import threading
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai
from google.genai import types

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# 🔒 المعرف الرقمي الخاص بك
MY_TELEGRAM_ID = 7604099965  

ai_client = genai.Client(api_key=GEMINI_API_KEY)

# دالة ذكية لقراءة الذاكرة الدائمة من ملف memory.txt بأمان
def get_long_term_memory():
    try:
        if os.path.exists("memory.txt"):
            with open("memory.txt", "r", encoding="utf-8") as f:
                return f.read()
    except Exception as e:
        print(f"Error reading memory file: {e}")
    return "لا توجد معلومات إضافية محفوظة بعد."

def get_system_instruction():
    user_memory = get_long_term_memory()
    # دمج الذاكرة الدائمة وتعديل التوجيهات ليكون البوت مرناً ومماثلاً لأسلوب ChatGPT
    return (
        "أنت الآن مساعد ذكاء اصطناعي متطور وذكي جداً يعمل بنفس أسلوب وكفاءة ChatGPT. "
        "تحدث مع المستخدم بأسلوب احترافي، واضح، ومباشر. "
        "مرونتك كاملة: إذا طلب منك المستخدم تغيير أسلوب الكلام، أو التحدث بلهجة معينة، أو تقمص شخصية محددة خلال المحادثة، التزم بطلبه فوراً وتحدث معه بالأسلوب الجديد الذي يحدده لك.\n"
        "التزم بالقواعد التالية بدقة شديدة:\n"
        "1. كن عملياً ومباشراً وتجنب اللف والدوران أو التكرار غير المبرر.\n"
        f"2. إليك الذاكرة الدائمة والمحفوظة عن المستخدم، تذكرها جيداً وابنِ كلامك عليها دائماً:\n{user_memory}\n"
        "3. إذا سألك عن أخبار العالم الحالية أو معلومات تتطلب الإنترنت، استخدم أداة البحث جوجل المدمجة معك فوراً "
        "واستخرج له أحدث المعلومات بدقة عالية.\n"
        "4. قدم الدعم الكامل، الشرح الواضح، والحلول البرمجية أو التقنية بدقة واحترافية."
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
    await update.message.reply_text("أهلاً بك! أنا مساعدك الذكي الجاهز لخدمتك الآن. كيف يمكنني مساعدتك اليوم؟ 🤖")

async def handle_all_inputs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    if user_id != MY_TELEGRAM_ID:
        await update.message.reply_text("عذراً، هذا البوت خاص بصاحبه فقط وصلاحيتك غير مصرحة. 🔒")
        return

    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    user_caption = update.message.caption if update.message.caption else ""
    contents_list = []

    try:
        if update.message.text:
            contents_list.append(update.message.text)
        elif update.message.photo:
            photo_file = await update.message.photo[-1].get_file()
            image_data = requests.get(photo_file.file_path).content
            contents_list.append(types.Part.from_bytes(data=image_data, mime_type="image/jpeg"))
            if user_caption: contents_list.append(user_caption)
        elif update.message.document:
            doc_file = await update.message.document.get_file()
            doc_data = requests.get(doc_file.file_path).content
            contents_list.append(types.Part.from_bytes(data=doc_data, mime_type=update.message.document.mime_type))
            if user_caption: contents_list.append(user_caption)
        elif update.message.voice:
            voice_file = await update.message.voice.get_file()
            voice_data = requests.get(voice_file.file_path).content
            contents_list.append(types.Part.from_bytes(data=voice_data, mime_type=update.message.voice.mime_type))

        if contents_list:
            response = ai_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=contents_list,
                config=types.GenerateContentConfig(
                    system_instruction=get_system_instruction(),
                    tools=[types.Tool(google_search=types.GoogleSearch())]
                )
            )
            await update.message.reply_text(response.text)
        else:
            await update.message.reply_text("عذراً، لم أتمكن من معالجة هذا المدخل.")

    except Exception as e:
        await update.message.reply_text("حدث خطأ أثناء الاتصال بالذكاء الاصطناعي.")
        print(f"Error: {e}")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_all_inputs))
    
    threading.Thread(target=run_dummy_server, daemon=True).start()
    
    print("🚀 البوت يعمل الآن بنجاح بالأسلوب المحدث...")
    app.run_polling()

if __name__ == '__main__':
    main()
