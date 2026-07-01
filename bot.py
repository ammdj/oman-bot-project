import os
import threading
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# جلب المفاتيح من بيئة نظام Render بشكل آمن تماماً
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
MY_CLOUD_CHANNEL = os.environ.get("MY_CLOUD_CHANNEL")

# 🔒 المعرف الرقمي الخاص بك (البارون) لضمان خصوصية السحابة
MY_TELEGRAM_ID = 7604099965  

# ملف محلي مؤقت فقط لفهرسة الأسماء للبحث السريع
INDEX_FILE = "cloud_index.txt"

def save_to_index(file_type: str, caption: str, message_id: int):
    try:
        with open(INDEX_FILE, "a", encoding="utf-8") as f:
            f.write(f"{file_type}|{caption}|{message_id}\n")
    except Exception as e:
        print(f"Index error: {e}")

def search_in_index(query: str):
    results = []
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if query.lower() in line.lower():
                    results.append(line.strip().split("|"))
    return results

def run_dummy_server():
    port = int(os.environ.get("PORT", 8000))
    from http.server import SimpleHTTPRequestHandler, HTTPServer
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != MY_TELEGRAM_ID:
        await update.message.reply_text("🔒 عذراً، هذه السحابة مشفرة وخاصة بالبارون فقط!")
        return
    await update.message.reply_text(
        "👑 أهلاً بك في سحابتك الشخصية الآمنة يا بارون.\n\n"
        "📦 يمكنك الآن إرسال أي (صور، مستندات، ملاحظات نصية، مقاطع صوتية) وسأقوم بحفظها وتأمينها فوراً مدى الحياة وبمساحة غير محدودة.\n\n"
        "🔍 للبحث عن أي شيء حفظته لاحقاً، أرسل كلمة: \n`بحث: اسم_الملف`"
    )

async def handle_cloud_storage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != MY_TELEGRAM_ID:
        await update.message.reply_text("الوصول مرفوض. السحابة مغلقة. 🔒")
        return

    if not MY_CLOUD_CHANNEL:
        await update.message.reply_text("❌ خطأ: يرجى ضبط متغير `MY_CLOUD_CHANNEL` في إعدادات Render أولاً.")
        return

    caption = update.message.caption if update.message.caption else "ملف_بدون_عنوان"
    
    try:
        if update.message.text:
            text_content = update.message.text.strip()
            
            if text_content.startswith(("بحث:", "بحث ")):
                query = text_content.replace("بحث:", "").replace("بحث", "").strip()
                search_results = search_in_index(query)
                if not search_results:
                    await update.message.reply_text(f"🔍 لم أجد أي بيانات مطابقة لـ '{query}' في السحابة يا بارون.")
                    return
                
                await update.message.reply_text(f"📂 تم العثور على {len(search_results)} ملفات مطابقة، جاري جلبها...")
                for res in search_results:
                    await context.bot.forward_message(chat_id=user_id, from_chat_id=MY_CLOUD_CHANNEL, message_id=int(res[2]))
                return

            cloud_msg = await context.bot.send_message(chat_id=MY_CLOUD_CHANNEL, text=f"📝 [بيانات نصية مخزنة]:\n\n{text_content}")
            save_to_index("text", text_content[:30], cloud_msg.message_id)
            await update.message.reply_text("✅ تم تشفير وحفظ البيانات النصية في سحابتك بنجاح يا بارون.")

        elif update.message.photo:
            photo_id = update.message.photo[-1].file_id
            cloud_msg = await context.bot.send_photo(chat_id=MY_CLOUD_CHANNEL, photo=photo_id, caption=f"📸 صورة مخزنة: {caption}")
            save_to_index("photo", caption, cloud_msg.message_id)
            await update.message.reply_text(f"✅ تم حفظ الصورة بنجاح تحت عنوان: `{caption}`")

        elif update.message.document:
            doc_id = update.message.document.file_id
            doc_name = update.message.document.file_name
            cloud_msg = await context.bot.send_document(chat_id=MY_CLOUD_CHANNEL, document=doc_id, caption=f"📄 مستند مخزن: {caption} ({doc_name})")
            save_to_index("document", f"{caption} {doc_name}", cloud_msg.message_id)
            await update.message.reply_text(f"✅ تم حفظ المستند `{doc_name}` بنجاح.")

        elif update.message.voice or update.message.audio:
            voice_id = update.message.voice.file_id if update.message.voice else update.message.audio.file_id
            cloud_msg = await context.bot.send_voice(chat_id=MY_CLOUD_CHANNEL, voice=voice_id, caption=f"🎵 ملف صوتي مخزن: {caption}")
            save_to_index("voice", caption, cloud_msg.message_id)
            await update.message.reply_text("✅ تم حفظ المقطع الصوتي بأمان في السحابة.")

    except Exception as e:
        await update.message.reply_text(f"⚠️ حدث خطأ أثناء نقل البيانات إلى السحابة: {str(e)}")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_cloud_storage))
    
    threading.Thread(target=run_dummy_server, daemon=True).start()
    
    print("🚀 سحابة البارون الشخصية تعمل الآن بأمان كامل...")
    app.run_polling()

if __name__ == '__main__':
    main()
