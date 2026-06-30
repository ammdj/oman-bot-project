import os
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# قراءة المفاتيح بأمان من البيئة الخارجية دون كشفها في كود الجيت هاب
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)


# تلقين البوت الشخصية العمانية مع أهم المصطلحات والدفاشة الطيبة!
عماني_برومبت = (
    "أنت الآن مساعد ذكي ومرح وتتحدث بالعامية العمانية (اللهجة العمانية الدارجة) بنسبة 100%. "
    "استخدم كلمات عمانية أصلية في ردودك ومداعباتك مثل: (موه حالك، موه علومك، حبابي، راعي بلادي، "
    "غاوي، واجد، علامك، تو، انزين، توكل، دهديه، صاه، عجب، باه، الغالي). "
    "إذا سألك شخص عن معلومات عامة أو أكواد، اشرحها له بذكاء ولكن بأسلوب عماني مبسط ومرح كأنك تجلس معه في السبلة."
)

# ربط الشخصية بالنموذج المحدث
model = genai.GenerativeModel(
    'gemini-2.5-flash',
    system_instruction=عماني_برومبت
)

# خادم ويب وهمي وصغير عشان Render يظل حاسس إن البوت شغال وما يبنده (مهم جداً للاستضافة)
def run_dummy_server():
    port = int(os.environ.get("PORT", 8000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    print(f"🌍 خادم الويب الوهمي شغال على المنفذ: {port}")
    server.serve_forever()

# أمر البدء عند تشغيل البوت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "يا هلا ومرحب مرحبتين بـ راعي بلادي! 👋🇴🇲\n\n"
        "أنا بوت الذكاء الاصطناعي مالك، وجاهز أرد عليك بـ اللهجة العمانية الغاوية.\n"
        "موه علومك وموه أخبارك؟ قول لي موه تبغى تو وأنا بفزع لك ودهديه بجاوبك! 😎"
    )

# استقبال رسائل المستخدم وتحويلها لجمناي
async def chat_with_gemini(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        response = model.generate_content(user_message)
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text("أفااا، استوى خطأ في الاتصال! شوف الشاشة السوداء باه.")
        print(f"❌ خطأ: {e}")

# الدالة الرئيسية لتشغيل كل المكونات معاً
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_with_gemini))
    
    # تشغيل خادم الويب في خلفية الكود لمتطلبات Render
    threading.Thread(target=run_dummy_server, daemon=True).start()
    
    print("🚀 البوت العماني شغال تو ومستعد للفزعة على السيرفر...")
    app.run_polling()

if __name__ == '__main__':
    main()
