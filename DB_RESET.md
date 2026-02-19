# Bot DB ni 0 qilib, noldan ishga tushirish

Bazani to‘liq tozalab, botni yangi DB bilan ishga tushirish ketma-ketligi.

---

## 1. Botni to‘xtatish

```bash
sudo systemctl stop postbot
```

Agar bot qo‘lda ishlayotgan bo‘lsa: terminalda **Ctrl+C**.

---

## 2. Loyiha papkasiga o‘tish

```bash
cd /opt/post_management_bot
# yoki loyiha joyi: cd /path/to/post_management_bot
```

---

## 3. Backup (ixtiyoriy)

Eski DB ni saqlab olish:

```bash
cp -r data data.backup.$(date +%Y%m%d)
# yoki faqat: cp data/bot.db data/bot.db.backup
```

---

## 4. DB va data ni tozalash

```bash
rm -f data/bot.db
```

Barcha `data` ni tozalash (kerak bo‘lsa):

```bash
rm -rf data/*
mkdir -p data
```

---

## 5. .env tekshirish

```bash
cat .env
```

Kamida bo‘lishi kerak:

- `BOT_TOKEN=<@BotFather dan token>`
- `OWNER_ID=<Telegram user ID>` yoki `OWNER_IDS=id1,id2`
- Ixtiyoriy: `DATABASE_PATH=data/bot.db`, `SCHEDULER_TIMEZONE=Asia/Tashkent`

---

## 6. Virtual muhit va dependencies

```bash
source .venv/bin/activate
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## 7. Kod yangilash (serverda git bo‘lsa)

```bash
git pull
```

---

## 8. Botni bir marta ishga tushirish (DB yaratilishi uchun)

```bash
python main.py
```

Bir necha soniya kutib, logda database init ko‘rinsa **Ctrl+C** bilan to‘xtating.

---

## 9. DB yaratilganini tekshirish

```bash
ls -la data/
```

`data/bot.db` fayli paydo bo‘lishi kerak.

---

## 10. Botni doimiy ishga tushirish (systemd)

```bash
sudo systemctl start postbot
sudo systemctl status postbot
```

Loglarni kuzatish:

```bash
journalctl -u postbot -f
```

---

## 11. Sozlamalarni qayta belgilash

DB yangi bo‘lgani uchun barcha sozlamalar qayta o‘rnatiladi:

| Nima | Qanday |
|------|--------|
| **Nashr guruhi** | O‘sha guruhda `/set_target_group` yoki botda "📢 Nashr guruhi" → ID |
| **Lead guruhi** | Leadlar keladigan guruhda `/set_admin_group` yoki botda "👥 Lead guruhi" → ID |
| **Adminlar** | Owner: "👤 Adminlar" → "Qo'shish" → Telegram ID |
| **Postlar** | Botda "Post qo'shish" orqali rasm/video/matn |
| **Vaqtlar** | "⏰ Post vaqtlari" → Vaqt qo'shish, post biriktirish |
| **Nashr** | "✅ Post joylashni yoqish" |

---

## Qisqa checklist

| # | Qadam | Buyruq |
|---|--------|--------|
| 1 | To‘xtatish | `sudo systemctl stop postbot` |
| 2 | Papka | `cd /opt/post_management_bot` |
| 3 | Backup | `cp -r data data.backup.$(date +%Y%m%d)` |
| 4 | DB o‘chirish | `rm -f data/bot.db` |
| 5 | .env | `BOT_TOKEN`, `OWNER_ID` / `OWNER_IDS` |
| 6 | Venv | `source .venv/bin/activate && pip install -r requirements.txt` |
| 7 | Kod | `git pull` |
| 8 | Bir marta ishga tushirish | `python main.py` → Ctrl+C |
| 9 | Tekshirish | `ls -la data/bot.db` |
| 10 | Ishga tushirish | `sudo systemctl start postbot` |
| 11 | Sozlamalar | Lead guruhi, nashr guruhi, adminlar, postlar, vaqtlar |
