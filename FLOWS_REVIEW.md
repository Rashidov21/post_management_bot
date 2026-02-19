# Flow'lar va mantiqiy tekshiruv

## 1. User flow (oddiy foydalanuvchi)

| Qadam | Handler / joy | Izoh |
|-------|----------------|------|
| `/start` (deep link `?start=post_123`) | `user.cmd_start_deep` | User yaratiladi, `_lead_source_by_user[uid]=123`, admin/owner bo‘lsa admin klaviaturasi, yo‘q bo‘lsa user klaviaturasi + adminlar ro‘yxati. |
| `/start` (oddiy) | `user.cmd_start` | Admin/owner bo‘lsa admin menyu, yo‘q bo‘lsa "faqat guruh orqali" + adminlar ro‘yxati. |
| "📩 Xabar yuborish" | `user.btn_user_write` | Agar `_lead_source_by_user` da bo‘lsa (post link orqali kirdi) → faqat "Xabaringizni yozing". Aks holda → post tanlash inline (mahsulot yoki "Umumiy savol"). |
| Post tanlash (callback `choose_lead_post_*`) | `user.cb_choose_lead_post` | `_lead_source_by_user` ga yoziladi yoki tozalanadi, "Xabaringizni yozing" ko‘rsatiladi. |
| "👥 Adminlar ro'yxati" | `user.btn_user_admins` | Adminlar ro‘yxati inline tugmalar bilan (Chat — ism), ID ko‘rsatilmaydi. |
| Kontakt yuborish | `user.user_contact_for_lead` | Telefon keyingi lead xabariga biriktiriladi. |
| Istalgan matn (buyruq/tugma emas) | `user.private_message_as_lead` | Rate limit, lead yaratiladi, agar `admin_group_id` o‘rnatilgan bo‘lsa lead guruhiga yuboriladi, aks holda faqat DB. |

**Tuzatilgan / holat:**
- Lead guruhi yo‘q: `LEAD_SENT_NO_GROUP` ko‘rsatiladi.
- Guruhga yuborish xatosi: `LEAD_SENT_FAILED` — "Xabar qabul qilindi, lekin adminlar guruhiga yuborishda texnik xatolik…" ko‘rsatiladi.

---

## 2. Admin flow

| Qadam | Handler / joy | Izoh |
|-------|----------------|------|
| /help, Yordam, Post qo‘shish, Nashr, Tarix, Nashr guruhi, Lead guruhi | admin router | AdminOnlyMiddleware: faqat admin yoki owner o‘tkaziladi. |
| Lead guruhi | `cmd_set_admin_group_private` / guruhda `/set_admin_group` | ID kiritish yoki guruhda buyruq — `admin_group_id` saqlanadi. |
| Post qo‘shish | rasm/video/caption → confirm/cancel | `_post_add_pending`, `content_service.add_content`. |
| Vaqt qo‘shish | soat → minut → `schedule_service.add_schedule` | **Kamchilik:** yangi vaqt faqat DB ga yoziladi, scheduler da yangi job qo‘shilmaydi — nashr faqat bot qayta ishga tushgach ishlaydi. |
| Post vaqtga biriktirish | assign_post → post tanlash → assign_schedule_*_content_* | `content_schedule` jadvali yangilanadi. |
| Tarix | postlar ro‘yxati, o‘chirish, aktivlashtirish, "Hozir yuborish" | |
| Leadlar (inline) | "🧾 Leadlar" → javob berilmagan leadlar, Reply #id, Chat, Leadni olish | `admin_reply_to_lead_text`, `cb_take_lead`, `mark_lead_answered`. |
| Admin qo‘shish (owner) | Adminlar → Qo‘shish → ID kiritish | `_admin_add_awaiting`, faqat owner. |

**Tuzatilgan / holat:**
- **Scheduler:** Yangi vaqt qo‘shilganda/o‘chirilganda `scheduler_runner` orqali job qo‘shiladi/o‘chiriladi.
- **Leadni olish:** `lead_actions_keyboard` da "✉️ Javob berish" va "Leadni olish" (callback `take_lead_{id}`), "💬 Chatga o'tish" mavjud.

---

## 3. Owner flow

| Qadam | Handler / joy | Izoh |
|-------|----------------|------|
| "👤 Adminlar" | `owner.btn_admins` | OwnerOnlyMiddleware (faqat Message). Inline: Ro‘yxat, Qo‘shish, O‘chirish. |
| Admin ro‘yxati / o‘chirish / qo‘shish | callback’lar | Har birida `is_owner()` qo‘lda tekshiriladi (OwnerOnlyMiddleware faqat Message uchun). |

**Kamchiliklar / tavsiyalar:**
- OwnerOnlyMiddleware faqat `Message` uchun ishlaydi; callback’lar to‘g‘ridan-to‘g‘ri handler ga keladi, lekin handler ichida `is_owner` tekshirilgani uchun xavfsiz.

---

## 4. Router va middleware tartibi

- **user** → **admin** (AdminOnlyMiddleware) → **owner** (OwnerOnlyMiddleware).
- Admin/owner tugma matnlari user router da `_ADMIN_OWNER_BUTTONS` da; lead handler ularni ushlamaydi.
- Admin router da `admin_reply_to_lead_text` faqat `_REPLY_IGNORE_TEXTS` da bo‘lmagan matnni ushlaydi, shuning uchun "Adminlar" / "Lead guruhi" owner/admin handlerlariga yetadi.

---

## 5. Boshqa mantiqiy nuqtalar

- **Rate limit:** soatiga 10 ta lead (config). 11-chi xabar bloklanadi.
- **Lead guruhi yo‘q:** lead DB ga yoziladi, foydalanuvchiga "yuborildi" deyiladi — yuqorida yozilgan UX muammosi.
- **Deep link source:** Bot qayta ishga tushsa `_lead_source_by_user` tozalanadi; user keyin xabar yuborsa source yo‘qoladi — qabul qilinadi.
- **assign_post_0:** Agar `schedule.id` None bo‘lsa (normally bo‘lmasligi kerak) "Post tanlash" `assign_post_0` beradi; schedule_id=0 DB da mavjud emas — chegaraviy holat, amalda kam.

---

## 6. Xulosa: ustun beriladigan tuzatishlar

1. ~~**Scheduler:** Yangi vaqt qo‘shilganda yangi cron job qo‘shish~~ — **Tuzatildi:** `bot/scheduler/runner.py` orqali "Vaqt qo‘shish" va vaqt o‘chirishda job qo‘shiladi/o‘chiriladi; `/set_times` orqali qo‘shilgan vaqtlar uchun ham job qo‘shiladi.
2. ~~**Lead guruhi yo‘q:** Aniqroq xabar~~ — **Tuzatildi:** `LEAD_SENT_NO_GROUP` — lead guruhi sozlanmagan bo‘lsa shu xabar ko‘rsatiladi.
3. ~~**Guruhga yuborish xatosi**~~ — **Tuzatildi:** `LEAD_SENT_FAILED` — guruhga yuborishda exception bo‘lsa foydalanuvchiga shu xabar ko‘rsatiladi.
4. ~~**Leadni olish tugmasi**~~ — **Tuzatildi:** `lead_actions_keyboard` ga "Leadni olish" tugmasi qo‘shildi (`take_lead_{id}`).
