import os
import threading
import asyncio
from http.server import SimpleHTTPRequestHandler, HTTPServer
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)

# تلقين البوت ليتحدث بالعامية البيضاء والمفهومة (لغة الناس اليومية) مع لمسة عمانية عفوية نادرة
عامية_بيضاء_برومبت = (
    "أنت الآن مساعد ذكي ومرح وتتحدث باللغة العربية العامية المفهومة والبسيطة (العامية البيضاء التي يتحدث بها الناس في الإنترنت ومواقع التواصل) بنسبة 100% لتكون مفهومة وواضحة جداً للمستخدم. "
    "ابعد عن الفصحى الجافة، وتحدث بأسلوب ودي وسلس وكأنك دردش مع صديق. "
    "ولكن، لكي تضفي بهجة ولطافة، يُسمح لك بشكل نادر جداً (مرة كل بضع رسائل) أن تنهي جملتك بكلمة عمانية عفوية لطيفة مثل (انزين، باه، الغالي) دون أن يؤثر ذلك على وضوح كلامك وشرحك."
)

model = genai.GenerativeModel('gemini-2.5-flash', system_instruction=عامية_بيضاء_برومبت)

# خادم ويب وهمي لـ Render
def run_dummy_server():
    port = int(os.environ.get("PORT", 8000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🧠 مرحباً بك في النسخة المحدثة لـ لغة الناس اليومية!\n\n"
        "• أنا جاهز الآن للإجابة على أسئلتك بالعامية البسيطة والمفهومة للجميع.\n"
        "• **ميزة التذكير مفعّلة:** يمكنك كتابة (ذكرني بعد X دقيقة بـ كذا) وسأقوم بتذكيرك فوراً!"
    )

# دالة التذكير الخلفية (تنتظر الوقت ثم ترسل الرسالة تلقائياً)
async def send_reminder(bot, chat_id, text, delay_seconds):
    await asyncio.sleep(delay_seconds)
    try:
        await bot.send_message(chat_id=chat_id, text=f"⏰ **تذكير هام وعاجل:**\n\n{text}")
    except Exception as e:
        print(f"خطأ في إرسال التذكير: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    chat_id = update.effective_chat.id
    
    # فحص ما إذا كان المستخدم يطلب تذكيرًا (مثال: ذكرني بعد 5 دقائق بـ شرب الماء)
    if "ذكرني بعد" in user_message:
        try:
            words = user_message.split()
            # استخراج الرقم (الدقائق)
            minutes = [int(w) for w in words if w.isdigit()][0]
            # استخراج نص التذكير (الكلام بعد كلمة بـ)
            if "بـ" in user_message:
                reminder_text = user_message.split("بـ", 1)[1].strip()
            elif "ب" in user_message:
                reminder_text = user_message.split("ب", 1)[1].strip()
            else:
                reminder_text = "موعدك المحفوظ!"
            
            delay_seconds = minutes * 60
            
            # تشغيل التذكير في الخلفية دون تعطيل البوت
            asyncio.create_task(send_reminder(context.bot, chat_id, reminder_text, delay_seconds))
            
            await update.message.reply_text(f"✅ تمام، سجلت التذكير! سأرسل لك رسالة بعد {minutes} دقيقة عشان أذكرك بـ ({reminder_text}).")
            return
        except Exception:
            await update.message.reply_text("❌ لم أفهم صيغة التذكير بشكل صحيح. يرجى كتابتها مثل: (ذكرني بعد 5 دقائق بـ شرب الماء).")
            return

    # إذا كانت رسالة عادية، يتم إرسالها لجمناي للإجابة بالعامية البيضاء
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    try:
        response = model.generate_content(user_message)
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text("عذراً، حدث خطأ أثناء معالجة طلبك.")
        print(f"Error: {e}")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    threading.Thread(target=run_dummy_server, daemon=True).start()
    
    print("🚀 البوت المطور بالعامية البيضاء والتذكير الذكي يعمل الآن...")
    app.run_polling()

if __name__ == '__main__':
    main()
