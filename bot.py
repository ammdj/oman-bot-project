import os
import threading
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

# جلب المفاتيح من بيئة نظام Render بشكل آمن تماماً
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

# 🔒 المعرف الرقمي الخاص بك (صاحب البوت)
MY_TELEGRAM_ID = 7604099965  

# تهيئة العميل البرمجي لـ OpenRouter
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

def get_long_term_memory():
    """قراءة ملف الذاكرة الدائمة بأمان وضمان عدم إيقاف البوت"""
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
    """بناء شخصية البوت المطابقة تماماً لأسلوب ChatGPT الذكي"""
    user_memory = get_long_term_memory()
    return (
        "أنت مساعد ذكاء اصطناعي متطور وذكي جداً يعمل بنفس أسلوب وكفاءة ChatGPT من OpenAI. "
        "تحدث مع المستخدم بأسلوب احترافي، واضح، ومباشر. "
        "مرونتك كاملة: إذا طلب منك المستخدم تغيير أسلوب الكلام أو اللهجة، التزم بطلبه فوراً.\n"
        "التزم بالقواعد التالية بدقة شديدة:\n"
        "1. كن عملياً ومباشراً وتجنب اللف والدوران.\n"
        f"2. إليك الذاكرة الدائمة والمحفوظة عن المستخدم، تذكرها جيداً وابنِ كلامك عليها دائماً:\n{user_memory}\n"
    )

async def send_split_message(message, text_to_send):
    """تقطيع الإجابات الطويلة تلقائياً وإرسالها لتفادي حظر تلجرام"""
    max_length = 4000 
    if len(text_to_send) <= max_length:
        await message.reply_text(text_to_send)
        return

    parts = []
    while len(text_to_send) > 0:
        if len(text_to_send) <= max_length:
            parts.append(text_to_send)
            break
        
        chunk = text_to_send[:max_length]
        last_newline = chunk.rfind('\n')
        
        if last_newline > max_length * 0.7:  
            parts.append(text_to_send[:last_newline])
            text_to_send = text_to_send[last_newline:].strip()
        else:  
            parts.append(chunk)
            text_to_send = text_to_send[max_length:]

    for part in parts:
        if part.strip():
            await message.reply_text(part)

def run_dummy_server():
    """إبقاء البوت مستيقظاً 24 ساعة على Render بدون توقف"""
    port = int(os.environ.get("PORT", 8000))
    from http.server import SimpleHTTPRequestHandler, HTTPServer
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != MY_TELEGRAM_ID:
        await update.message.reply_text("عذراً، هذا البوت مخصص لصاحبه فقط! 🔒")
        return
    await update.message.reply_text("أهلاً بك! أنا مساعدك الذكي بنسخته النهائية المستقرة والمحمية ضد الضغط. كيف يمكنني مساعدتك؟ 🤖")

async def handle_all_inputs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    if user_id != MY_TELEGRAM_ID:
        await update.message.reply_text("عذراً، هذا البوت خاص بصاحبه فقط. 🔒")
        return

    user_text = update.message.text if update.message.text else ""
    
    # آلية التذكر والحفظ السريع
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
        await update.message.reply_text("عذراً، هذا النموذج مخصص للدردشة النصية الذكية حالياً.")
        return

    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    try:
        # 🚀 الاستدعاء الذكي عبر الموجه الموحد لتفادي مشاكل الضغط والحظر اليومي نهائياً
        completion = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "https://render.com", 
                "X-Title": "Telegram Bot MultiRouter",
            },
            model="openrouter/free",  # الموجه السحابي الموحد والمضمون لجميع النماذج المجانية المتاحة حالياً
            messages=[
                {"role": "system", "content": get_system_instruction()},
                {"role": "user", "content": user_text}
            ],
            timeout=30.0
        )
        
        if hasattr(completion, 'choices') and completion.choices:
            reply_text = completion.choices.message.content
            if reply_text:
                await send_split_message(update.message, reply_text)
                return
        
        # في حال أرجعت المنصة نص خطأ عادي بدلاً من كائن كامل
        await update.message.reply_text(f"⚠️ تنبيه تقني من الخادم السحابي: {str(completion)}")

    except Exception as e:
        # فحص مشكلة فنية شائعة في مفاتيح OpenRouter الجديدة
        error_msg = str(e)
        if "401" in error_msg or "Unauthorized" in error_msg:
            await update.message.reply_text("❌ خطأ: المفتاح `OPENROUTER_API_KEY` غير مفعل أو به أحرف خاطئة في Render. يرجى إعادة إنشائه.")
        elif "429" in error_msg:
            await update.message.reply_text("⚠️ تم استهلاك حد الـ 50 طلباً المجاني لحسابك اليوم على الموجه. يرجى الانتظار حتى الغد أو إضافة 1$ رصيد للحساب لمنحك طلبات غير محدودة.")
        else:
            await update.message.reply_text(f"⚠️ حدث خطأ في الاتصال بالخادم: {error_msg}")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_all_inputs))
    
    threading.Thread(target=run_dummy_server, daemon=True).start()
    
    print("🚀 تم تشغيل نظام التوجيه التلقائي الموحد للبوت...")
    app.run_polling()

if __name__ == '__main__':
    main()
