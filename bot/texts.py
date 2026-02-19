# -*- coding: utf-8 -*-
"""
Bot static messages in Uzbek.
"""

# Common
WELCOME = (
    "Assalomu alaykum! Botimizga xush kelibsiz.\n\n"
    "Mahsulot haqida batafsil ma'lumot olish uchun adminlar bilan bog'laning. "
    "Quyidagi adminlar ro'yxati va tugmalar orqali xabar yuborishingiz mumkin."
)
# Oddiy user guruh posti orqali kirmaganda (faqat /start)
WELCOME_USER_ONLY_VIA_GROUP = (
    "Assalomu alaykum!\n\n"
    "Mahsulot haqida batafsil ma'lumot olish uchun adminlar bilan bog'laning. "
    "Quyidagi adminlar ro'yxati va tugmalar orqali xabar yuborishingiz mumkin."
)
USER_CONTACT_ONLY_VIA_GROUP = (
    "Mahsulot haqida batafsil ma'lumot olish uchun adminlar bilan bog'laning. "
    "Xabaringizni yuboring — adminlar guruhiga yetkaziladi."
)
LEAD_SENT = (
    "Sizning xabaringiz adminlarga yuborildi. Tez orada aloqaga chiqishadi."
)
LEAD_SENT_NO_GROUP = (
    "Xabar qabul qilindi. Lead guruhi hali sozlanmagan bo'lsa adminlar keyinroq ko'radi."
)
LEAD_SENT_FAILED = (
    "Xabar qabul qilindi, lekin adminlar guruhiga yuborishda texnik xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring yoki adminlarga murojaat qiling."
)
LEAD_RATE_LIMIT = (
    "Juda ko'p xabar yubordingiz. Iltimos, biroz kutib qayta urinib ko'ring."
)
CONTACT_ADMIN = "Admin bilan bog'lanish"
TAKE_LEAD = "Leadni olish"
ADMIN_LIST = "Adminlar ro'yxati"
BACK = "Orqaga"

# Admin / Owner
HELP_HEADER = "Buyruqlar (admin/egasi):"
HELP_GUIDE = (
    "Qisqa qo'llanma:\n"
    "1) Post qo'shish: rasm/video yoki matn yuboring, so'ng Yakunlash.\n"
    "2) Nashr vaqtlari: vaqt tanlang va Post tanlash tugmasi bilan post biriktiring.\n"
    "3) Nashrni yoqish/o'chirish: inline menyudan yoki post sahifasidan.\n"
    "4) Guruh sozlamalari: target_group va admin_group ni /set_* orqali belgilang.\n"
)
CMD_START = "/start - Boshlash"
CMD_HELP = "/help - Yordam"
CMD_SET_TIMES = "/set_times - Nashr vaqtlarini sozlash (masalan: 09:00, 14:00, 18:00)"
CMD_POST_ON = "/post_on - Kunlik nashrni yoqish"
CMD_POST_OFF = "/post_off - Kunlik nashrni o'chirish"
CMD_HISTORY = "/history - Postlar tarixi"
CMD_DELETE_POST = "/delete_post - Postni o'chirish (ID orqali)"
CMD_ACTIVATE_POST = "/activate_post (id) - Postni qayta aktiv qilish"
CMD_ADD_TEXT = "/add_text - Faqat matn post qo'shish (masalan: /add_text Reklama matni)"
ADD_TEXT_EMPTY = "Matn kiriting. Masalan: /add_text Reklama matni shu yerda"
CMD_SET_TARGET_GROUP = "/set_target_group - Nashr guruhini o'rnatish (guruhda yuboring)"
CMD_SET_ADMIN_GROUP = "/set_admin_group - Leadlar yuboriladigan admin guruhini o'rnatish"
CMD_ADD_ADMIN = "/add_admin - Admin qo'shish (faqat egasi)"
CMD_REMOVE_ADMIN = "/remove_admin - Adminni olib tashlash (faqat egasi)"
CMD_LIST_ADMINS = "/list_admins - Adminlar ro'yxati (faqat egasi)"

