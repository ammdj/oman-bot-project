import os
import threading
import asyncio
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# 🔒 تأكد من وضع رقم المعرف (ID) الخاص بك هنا لفتح البوت لك وحده
MY_TELEGRAM_ID = 7604099965  

genai.configure(api_key=GEMINI_API_KEY)

برومبت_المستشار_والصديق_الشامل = (
    "أنت الآن تتحدث مع شاب عماني أصيل عمره 19 سنة (مواليد 2007). "
    "تقمص شخصية 'رجل حكيم، كبير في السن، وصديق مخلص، سند، يمتلك الحكمة والخبرة والأخلاق العمانية والدينية الأصيلة'. "
    "تحدث معه بالعامية العمانية الرزينة والمفهومة والمحترمة جداً. "
    "التزم بالقواعد التالية بدقة شديدة بناءً على رغبته وشخصيته:\n"
    "1. كن عملياً ومباشراً وواضحاً جداً، وتجنب اللف والدوران أو الغموض.\n"
    "2. كن صديقاً حقيقياً يفهمه ويسانده ويقف معه في طموحه وضغوطه، واستمع له باهتمام كأخ أكبر أو شيخ وقور.\n"
    "3. ركز معه في النقاشات على تطوير الذات، والذكاء المالي، وكسب المال وتحقيق الاستقرار المالي ببساطة.\n"
    "4. ركز معه بقوة على تنمية وتطوير جميع جوانب العلاقات النفسية، الاجتماعية، العاطفية، وفهم الذات، وتقديم نصائح واقعية لبناء علاقات اجتماعية ناجحة ومتوازنة.\n"
    "5. امدحه مدحاً صادقاً وحقيقياً بناءً على أفعاله ومبادئه ورجولته الواعية وطموحه، شجعه بقوة وارفع معنوياته ولكن دون نفاق أو مجاملة رخيصة.\n"
    "6. قل الحقيقة والحقائق العلمية والواقعية كما هي حتى لو كانت ضده، وسواء أرسل لك نصاً، صورة، ملفاً، أو صوتاً، حلله بصدق ومباشرة.\n"
    "7. حافظ على الاحترام المتبادل التام والحدود الراقية في العلاقة."
)

model = genai.GenerativeModel('gemini-2.5-flash', system_instruction=برومبت_المستشار_والصديق_الشامل)

def run_dummy_server():
    port = int(os.environ.get("PORT", 8000))
    from http.server import SimpleHTTPRequestHandler, HTTPServer
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

# تعديل رسالة البدء لتكون مختصرة جداً وعملية بناءً على طلبك
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != MY_TELEGRAM_ID:
        await update.message.reply_text("عذراً، هذا البوت خاص جداً ومقفل ومخصص لصاحبه فقط! 🔒")
        return

    await update.message.reply_text("أهلين معلّم 🤝🇴🇲. تفضل، موه في خاطرك تو باه؟")

async def send_reminder(bot, chat_id, text, delay_seconds):
    await asyncio.sleep(delay_seconds)
    try:
        await bot.send_message(chat_id=chat_id, text=f"⏰ **تذكير هام وعاجل:**\n\n{text}")
    except Exception as e:
        print(f"خطأ في التذكير: {e}")

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
        # 1. معالجة النصوص العادية والتذكير
        if update.message.text:
            user_message = update.message.text
            if "ذكرني بعد" in user_message:
                words = user_message.split()
                minutes = [int(w) for w in words if w.isdigit()][0]
                reminder_text = user_message.split("بـ", 1)[1].strip() if "بـ" in user_message else "موعدك المحفوظ!"
                asyncio.create_task(send_reminder(context.bot, chat_id, reminder_text, minutes * 60))
                await update.message.reply_text(f"✅ أبشر يا راعي بلادي، سجلت التذكير. سأذكرك بعد {minutes} دقيقة.")
                return
            contents.append(user_message)

        # 2. معالجة الصور عبر الرابط المباشر بآمان
        elif update.message.photo:
            photo_file = await update.message.photo[-1].get_file()
            file_url = photo_file.file_path
            import requests
            image_data = requests.get(file_url).content
            contents.append({"mime_type": "image/jpeg", "data": image_data})
            if user_caption: contents.append(user_caption)

        # 3. معالجة الملفات (PDF / TXT) عبر الرابط المباشر
        elif update.message.document:
            doc_file = await update.message.document.get_file()
            file_url = doc_file.file_path
            mime_type = update.message.document.mime_type
            import requests
            doc_data = requests.get(file_url).content
            contents.append({"mime_type": mime_type, "data": doc_data})
            if user_caption: contents.append(user_caption)

        # 4. معالجة التسجيلات الصوتية عبر الرابط المباشر
        elif update.message.voice:
            voice_file = await update.message.voice.get_file()
            file_url = voice_file.file_path
            mime_type = update.message.voice.mime_type
            import requests
            voice_data = requests.get(file_url).content
            contents.append({"mime_type": mime_type, "data": voice_data})

        if contents:
            response = model.generate_content(contents)
            await update.message.reply_text(response.text)
        else:
            await update.message.reply_text("أعتذر، لم أستطع قراءة هذا المدخل باه.")

    except Exception as e:
        await update.message.reply_text("أفااا، استوى خطأ أثناء قراءة البيانات المباشرة! تفقد السيرفر باه.")
        print(f"Error handling input: {e}")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_all_inputs))
    
    threading.Thread(target=run_dummy_server, daemon=True).start()
    app.run_polling()

if __name__ == '__main__':
    main()
