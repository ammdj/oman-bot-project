import os
import threading
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

# جلب المفاتيح من بيئة نظام Render بشكل آمن
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

# 🔒 المعرف الرقمي الخاص بك (صاحب البوت)
MY_TELEGRAM_ID = 7604099965  

# تهيئة العميل البرمجي لـ OpenRouter
client = OpenAI(
    base_url="https://openrouter.ai",
    api_key=OPENROUTER_API_KEY,
)

def get_long_term_memory():
    """قراءة ملف الذاكرة الدائمة بأمان لدمجها مع المحادثة"""
    try:
        if not os.path.exists("memory.txt"):
            with open("memory.txt", "w", encoding="utf-8") as f:
                f.write("")
            return "لا توجد معلومات إضافية محفوظة بعد."
        
        with open("memory.txt", "r", encoding="utf-8") as f:
            content = f.read().strip()
            return content if content else "لا توجد معلومات إضافية محفوظة بعد."
    except Exception as e:
        print(f"Error reading memory file: {e}")
    return "لا توجد معلومات إضافية محفوظة بعد."

def append_to_memory_file(new_info: str) -> bool:
    """تحديث ملف الذاكرة فوراً بكتابة السطور الجديدة على السيرفر"""
    try:
        current = ""
        if os.path.exists("memory.txt"):
            with open("memory.txt", "r", encoding="utf-8") as f:
                current = f.read().strip()
        
        updated = current + f"\n- {new_info}" if current else f"- {new_info}"
        with open("memory.txt", "w", encoding="utf-8") as f:
            f.write(updated.strip())
        return True
    except Exception as e:
        print(f"Error saving to memory file: {e}")
        return False

def get_system_instruction():
    """بناء شخصية البوت الذكية مع دمج الذاكرة المحفوظة"""
    user_memory = get_long_term_memory()
    return (
        "أنت مساعد ذكاء اصطناعي متطور وذكي جداً يعمل بنفس أسلوب وكفاءة ChatGPT. "
        "تحدث مع المستخدم بأسلوب احترافي، واضح، ومباشر. "
        "مرونتك كاملة: إذا طلب منك المستخدم تغيير أسلوب الكلام أو اللهجة، التزم بطلبه فوراً.\n"
        "التزم بالقواعد التالية بدقة شديدة:\n"
        "1. كن عملياً ومباشراً وتجنب اللف والدوران.\n"
        f"2. إليك الذاكرة الدائمة والمحفوظة عن المستخدم، تذكرها جيداً وابنِ كلامك عليها دائماً:\n{user_memory}\n"
    )

def run_dummy_server():
    """تشغيل سيرفر محلي لإبقاء البوت حياً على منصة Render"""
    port = int(os.environ.get("PORT", 8000))
    from http.server import SimpleHTTPRequestHandler, HTTPServer
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != MY_TELEGRAM_ID:
        await update.message.reply_text("عذراً، هذا البوت خاص ومقفل لصاحبه فقط! 🔒")
        return
    await update.message.reply_text("أهلاً بك! أنا مساعدك الذكي الخارق المدعوم من OpenRouter. كيف يمكنني مساعدتك اليوم؟ 🤖")

async def handle_all_inputs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    if user_id != MY_TELEGRAM_ID:
        await update.message.reply_text("عذراً، هذا البوت خاص بصاحبه فقط. 🔒")
        return

    user_text = update.message.text if update.message.text else ""
    
    # ميزة تذكر وحفظ المعلومات الشخصية
    if user_text.strip().startswith(("احفظ:", "تذكر:", "احفظ ", "تذكر ")):
        clean_info = user_text.replace("احفظ:", "").replace("تذكر:", "").replace("احفظ", "").replace("تذكر", "").strip()
        if clean_info:
            if append_to_memory_file(clean_info):
                await update.message.reply_text(f"✅ تم حفظ هذه المعلومة بنجاح في ذاكرتي الدائمة: \n`{clean_info}`")
                return
            else:
                await update.message.reply_text("❌ حدث خطأ داخلي أثناء محاولة كتابة الملف على السيرفر.")
                return

    if not update.message.text:
        await update.message.reply_text("عذراً، هذا النموذج يدعم الرسائل النصية فقط حالياً.")
        return

    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    try:
        # استدعاء نموذج مستقر جداً ومجاني بالكامل عبر الخادم الموحد لـ OpenRouter
        completion = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "https://render.com", 
                "X-Title": "Telegram Bot",
            },
            model="google/gemini-2.5-flash:free",  # استخدام النسخة المجانية المستقرة والمدعومة بالكامل
            messages=[
                {
                    "role": "system",
                    "content": get_system_instruction(),
                },
                {
                    "role": "user",
                    "content": user_text,
                }
            ]
        )
        
        # حماية برمجية: التحقق من شكل الرد قبل قراءته لتفادي خطأ الـ 'str'
        if hasattr(completion, 'choices') and completion.choices:
            reply_text = completion.choices[0].message.content
            if reply_text:
                await update.message.reply_text(reply_text)
                return
        
        # إذا رجع الرد على هيئة نص عادي (رسالة خطأ من OpenRouter)، يتم طباعتها مباشرة للفحص
        if isinstance(completion, str):
            await update.message.reply_text(f"⚠️ تنبيه تقني من الخادم: {completion}")
        else:
            await update.message.reply_text("أعتذر، واجهت مشكلة في استخراج رد مناسب من الخادم المفتوح.")

    except Exception as e:
        await update.message.reply_text(f"⚠️ حدث خطأ في اتصال البوت: {str(e)}")
        print(f"Error details: {e}")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_all_inputs))
    
    threading.Thread(target=run_dummy_server, daemon=True).start()
    
    print("🚀 البوت المستقر بنظام OpenRouter يعمل الآن...")
    app.run_polling()

if __name__ == '__main__':
    main()
