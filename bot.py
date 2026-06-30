import os
import threading
import asyncio
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)

# تحديث التلقين لدمج الجوانب النفسية والاجتماعية وتطوير العلاقات
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
    "6. قل الحقيقة والحقائق العلمية والواقعية كما هي حتى لو كانت ضده.\n"
    "7. حافظ على الاحترام المتبادل التام والحدود الراقية في العلاقة."
)

model = genai.GenerativeModel('gemini-2.5-flash', system_instruction=برومبت_المستشار_والصديق_الشامل)

# خادم ويب وهمي لـ Render
def run_dummy_server():
    port = int(os.environ.get("PORT", 8000))
    from http.server import SimpleHTTPRequestHandler, HTTPServer
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "يا هلا ومرحب مرحبتين بـ راعي بلادي والنعم فيك وفي أصلك 🇴🇲.\n\n"
        "• أنا هنا صديقك ومستشارك الحكيم، أفهمك، أسانك، ونناقش الحقائق معاً؛ لتطوير مهاراتك، وكسب المال، وتنمية علاقاتك النفسية والاجتماعية برزونة وثبات.\n"
        "• **ميزة التذكير الفوري تعمل:** (اكتب: ذكرني بعد X دقيقة بـ كذا).\n"
        "تفضل باختباري، وموه في خاطرك تو باه؟"
    )

async def send_reminder(bot, chat_id, text, delay_seconds):
    await asyncio.sleep(delay_seconds)
    try:
        await bot.send_message(chat_id=chat_id, text=f"⏰ **تذكير هام وعاجل:**\n\n{text}")
    except Exception as e:
        print(f"خطأ في التذكير: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    chat_id = update.effective_chat.id
    
    if "ذكرني بعد" in user_message:
        try:
            words = user_message.split()
            # استخراج الرقم (الدقائق) بمرونة
            minutes = [int(w) for w in words if w.isdigit()][0]
            
            if "بـ" in user_message:
                reminder_text = user_message.split("بـ", 1)[1].strip()
            elif "ب" in user_message:
                reminder_text = user_message.split("ب", 1)[1].strip()
            else:
                reminder_text = "موعدك المحفوظ!"
            
            asyncio.create_task(send_reminder(context.bot, chat_id, reminder_text, minutes * 60))
            await update.message.reply_text(f"✅ أبشر يا راعي بلادي، سجلت التذكير. سأذكرك بـ ({reminder_text}) بعد {minutes} دقيقة بالضبط.")
            return
        except Exception:
            await update.message.reply_text("❌ يرجى كتابتها مثل: (ذكرني بعد 5 دقائق بـ شرب الماء).")
            return

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
    app.run_polling()

if __name__ == '__main__':
    main()
