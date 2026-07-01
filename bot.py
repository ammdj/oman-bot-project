import os
import threading
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai
from google.genai import types

# جلب المفاتيح من بيئة نظام Render بشكل آمن تماماً وبدون أي رموز داخل الكود
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# 🔒 المعرف الرقمي الخاص بك (صاحب البوت)
MY_TELEGRAM_ID = 7604099965  

# تهيئة عميل الذكاء الاصطناعي بالشكل المحدث
ai_client = genai.Client(api_key=GEMINI_API_KEY)

def get_long_term_memory():
    """قراءة ملف الذاكرة الدائمة بأمان وضمان عدم توقف البوت"""
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
    """تحديث ملف الذاكرة فوراً بكتابة السطور الجديدة"""
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
    """توليد التوجيهات الأساسية للبوت بأسلوب معالجة ChatGPT والذاكرة المدمجة"""
    user_memory = get_long_term_memory()
    return (
        "أنت مساعد ذكاء اصطناعي متطور وذكي جداً يعمل بنفس أسلوب وكفاءة ChatGPT. "
        "تحدث مع المستخدم بأسلوب احترافي، واضح، ومباشر. "
        "مرونتك كاملة: إذا طلب منك المستخدم تغيير أسلوب الكلام أو اللهجة، التزم بطلبه فوراً.\n"
        "التزم بالقواعد التالية بدقة شديدة:\n"
        "1. كن عملياً ومباشراً وتجنب اللف والدوران.\n"
        f"2. إليك الذاكرة الدائمة والمحفوظة عن المستخدم، تذكرها جيداً وابنِ كلامك عليها دائماً:\n{user_memory}\n"
        "3. إذا سألك عن أخبار العالم الحالية، استخدم أداة البحث جوجل المدمجة معك لتقديم معلومات حقيقية ومحدثة."
    )

def run_dummy_server():
    """تشغيل سيرفر محلي بسيط لإبقاء البوت حياً على منصة Render"""
    port = int(os.environ.get("PORT", 8000))
    from http.server import SimpleHTTPRequestHandler, HTTPServer
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != MY_TELEGRAM_ID:
        await update.message.reply_text("عذراً، هذا البوت خاص ومقفل لصاحبه فقط! 🔒")
        return
    await update.message.reply_text("أهلاً بك! أنا مساعدك الذكي الجاهز لخدمتك الآن. كيف يمكنني مساعدتك؟ 🤖")

async def handle_all_inputs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    if user_id != MY_TELEGRAM_ID:
        await update.message.reply_text("عذراً، هذا البوت خاص بصاحبه فقط. 🔒")
        return

    user_text = update.message.text if update.message.text else ""
    
    # ميزة التذكر المباشر والمستقر
    if user_text.strip().startswith(("احفظ:", "تذكر:", "احفظ ", "تذكر ")):
        clean_info = user_text.replace("احفظ:", "").replace("تذكر:", "").replace("احفظ", "").replace("تذكر", "").strip()
        if clean_info:
            if append_to_memory_file(clean_info):
                await update.message.reply_text(f"✅ تم حفظ هذه المعلومة بنجاح في ذاكرتي الدائمة: \n`{clean_info}`")
                return
            else:
                await update.message.reply_text("❌ حدث خطأ داخلي أثناء محاولة كتابة الملف على السيرفر.")
                return

    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    user_caption = update.message.caption if update.message.caption else ""
    contents_list = []

    try:
        # معالجة النصوص والوسائط المتعددة بشكل آمن
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
            # الاتصال بالنموذج مع تمرير أداة بحث جوجل بالصيغة المدعومة والمستقرة لعام 2026
            response = ai_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=contents_list,
                config=types.GenerateContentConfig(
                    system_instruction=get_system_instruction(),
                    tools=[{"google_search": {}}]  # الصيغة المباشرة والأكثر استقراراً لمنع أخطاء الاتصال
                )
            )
            if response.text:
                await update.message.reply_text(response.text)
            else:
                await update.message.reply_text("أعتذر، لم أتمكن من صياغة رد نصي في الوقت الحالي.")
        else:
            await update.message.reply_text("عذراً، لم أفهم هذا المدخل.")

    except Exception as e:
        # هنا قمنا بتغيير رسالة الخطأ لتطبع لك السبب الحقيقي والفعلي القادم من السيرفر مباشرة
        await update.message.reply_text(f"⚠️ حدث خطأ في النظام: {str(e)}")
        print(f"Error details: {e}")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_all_inputs))
    
    threading.Thread(target=run_dummy_server, daemon=True).start()
    
    print("🚀 البوت المستقر والآمن يعمل الآن بنجاح...")
    app.run_polling()

if __name__ == '__main__':
    main()
