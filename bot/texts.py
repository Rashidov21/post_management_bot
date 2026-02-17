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
CMD_SET_BANNER = "/set_banner - Asosiy banner rasmni o'rnatish"
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
BANNER_SET = "Asosiy banner rasm o'rnatildi."
CONTENT_SAVED = "Kontent saqlandi va aktiv post sifatida belgilandi."
NO_ACTIVE_CONTENT = "Aktiv post yo'q. Avval kontent yuboring (rasm, video yoki matn)."
HISTORY_HEADER = "Postlar tarixi (oxirgi 20):"
POST_DELETED = "Post o'chirildi (endi nashr etilmaydi)."
POST_NOT_FOUND = "Bunday post topilmadi yoki allaqachon o'chirilgan."
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
    "💬 Xabar: {text}\n"
    "📌 Manba post: {source}"
)
LEAD_SOURCE_UNKNOWN = "noma'lum"
LEAD_TAKEN = "Lead sizga biriktirildi. Foydalanuvchiga javob yozing."
LEAD_ALREADY_TAKEN = "Bu leadni boshqa admin allaqachon oldi."

# Inline when bot posts in group
CONTACT_ADMIN_BUTTON = "Admin bilan bog'lanish"
