import os
import traceback
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

# جلب الإعدادات من Environment Variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")
PDF_ROOT = os.environ.get("PDF_ROOT", "PDF_Files")
DEVELOPER_USERNAME = os.environ.get("DEVELOPER_USERNAME", "@mr_alallaghy")

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN غير موجود في متغيرات البيئة!")

# ترتيب الأزرار في الصفوف
def arrange_buttons(items, prefix):
    keyboard = []
    temp = []
    for i, item in enumerate(items):
        callback_id = f"{prefix}_{i}"
        temp.append(InlineKeyboardButton(item, callback_data=callback_id))
        if len(temp) == 2:
            keyboard.append(temp)
            temp = []
    if temp:
        keyboard.append([temp[0]])
    return keyboard

# إضافة زر تواصل مع المطور وزر رجوع
def add_contact_and_back(keyboard, back_callback=None):
    if back_callback:
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data=back_callback)])
    keyboard.append([InlineKeyboardButton("📩 تواصل مع المطور", url=f"https://t.me/{DEVELOPER_USERNAME[1:]}")])
    return keyboard

# بدء البوت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not os.path.exists(PDF_ROOT):
        await update.message.reply_text("❌ لم يتم العثور على مجلد PDF_Files في نفس مسار البوت.")
        return

    sections = os.listdir(PDF_ROOT)
    sections = [s for s in sections if os.path.isdir(os.path.join(PDF_ROOT, s))]

    if not sections:
        await update.message.reply_text("📂 لا توجد أقسام داخل مجلد PDF_Files.")
        return

    context.user_data["sections"] = sections

    # 💫 الرسالة الأدبية المضافة
    welcome_message = (
        "🌟 مرحبًا بك في بوت الملفات الدراسية.\n\n"
        "📚 بُني هذا العمل بمجهود مجموعة من الطلبة والمساهمين، "
        "الذين جمعوا ونسّقوا هذه الملفات لتكون عونًا لكل باحثٍ عن العلم.\n\n"
        "💖 نرجو منك دعوةً طيبة بظهر الغيب، "
        "لعلّ الله يكتب بها الأجر لكل من شارك وساهم في إعداد هذا العمل.\n\n"
        "📘 اختر القسم العلمي لبدء التصفح:"
    )

    keyboard = arrange_buttons(sections, "section")
    keyboard = add_contact_and_back(keyboard)
    await update.message.reply_text(welcome_message, reply_markup=InlineKeyboardMarkup(keyboard))

# التعامل مع أزرار التصفح
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import traceback
    try:
        query = update.callback_query
        await query.answer()
        data = query.data.split("_")
        level = data[0]

        if level == "section":
            index = int(data[1])
            section = context.user_data["sections"][index]
            path = os.path.join(PDF_ROOT, section)
            semesters = os.listdir(path)
            semesters = [s for s in semesters if os.path.isdir(os.path.join(path, s))]
            context.user_data.update({"semesters": semesters, "selected_section": section})
            keyboard = arrange_buttons(semesters, "semester")
            keyboard = add_contact_and_back(keyboard, "back_to_sections")
            await query.edit_message_text(f"📖 القسم: {section}\nاختر الفصل:", reply_markup=InlineKeyboardMarkup(keyboard))

        elif level == "semester":
            index = int(data[1])
            semester = context.user_data["semesters"][index]
            section = context.user_data["selected_section"]
            path = os.path.join(PDF_ROOT, section, semester)
            subjects = os.listdir(path)
            subjects = [s for s in subjects if os.path.isdir(os.path.join(path, s))]
            context.user_data.update({"subjects": subjects, "selected_semester": semester})
            keyboard = arrange_buttons(subjects, "subject")
            keyboard = add_contact_and_back(keyboard, "back_to_semesters")
            await query.edit_message_text(f"📖 الفصل: {semester}\nاختر المادة:", reply_markup=InlineKeyboardMarkup(keyboard))

        elif level == "subject":
            index = int(data[1])
            subject = context.user_data["subjects"][index]
            section = context.user_data["selected_section"]
            semester = context.user_data["selected_semester"]
            path = os.path.join(PDF_ROOT, section, semester, subject)
            files = [f for f in os.listdir(path) if f.endswith(".pdf")]
            context.user_data.update({"files": files, "selected_subject": subject})
            keyboard = [[InlineKeyboardButton(f, callback_data=f"file_{i}")] for i, f in enumerate(files)]
            keyboard = add_contact_and_back(keyboard, "back_to_subjects")
            await query.edit_message_text(f"📘 المادة: {subject}\nاختر الملف:", reply_markup=InlineKeyboardMarkup(keyboard))

        elif level == "file":
            index = int(data[1])
            file_name = context.user_data["files"][index]
            section = context.user_data["selected_section"]
            semester = context.user_data["selected_semester"]
            subject = context.user_data["selected_subject"]
            file_path = os.path.join(PDF_ROOT, section, semester, subject, file_name)
            await query.message.reply_document(document=open(file_path, "rb"))

        elif query.data == "back_to_subjects":
            semester = context.user_data["selected_semester"]
            subjects = context.user_data["subjects"]
            keyboard = arrange_buttons(subjects, "subject")
            keyboard = add_contact_and_back(keyboard, "back_to_semesters")
            await query.edit_message_text(f"📖 الفصل: {semester}\nاختر المادة:", reply_markup=InlineKeyboardMarkup(keyboard))

        elif query.data == "back_to_semesters":
            section = context.user_data["selected_section"]
            semesters = context.user_data["semesters"]
            keyboard = arrange_buttons(semesters, "semester")
            keyboard = add_contact_and_back(keyboard, "back_to_sections")
            await query.edit_message_text(f"📖 القسم: {section}\nاختر الفصل:", reply_markup=InlineKeyboardMarkup(keyboard))

        elif query.data == "back_to_sections":
            sections = context.user_data["sections"]
            keyboard = arrange_buttons(sections, "section")
            keyboard = add_contact_and_back(keyboard)
            await query.edit_message_text("📚 اختر القسم العلمي:", reply_markup=InlineKeyboardMarkup(keyboard))

    except Exception as e:
        print("❌ خطأ:", e)
        traceback.print_exc()

# تشغيل البوت
def main():
    print("🚀 جاري تشغيل البوت...")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    print("✅ تم تشغيل البوت بنجاح، يمكنك الآن مراسلته على تيليجرام.")
    app.run_polling()

if __name__ == "__main__":
    main()
