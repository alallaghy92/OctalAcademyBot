import os
import json
import traceback
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler

# إعدادات البيئة
BOT_TOKEN = os.environ.get("BOT_TOKEN")
PDF_ROOT = os.environ.get("PDF_ROOT", "PDF_Files")
DEVELOPER_USERNAME = os.environ.get("DEVELOPER_USERNAME", "@mr_alallaghy")

USERS_FILE = "users.json"  # ملف لتخزين معرفات المستخدمين

# رسائل التذكير
MORNING_AZKAR = "🌞 أذكار الصباح:\n\n🕋 أصبحنا وأصبح الملك لله..."
EVENING_AZKAR = "🌙 أذكار المساء:\n\n🕋 أمسينا وأمسى الملك لله..."
SURAT_AL_KAHF = "📖 تذكير بقراءة سورة الكهف اليوم.\n\nقال النبي ﷺ: \"من قرأ سورة الكهف يوم الجمعة أضاء له من النور ما بين الجمعتين\""

# تأكد من وجود التوكن
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN غير موجود في متغيرات البيئة!")


# ---------------------- وظائف مساعدة ----------------------

def load_users():
    """تحميل قائمة المستخدمين من ملف JSON."""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_users(users):
    """حفظ قائمة المستخدمين في ملف JSON."""
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def add_user(user_id):
    """إضافة مستخدم جديد إن لم يكن موجودًا."""
    users = load_users()
    if user_id not in users:
        users.append(user_id)
        save_users(users)
        print(f"✅ تم حفظ مستخدم جديد: {user_id}")


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


def add_contact_and_back(keyboard, back_callback=None):
    if back_callback:
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data=back_callback)])
    keyboard.append([InlineKeyboardButton("📩 تواصل مع المطور", url=f"https://t.me/{DEVELOPER_USERNAME[1:]}")])
    return keyboard


# ---------------------- أوامر البوت ----------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عند تنفيذ /start"""
    user_id = update.effective_user.id
    add_user(user_id)
    print(f"✅ المستخدم {user_id} بدأ المحادثة.")

    # رسالة الترحيب
    welcome_message = (
        "🌟 مرحبًا بك في بوت أكادمية أوكتال .\n\n"
        "🌟 نحن هنا لمساعدتك في البحث عن المقررات الدراسية لجميع المواد .\n\n"
        "📚 بُني هذا العمل بمجهود مجموعة من الطلبة والمساهمين، "
        "الذين جمعوا ونسّقوا هذه الملفات لتكون عونًا لكل باحثٍ عن العلم.\n\n"
        "💖 نرجو منك دعوةً طيبة بظهر الغيب، "
        "لعلّ الله يكتب بها الأجر لكل من شارك وساهم في إعداد هذا العمل.\n\n"
        "📘 اختر القسم العلمي لبدء التصفح:"
    )

    # تحقق من المجلدات
    if not os.path.exists(PDF_ROOT):
        await context.bot.send_message(chat_id=user_id, text="❌ لم يتم العثور على مجلد PDF_Files في نفس مسار البوت.")
        await context.bot.send_message(chat_id=user_id, text=welcome_message)
        return

    sections = [s for s in os.listdir(PDF_ROOT) if os.path.isdir(os.path.join(PDF_ROOT, s))]
    if not sections:
        await context.bot.send_message(chat_id=user_id, text="📂 لا توجد أقسام داخل مجلد PDF_Files.")
        await context.bot.send_message(chat_id=user_id, text=welcome_message)
        return

    context.user_data["sections"] = sections

    keyboard = arrange_buttons(sections, "section")
    keyboard = add_contact_and_back(keyboard)

    await context.bot.send_message(
        chat_id=user_id,
        text=welcome_message,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
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


# ---------------------- جدولة التذكيرات ----------------------

def send_reminders(app, text):
    """إرسال التذكير لجميع المستخدمين."""
    users = load_users()
    for uid in users:
        try:
            app.bot.send_message(chat_id=uid, text=text)
        except Exception as e:
            print(f"⚠️ لم يتمكن البوت من إرسال الرسالة للمستخدم {uid}: {e}")


def schedule_reminders(app):
    scheduler = BackgroundScheduler()

    scheduler.add_job(lambda: send_reminders(app, MORNING_AZKAR),
                      trigger='cron', hour=8, minute=0)

    scheduler.add_job(lambda: send_reminders(app, EVENING_AZKAR),
                      trigger='cron', hour=17, minute=0)

    scheduler.add_job(lambda: send_reminders(app, SURAT_AL_KAHF),
                      trigger='cron', day_of_week='fri', hour=8, minute=0)

    scheduler.start()


# ---------------------- تشغيل البوت ----------------------

def main():
    print("🚀 جاري تشغيل البوت...")
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))

    schedule_reminders(app)

    print("✅ تم تشغيل البوت بنجاح.")
    app.run_polling()


if __name__ == "__main__":
    main()