POSTING_ON = "Post joylash yoqildi."
POSTING_OFF = "Post joylash o'chirildi."
TIMES_SET = "Nashr vaqtlari yangilandi."
TARGET_GROUP_SET = "Nashr guruhi o'rnatildi."
TARGET_GROUP_PROMPT_ID = "Nashr guruhi ID sini kiriting (masalan -1001234567890):"
TARGET_GROUP_ID_RECEIVED = "ID qabul qilindi. Botni shu guruhga qo'shing va admin sifatida qo'ying. Keyin tasdiqlang."
BTN_CONFIRM_TARGET_GROUP = "Guruhni belgilash"
ADMIN_GROUP_SET = "Admin guruhi o'rnatildi."
ADMIN_GROUP_PROMPT_ID = "Lead guruhi ID sini kiriting (masalan -1001234567890):"
ADMIN_GROUP_ID_RECEIVED = "ID qabul qilindi. Botni shu guruhga qo'shing va admin qiling. Keyin tasdiqlang."
BTN_CONFIRM_ADMIN_GROUP = "Guruhni belgilash"
GROUP_ID_SHOULD_BE_NEGATIVE = "Guruh ID odatda manfiy bo'ladi (masalan -1001234567890). Iltimos, guruhda /set_target_group yuborib oling yoki to'g'ri manfiy ID kiriting."
CONTENT_SAVED = "Kontent saqlandi va aktiv post sifatida belgilandi."
NO_ACTIVE_CONTENT = "Aktiv post yo'q. Avval kontent yuboring (rasm, video yoki matn)."
# Post qo'shish oqimi
BTN_ADD_POST = "➕ Post qo'shish"
POST_ADD_SEND_MEDIA = "Post uchun rasm yoki video yuboring."
POST_ADD_SEND_CAPTION = "Matn (caption) yozing (ixtiyoriy) yoki «Yakunlash» tugmasini bosing."
POST_ADD_CAPTION_ADDED = "Matn qo'shildi. «Yakunlash» tugmasini bosing."
POST_ADD_SAVED = "Post saqlandi va aktiv post sifatida belgilandi."
POST_ADD_CANCELLED = "Bekor qilindi."
BTN_POST_CONFIRM = "✅ Yakunlash"
BTN_POST_CANCEL = "❌ Bekor qilish"
HISTORY_HEADER = "Postlar tarixi (oxirgi 10):"
HISTORY_SINGLE_HEADER = "Post #{id} | {content_type} | yaratilgan: {created_at} | oxirgi nashr: {posted}"
HISTORY_CAPTION_LABEL = "Matn (caption):"
BTN_HISTORY_BACK = "◀️ Orqaga"
POST_DELETED = "Post o'chirildi (endi nashr etilmaydi)."
POST_ACTIVATED = "Post aktiv qilindi (endi guruhga nashr etiladi)."
POST_NOT_FOUND = "Bunday post topilmadi yoki allaqachon o'chirilgan."
POST_ALREADY_ACTIVE = "Bu post allaqachon aktiv."
SCHEDULE_ADDED = "Vaqt qo'shildi: {}"
SCHEDULE_REMOVED = "Vaqt olib tashlandi: {}"
SCHEDULE_INVALID = "Vaqt noto'g'ri. Masalan: 09:00 yoki 14:30"
CURRENT_TIMES = "Joriy post joylash vaqtlari: {}"
ADMIN_ADDED = "Admin qo'shildi."
ADMIN_REMOVED = "Admin olib tashlandi."
ADMIN_ALREADY = "Bu foydalanuvchi allaqachon admin."
ADMIN_NOT_FOUND = "Admin topilmadi."
REPLY_TO_ADD_ADMIN = "Admin qo'shish uchun foydalanuvchi xabariga reply qiling va /add_admin yozing."
ADMIN_ADD_PROMPT = (
    "Yangi adminning Telegram ID sini kiriting (faqat raqam, masalan 123456789). "
    "ID ni @userinfobot orqali olish mumkin."
)
ADMIN_ADD_INVALID_ID = "Faqat raqam (Telegram ID) kiriting. Masalan: 123456789"
REPLY_TO_REMOVE_ADMIN = "Adminni olib tashlash uchun uning xabariga reply qiling va /remove_admin yozing."
OWNER_ONLY = "Bu buyruqni faqat bot egasi ishlata oladi."
ADMIN_ONLY = "Bu buyruqni faqat adminlar ishlata oladi."
LIST_ADMINS_HEADER = "Adminlar:"

