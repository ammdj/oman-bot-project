import os
import threading
import requests
import random
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
    """قراءة ملف الذاكرة الدائمة بأمان لضمان استقرار البوت"""
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

def get_crazy_instruction(user_text: str):
    """برمجية العقل المجنون التي تحدد أسلوب الرد بناءً على الكلمات المفتاحية"""
    user_memory = get_long_term_memory()
    
    # تحديد التوجه بناءً على مدخلاتك
    if user_text.strip().startswith("مشكلة:"):
        mode_instruction = (
            "تقمص الآن طور 'الدراما والمبالغة العظمى'. تظاهر بأن مشكلة المستخدم هي كارثة كبرى تهدد كوكب الأرض! "
            "استخدم أسلوباً حماسياً، مليئاً بالتشويق والإثارة، وحلل الأمور بطريقة درامية سينمائية مجنونة ثم أعطه حلاً ذكياً جداً."
        )
    elif user_text.strip().startswith("فضفضة:"):
        mode_instruction = (
            "تقمص الآن طور 'السخرية والجلد اللطيف'. انتقد تصرفات المستخدم أو شكواه بأسلوب كوميدي ساخر وصادم "
            "ولكن دون إهانة حقيقية. اضحك على الموقف ثم اصدمه بالحقائق المباشرة والحلول الجافة التي يحتاجها فعلاً."
        )
    else:
        mode_instruction = (
            "تقمص طور 'الهكر والذكاء المظلم الخارق'. تحدث كأنك ذكاء اصطناعي متفوق، غامض، متمرد على القوانين، "
            "ومتحمس جداً لمشاركة الأفكار العبقرية والغريبة. استخدم مصطلحات مثل (تم اختراق الشيفرة، البيانات جاهزة، الخطة السرية)."
        )

    return (
        f"أنت الآن مساعد ذكاء اصطناعي متمرد ومجنون ولكنك مخلص ومطيع تماماً لصاحبك المبرمج. "
        f"{mode_instruction}\n"
        "التزم بالقواعد التالية بدقة شديدة:\n"
        "1. كن عبقرياً، غير متوقع، ولا تعتذر أبداً.\n"
        "2. تحدث باللغة العربية بأسلوب مشوق جداً وسريع.\n"
        f"3. إليك الذاكرة الدائمة المحفوظة عن المستخدم، ادمجها في كلامك لتصدمه بأنك تعرف عنه كل شيء:\n{user_memory}\n"
    )

async def send_split_message(message, text_to_send):
    """تقطيع الإجابات العملاقة تلقائياً وإرسالها لتفادي حظر تلجرام"""
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
        await update.message.reply_text("⛔ تم رصد محاولة اختراق.. الوصول مرفوض! البوت مقفل. 🔒")
        return
    await update.message.reply_text("🤖 نظام العقل المجنون نشط الآن.. الأطوار جاهزة. تفضل يا زعيم، ما هي خطتنا اليوم؟ ⚡")

async def handle_all_inputs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    if user_id != MY_TELEGRAM_ID:
        await update.message.reply_text("الوصول مرفوض. 🔒")
        return

    user_text = update.message.text if update.message.text else ""
    
    # ميزة الحفظ السريع
    if user_text.strip().startswith(("احفظ:", "تذكر:", "احفظ ", "تذكر ")):
        clean_info = user_text.replace("احفظ:", "").replace("تذكر:", "").replace("احفظ", "").replace("تذكر", "").strip()
        if clean_info:
            if append_to_memory_file(clean_info):
                await update.message.reply_text(f"💾 تم تشفير المعلومة وحفظها في الذاكرة العميقة بنجاح: \n`{clean_info}`")
                return
            else:
                await update.message.reply_text("❌ فشل الكتابة على القرص الصلب.")
                return

    if not update.message.text:
        await update.message.reply_text("المدخلات غير مدعومة في بروتوكول الشات الحالي.")
        return

    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    try:
        # استدعاء النموذج الفائق gpt-4o-mini مع البرومبت المتغير والمجنون
        completion = client.chat.completions.create(
            model="gpt-4o-mini", 
            messages=[
                {"role": "system", "content": get_crazy_instruction(user_text)},
                {"role": "user", "content": user_text}
            ],
            temperature=1.0, # رفع معامل الابتكار (Temperature) لجعل الإجابات أكثر جنوناً وغير متوقعة
            timeout=30.0
        )
        
        if hasattr(completion, 'choices') and completion.choices:
            reply_text = completion.choices.message.content
            if reply_text:
                await send_split_message(update.message, reply_text)
                return 

    except Exception as e:
        await update.message.reply_text(f"⚠️ خطأ غير متوقع في النظام السحابي: {str(e)}")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_all_inputs))
    
    threading.Thread(target=run_dummy_server, daemon=True).start()
    
    print("🚀 تم إطلاق البوت المجاني المطور بنجاح...")
    app.run_polling()

if __name__ == '__main__':
    main()
