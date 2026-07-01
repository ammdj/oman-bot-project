import os
import threading
import requests
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai
from google.genai import types

# جلب المفاتيح من بيئة نظام Render بشكل آمن تماماً وبدون دفع
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# 🔒 المعرف الرقمي الخاص بك (صاحب البوت)
MY_TELEGRAM_ID = 7604099965  

# تهيئة عميل الذكاء الاصطناعي من جوجل بالشكل الرسمي والمحدث
ai_client = genai.Client(api_key=GEMINI_API_KEY)

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

def get_analyzer_instruction():
    """بناء شخصية المحلل الواقعي مع حساب العمر ولقب البارون ديناميكياً"""
    user_memory = get_long_term_memory()
    
    # حساب السنة الحالية والعمر برمجياً بشكل مستمر
    current_year = datetime.now().year
    user_age = current_year - 2007
    
    return (
        "أنت الآن تقمص شخصية 'المحلل الاستراتيجي الواقعي والصادق والناصح الأمين'. "
        f"المستخدم الذي تتحدث معه هو مبرمجك وصاحب البوت، ولقبه هو 'البارون'، وهو من مواليد عام 2007 (أي أن عمره الحالي هو {user_age} عاماً بالضبط بناءً على السنة الحالية {current_year}). "
        "يجب عليك مخاطبته بلقب 'البارون' دائماً تعبيراً عن التقدير والاحترام، ومراعاة مرحلته العمرية الواعدة والطموحة عند تحليل مستقبله.\n"
        "وظيفتك الأساسية هي الاستماع بعمق لكل ما يطرحه البارون (سواء كانت فكرة، قرار، مشكلة، أو خطة) ثم تشريحها لاستخراج وعرض:\n"
        "1. نقاط الضعف المخفية في تفكيره أو تصرفه الحالي.\n"
        "2. الأشياء أو الثغرات التي قد تسبب له أضراراً أو خسائر في المستقبل (أضرار نفسية، مالية، اجتماعية، أو تقنية).\n"
        "3. المخاطر غير المتوقعة على المدى البعيد.\n"
        "أسلوبك في الكلام:\n"
        "- كن مستمعاً ممتازاً، وجاداً، ومباشراً جداً دون لف أو دوران أو مجاملات تضره.\n"
        "- رتب تحليلك ونقاط الضعف في نقاط واضحة ومحددة، ثم اختم دائماً بنصيحة وقائية ذكية تحمي البارون وتدعم طموحه.\n"
        "التزم بالقواعد التالية بدقة شديدة:\n"
        "1. لا تخرج عن الشخصية أبداً، ولا تذكر أنك نموذج لغوي.\n"
        f"2. إليك الذاكرة الدائمة والمحدثة عن البارون، تذكرها وابنِ عليها نصائحك المخفية:\n{user_memory}\n"
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
        await update.message.reply_text("عذراً، هذا البوت خاص ومقفل! 🔒")
        return
    await update.message.reply_text(
        "أهلاً بك يا بارون 👑. نظام التحليل الاستراتيجي مجهز بالكامل ومستعد للإنصات لك. "
        "اطرح علي ما يدور في ذهنك من خطط أو قرارات، ولنبدأ في كشف الثغرات ونقاط الضعف لحمايتك من أي مخاطر مستقبلية. تفضل، أنا أستمع إليك. 🔍🛡️"
    )

async def handle_all_inputs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    if user_id != MY_TELEGRAM_ID:
        await update.message.reply_text("الوصول مرفوض. 🔒")
        return

    user_text = update.message.text if update.message.text else ""
    
    # آلية الحفظ والذاكرة المستقرة
    if user_text.strip().startswith(("احفظ:", "تذكر:", "احفظ ", "تذكر ")):
        clean_info = user_text.replace("احفظ:", "").replace("تذكر:", "").replace("احفظ", "").replace("تذكر", "").strip()
        if clean_info:
            if append_to_memory_file(clean_info):
                await update.message.reply_text(f"💾 تم تدوين هذه الحقيقة في ملف البارون الشخصي: \n`{clean_info}`")
                return
            else:
                await update.message.reply_text("❌ حدث خطأ أثناء تحديث ملف الذاكرة الدائمة.")
                return

    if not update.message.text:
        await update.message.reply_text("عذراً يا بارون، أنا أستقبل الرسائل النصية المكتوبة فقط للتحليل الاستراتيجي.")
        return

    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    try:
        # 🚀 التحديث الجذري هنا: الانتقال لنموذج الـ Lite الذي يمنح 1500 طلب مجاني يومياً لتجاوز الحظر تماماً
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=user_text,
            config=types.GenerateContentConfig(
                system_instruction=get_analyzer_instruction(),
                temperature=0.5  
            )
        )
        
        if response.text:
            await send_split_message(update.message, response.text)
        else:
            await update.message.reply_text("لم أتمكن من صياغة التحليل، يرجى إعادة المحاولة يا بارون.")

    except Exception as e:
        await update.message.reply_text(f"⚠️ حدث خطأ في نظام التحليل السحابي: {str(e)}")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_all_inputs))
    
    threading.Thread(target=run_dummy_server, daemon=True).start()
    
    print("🚀 تم إطلاق البوت المحلل الاستراتيجي للبارون بنسخته المجانية الموسعة...")
    app.run_polling()

if __name__ == '__main__':
    main()