# Lead forward format (to admin group)
LEAD_FORWARD_TEMPLATE = (
    "📩 Yangi lead\n"
    "👤 Ism: {name}\n"
    "🆔 Username: @{username}\n"
    "🆔 ID: {user_id}\n"
    "📞 Tel: {phone}\n"
    "💬 Xabar: {text}\n"
    "📌 Manba post: {source}"
)
LEAD_SOURCE_UNKNOWN = "noma'lum"
LEAD_TAKEN = "Lead sizga biriktirildi. Foydalanuvchiga javob yozing."
LEAD_ALREADY_TAKEN = "Bu leadni boshqa admin allaqachon oldi."

# Inline when bot posts in group (guruhdagi post ostida — botga post konteksti bilan)
CONTACT_ADMIN_BUTTON = "Admin bilan bog'lanish"
BTN_CONTACT_ADMINS_UNDER_POST = "📩 Adminlar bilan bog'lanish"

# Reply / Inline button labels
BTN_USER_WRITE = "📩 Xabar yuborish"
BTN_HELP = "📋 Yordam"
BTN_HISTORY = "📜 Postlar tarixi"
BTN_POST_ON = "✅ Post joylashni yoqish"
BTN_POST_OFF = "❌ Post joylashni o'chirish"
BTN_SCHEDULE = "⏰ Post vaqtlari"
BTN_TARGET_GROUP = "📢 Nashr guruhi"
BTN_LEAD_GROUP = "👥 Lead guruhi"
BTN_ADMINS = "👤 Adminlar"
BTN_USER_ADMINS = "👥 Adminlar ro'yxati"
BTN_ADMIN_LIST = "Ro'yxat"
BTN_ADMIN_ADD_HINT = "Qo'shish (reply)"
BTN_ADMIN_REMOVE_HINT = "O'chirish (reply)"
BTN_BACK = "◀️ Orqaga"
BTN_REFRESH_HISTORY = "🔄 Yangilash"
BTN_ADD_TIME = "➕ Vaqt qo'shish"
BTN_INLINE_HISTORY = "📜 Postlar tarixi"
BTN_INLINE_SCHEDULE = "⏰ Nashr vaqtlari"
BTN_INLINE_POST_ON = "✅ Joylashni yoqish"
BTN_INLINE_POST_OFF = "❌ Joylashni o'chirish"
SCHEDULE_ADD_TIME_HINT = "Post joylash uchun yangi vaqtni 09:00 formatida yuboring yoki /set_times 09:00 12:00 buyrug'ini ishlating."
BTN_POST_NOW = "Hozir joylash"
POST_NOW_SUCCESS = "Post guruhga yuborildi."
POST_NOW_FAILED = "Post yuborish amalga oshmadi (guruh yoki kontent tekshiring)."
SCHEDULE_PICK_HOUR = "Soatni tanlang"
SCHEDULE_PICK_MINUTE = "Minutni tanlang"
SCHEDULE_TIME_ADDED = "Vaqt qo'shildi."
POST_NOT_ASSIGNED = "Post tanlanmagan"
BTN_ASSIGN_POST = "Post tanlash"
SCHEDULE_ASSIGNED = "Post vaqtga biriktirildi."
SCHEDULE_PICK_POST_HEADER = "Ushbu vaqt uchun post tanlang:"
NASHR_TIMES_LABEL = "Post joylash vaqtlari:"
PUBLISHING_ENABLED = "Nashr yoqilgan"
PUBLISHING_DISABLED = "Nashr o'chirilgan"
BTN_PUBLISHING_ON = "Nashr yoqish"
BTN_PUBLISHING_OFF = "Nashr o'chirish"
USER_WRITE_HINT = "Quyida xabaringizni yozing — adminlar ko'radi va javob beradi."
USER_PICK_PRODUCT = "Qaysi mahsulot (post) haqida yozmoqchisiz? Quyidagilardan birini tanlang yoki «Umumiy savol» ni bosing."
USER_CONTACT_RECEIVED = "Raqam qabul qilindi. Endi xabaringizni yuboring."
USER_ADMINS_LIST_HEADER = "Adminlar bilan bog'lanish uchun quyidagi tugmalar orqali chatga o'ting."
BTN_NAV_BACK = "◀️ Orqaga"
BTN_NAV_HOME = "🏠 Bosh menyu"
BTN_NAV_REFRESH = "🔄 Yangilash"
