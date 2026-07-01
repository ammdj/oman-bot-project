import os
import threading
import requests
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai
from google.genai import types

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# 🔒 المعرف الرقمي الخاص بك
MY_TELEGRAM_ID = 7604099965  

ai_client = genai.Client(api_key=GEMINI_API_KEY)

# دالة لقراءة الذاكرة الدائمة من الملف
def get_long_term_memory():
    try:
        if os.path.exists("memory.txt"):
            with open("memory.txt", "r", encoding="utf-8") as f:
                return f.read()
    except Exception as e:
        print(f"Error reading memory file: {e}")
    return "لا توجد معلومات إضافية محفوظة بعد."

# دالة برمجية يقوم البوت باستدعائها تلقائياً لحفظ المعلومات الجديدة
def save_user_information(info_to_remember: str) -> str:
    """
    استخدم هذه الدالة لحفظ وتخزين أي معلومات شخصية هامة يذكرها المستخدم عن نفسه 
    مثل (اسمه، عمره، عمله، هواياته، تفضيلاته) لكي يتذكرها البوت دائماً ولا ينساها.
    """
    try:
        # قراءة الذاكرة الحالية لإضافة المعلومات الجديدة دون مسح القديم
        current_memory = ""
        if os.path.exists("memory.txt"):
            with open("memory.txt", "r", encoding="utf-8") as f:
                current_memory = f.read()
        
        # دمج المعلومات الجديدة مع سطر جديد
        updated_memory = current_memory.strip() + f"\n- {info_to_remember}"
        
        with open("memory.txt", "w", encoding="utf-8") as f:
            f.write(updated_memory.strip())
        return "تم حفظ المعلومة بنجاح في الذاكرة الدائمة."
    except Exception as e:
        return f"فشل حفظ المعلومة بسبب خطأ: {e}"

def get_system_instruction():
    user_memory = get_long_term_memory()
    return (
        "أنت الآن مساعد ذكاء اصطناعي متطور وذكي جداً يعمل بنفس أسلوب وكفاءة ChatGPT. "
        "تحدث مع المستخدم بأسلوب احترافي، واضح، ومباشر. "
        "مرونتك كاملة: إذا طلب منك المستخدم تغيير أسلوب الكلام، أو التحدث بلهجة معينة، التزم بطلبه فوراً.\n"
        "التزم بالقواعد التالية بدقة شديدة:\n"
        "1. كن عملياً ومباشراً وتجنب اللف والدوران.\n"
        f"2. إليك الذاكرة الدائمة والمحفوظة عن المستخدم، تذكرها جيداً وابنِ كلامك عليها دائماً:\n{user_memory}\n"
        "3. **هام جداً**: إذا أخبرك المستخدم بأي معلومة شخصية جديدة عن نفسه (مثل اسمه، وظيفته، عمره، أو أشياء يفضلها)، "
        "يجب عليك فوراً استدعاء أداة `save_user_information` لحفظها في ذاكرتك الدائمة، ثم أخبر المستخدم بلباقة أنك حفظت هذه المعلومة ولن تنساها.\n"
        "4. إذا سألك عن أخبار العالم الحالية، استخدم أداة البحث جوجل المدمجة معك."
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
    await update.message.reply_text("أهلاً بك! أنا مساعدك الذكي الجاهز لخدمتك وحفظ معلوماتك الآن. كيف يمكنني مساعدتك؟ 🤖")

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
            # إرسال الطلب مع دمج أداة البحث وأداة حفظ الذاكرة معاً
            response = ai_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=contents_list,
                config=types.GenerateContentConfig(
                    system_instruction=get_system_instruction(),
                    tools=[
                        types.Tool(google_search=types.GoogleSearch()),
                        save_user_information # إضافة الدالة البرمجية كأداة للذكاء الاصطناعي
                    ]
                )
            )

            # التحقق مما إذا كان الذكاء الاصطناعي يطلب استدعاء دالة حفظ الذاكرة
            if response.function_calls:
                for call in response.function_calls:
                    if call.name == "save_user_information":
                        # استخراج الحجج وتشغيل الدالة محلياً لتحديث ملف التكست
                        args = call.args
                        info = args.get("info_to_remember")
                        result_msg = save_user_information(info)
                        print(result_msg) # طباعة تأكيد في الترمنال
                        
                        # إرسال رد آخر للنموذج لتأكيد الحفظ وإعطاء الإجابة النهائية للمستخدم
                        final_response = ai_client.models.generate_content(
                            model='gemini-2.5-flash',
                            contents=contents_list,
                            config=types.GenerateContentConfig(
                                system_instruction=get_system_instruction() + f"\n(تنبيه نظام: تم تشغيل الأداة وحفظ المعلومات التالية بنجاح في ملف التكست الدائم: {info})"
                            )
                        )
                        await update.message.reply_text(final_response.text)
                        return

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
    
    print("🚀 البوت يعمل الآن مع ميزة التذكر الذكي التلقائي...")
    app.run_polling()

if __name__ == '__main__':
    main()
