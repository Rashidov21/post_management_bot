# -*- coding: utf-8 -*-
"""
Bot static messages in Uzbek.
"""

# Common
WELCOME = (
    "Assalomu alaykum! Botimizga xush kelibsiz.\n\n"
    "Reklama postlari guruhda vaqtida nashr etiladi. "
    "Savol yoki taklifingiz bo'lsa, quyidagi tugma orqali adminlar bilan bog'laning."
)
# Oddiy user guruh posti orqali kirmaganda (faqat /start)
WELCOME_USER_ONLY_VIA_GROUP = (
    "Assalomu alaykum!\n\n"
    "Adminlar bilan bog'lanish uchun guruhdagi reklama postidagi "
    "'Admin bilan bog'lanish' tugmasini bosing. Shundan keyin xabaringizni yuborishingiz mumkin."
)
USER_CONTACT_ONLY_VIA_GROUP = (
    "Adminlar bilan bog'lanish uchun avval guruhdagi reklama postidagi "
    "'Admin bilan bog'lanish' tugmasini bosing, keyin xabar yuboring."
)
LEAD_SENT = (
    "Sizning xabaringiz adminlarga yuborildi. Tez orada aloqaga chiqishadi."
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
CMD_START = "/start - Boshlash"
CMD_HELP = "/help - Yordam"
CMD_SET_TIMES = "/set_times - Nashr vaqtlarini sozlash (masalan: 09:00, 14:00, 18:00)"
CMD_POST_ON = "/post_on - Kunlik nashrni yoqish"
CMD_POST_OFF = "/post_off - Kunlik nashrni o'chirish"
CMD_HISTORY = "/history - Postlar tarixi"
CMD_DELETE_POST = "/delete_post - Postni o'chirish (ID orqali)"
CMD_ACTIVATE_POST = "/activate_post (id) - Postni qayta aktiv qilish"
CMD_SET_BANNER = "/set_banner - Asosiy banner rasmni o'rnatish"
CMD_ADD_TEXT = "/add_text - Faqat matn post qo'shish (masalan: /add_text Reklama matni)"
ADD_TEXT_EMPTY = "Matn kiriting. Masalan: /add_text Reklama matni shu yerda"
CMD_SET_TARGET_GROUP = "/set_target_group - Nashr guruhini o'rnatish (guruhda yuboring)"
CMD_SET_ADMIN_GROUP = "/set_admin_group - Leadlar yuboriladigan admin guruhini o'rnatish"
CMD_ADD_ADMIN = "/add_admin - Admin qo'shish (faqat egasi)"
CMD_REMOVE_ADMIN = "/remove_admin - Adminni olib tashlash (faqat egasi)"
CMD_LIST_ADMINS = "/list_admins - Adminlar ro'yxati (faqat egasi)"

POSTING_ON = "Kunlik nashr yoqildi."
POSTING_OFF = "Kunlik nashr o'chirildi."
TIMES_SET = "Nashr vaqtlari yangilandi."
TARGET_GROUP_SET = "Nashr guruhi o'rnatildi."
ADMIN_GROUP_SET = "Admin guruhi o'rnatildi."
GROUP_ID_SHOULD_BE_NEGATIVE = "Guruh ID odatda manfiy bo'ladi (masalan -1001234567890). Iltimos, guruhda /set_target_group yuborib oling yoki to'g'ri manfiy ID kiriting."
BANNER_SET = "Asosiy banner rasm o'rnatildi."
CONTENT_SAVED = "Kontent saqlandi va aktiv post sifatida belgilandi."
NO_ACTIVE_CONTENT = "Aktiv post yo'q. Avval kontent yuboring (rasm, video yoki matn)."
HISTORY_HEADER = "Postlar tarixi (oxirgi 20):"
POST_DELETED = "Post o'chirildi (endi nashr etilmaydi)."
POST_ACTIVATED = "Post aktiv qilindi (endi guruhga nashr etiladi)."
POST_NOT_FOUND = "Bunday post topilmadi yoki allaqachon o'chirilgan."
POST_ALREADY_ACTIVE = "Bu post allaqachon aktiv."
SCHEDULE_ADDED = "Vaqt qo'shildi: {}"
SCHEDULE_REMOVED = "Vaqt olib tashlandi: {}"
SCHEDULE_INVALID = "Vaqt noto'g'ri. Masalan: 09:00 yoki 14:30"
CURRENT_TIMES = "Joriy nashr vaqtlari: {}"
ADMIN_ADDED = "Admin qo'shildi."
ADMIN_REMOVED = "Admin olib tashlandi."
ADMIN_ALREADY = "Bu foydalanuvchi allaqachon admin."
ADMIN_NOT_FOUND = "Admin topilmadi."
REPLY_TO_ADD_ADMIN = "Admin qo'shish uchun foydalanuvchi xabariga reply qiling va /add_admin yozing."
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

# Inline when bot posts in group
CONTACT_ADMIN_BUTTON = "Admin bilan bog'lanish"

# Reply / Inline button labels
BTN_USER_WRITE = "📩 Xabar yuborish"
BTN_HELP = "📋 Yordam"
BTN_HISTORY = "📜 Postlar tarixi"
BTN_POST_ON = "✅ Nashrni yoqish"
BTN_POST_OFF = "❌ Nashrni o'chirish"
BTN_SCHEDULE = "⏰ Nashr vaqtlari"
BTN_BANNER = "🖼 Banner"
BTN_TARGET_GROUP = "📢 Nashr guruhi"
BTN_LEAD_GROUP = "👥 Lead guruhi"
BTN_ADMINS = "👤 Adminlar"
BTN_USER_ADMINS = "👥 Adminlar ro'yxati"
BTN_ADMIN_LIST = "Ro'yxat"
BTN_ADMIN_ADD_HINT = "Qo'shish (reply)"
BTN_ADMIN_REMOVE_HINT = "O'chirish (reply)"
BTN_BACK = "◀️ Orqaga"
BTN_REFRESH_HISTORY = "🔄 Yangilash"
USER_WRITE_HINT = "Quyida xabaringizni yozing — adminlar ko'radi va javob beradi."
USER_CONTACT_RECEIVED = "Raqam qabul qilindi. Endi xabaringizni yuboring."
USER_ADMINS_LIST_HEADER = "Adminlar bilan bog'lanish uchun quyidagi tugma orqali xabar yuboring."
