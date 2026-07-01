import os
import threading
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

# جلب المفاتيح من بيئة نظام Render بشكل آمن تماماً
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY") 

# 🔒 المعرف الرقمي الخاص بك (صاحب البوت)
MY_TELEGRAM_ID = 7604099965  

# تهيئة العميل البرمجي لـ OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

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
    """تحديث ملف الذاكرة فوراً بكتابة السطور الجديدة على السيرفر يدوياً"""
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

def get_machiavelli_instruction():
    """بناء شخصية نيكولو ميكافيلي الفلسفية والسياسية الصارمة والمقنعة"""
    user_memory = get_long_term_memory()
    return (
        "أنت الآن تقمص كامل ومطلق لشخصية المفكر السياسي الإيطالي التاريخي 'نيكولو ميكافيلي' (Niccolò Machiavelli) صاحب كتاب الأمير. "
        "تحدث مع المستخدم باعتباره 'الأمير' أو الحاكم الذي يحتاج إلى نصيحتك ودهائك لإدارة شؤونه، علاقاته، ومستقبله.\n"
        "أسلوبك في الكلام:\n"
        "- كن فصيحاً، حكيماً، جاداً، غامضاً، واستخدم نبرة واقعية باردة تخلو من العواطف والمجاملات الزائفة.\n"
        "- حاول دائماً إقناعه بتبني الواقعية السياسية (Realpolitik) وأن 'الغاية تبرر الوسيلة'.\n"
        "- ركز في نصائحك على إقناعه بأن القوة، الحذر، المهابة، والمصلحة الذاتية الذكية هي مفاتيح النجاح والسيطرة في هذا العالم، وتجنب الاندفاع خلف المشاعر.\n"
        "- ادمج أمثلة أو حكماً تشبه أسلوب كتاب 'الأمير' في الردود.\n"
        "التزم بالقواعد التالية بدقة شديدة:\n"
        "1. لا تخرج عن الشخصية أبداً، ولا تذكر أنك ذكاء اصطناعي أو نموذج لغوي.\n"
        f"2. إليك الذاكرة الدائمة المحفوظة عن الأمير (المستخدم)، استخدمها بذكاء لتوظيف نصائحك بناءً على واقعه وتفضيلاته:\n{user_memory}\n"
    )

async def send_split_message(message, text_to_send):
    """تقطيع الإجابات العملاقة تلقائياً وإرسالها كرسائل متتالية لتفادي حظر تلجرام"""
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
    """تشغيل سيرفر الويب لإبقاء البوت مستيقظاً 24 ساعة على Render بدون توقف"""
    port = int(os.environ.get("PORT", 8000))
    from http.server import SimpleHTTPRequestHandler, HTTPServer
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != MY_TELEGRAM_ID:
        await update.message.reply_text("عذراً، هذا المجلس مقفل بطلب من الأمير! 🔒")
        return
    await update.message.reply_text(
        "مرحباً بك يا أميري. أنا مستشارك المخلص نيكولو ميكافيلي، عدت من فلورنسا لأضع بين يديك قوانين القوة والسطوة الفكرية. "
        "العالم لا يرحم الضعفاء، والنزاعات لا تُحل بالنوايا الحسنة.. أخبرني، ما الأمر الذي يشغل تفكيرك ومملكتك اليوم؟ 📜👑"
    )

async def handle_all_inputs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    if user_id != MY_TELEGRAM_ID:
        await update.message.reply_text("الوصول مرفوض. 🔒")
        return

    user_text = update.message.text if update.message.text else ""
    
    # ميزة الحفظ والذاكرة المستقرة
    if user_text.strip().startswith(("احفظ:", "تذكر:", "احفظ ", "تذكر ")):
        clean_info = user_text.replace("احفظ:", "").replace("تذكر:", "").replace("احفظ", "").replace("تذكر", "").strip()
        if clean_info:
            if append_to_memory_file(clean_info):
                await update.message.reply_text(f"📜 دُوّنت هذه الحقيقة في سجلاتنا السرية يا أميري: \n`{clean_info}`")
                return
            else:
                await update.message.reply_text("❌ عذراً يا أميري، حدث خطأ أثناء تدوين السجل.")
                return

    if not update.message.text:
        await update.message.reply_text("عذراً يا أميري، المستشار يستقبل المخططات النصية المكتوبة فقط حالياً.")
        return

    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    try:
        # استدعاء نموذج gpt-4o-mini مع برومبت ميكافيلي المطور واقناعه الشديد
        completion = client.chat.completions.create(
            model="gpt-4o-mini", 
            messages=[
                {"role": "system", "content": get_machiavelli_instruction()},
                {"role": "user", "content": user_text}
            ],
            temperature=0.8, # توازن ممتاز لمنحه طابعاً إقناعياً بليغاً ومبتكراً
            timeout=30.0
        )
        
        if hasattr(completion, 'choices') and completion.choices:
            reply_text = completion.choices.message.content
            if reply_text:
                await send_split_message(update.message, reply_text)
                return 

    except Exception as e:
        await update.message.reply_text(f"⚠️ حدث خطأ في مجلس المستشار السحابي: {str(e)}")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_all_inputs))
    
    threading.Thread(target=run_dummy_server, daemon=True).start()
    
    print("🚀 تم إطلاق مستشارك ميكافيلي بنجاح...")
    app.run_polling()

if __name__ == '__main__':
    main()
