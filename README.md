# Post Management Bot

Telegram bot: avtomatik reklama repost, lead yig‘ish, adminlar bilan bog‘lanish, postlar tarixi.

**Texnologiyalar:** Python 3.11+, aiogram 3, SQLite (aiosqlite), APScheduler.

---

## O‘rnatish

```bash
git clone https://github.com/YOUR_USER/post_management_bot.git
cd post_management_bot

python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
# .env da BOT_TOKEN va OWNER_ID ni to‘ldiring
```

## Ishga tushirish

```bash
python main.py
```

---

## Sozlamalar (.env)

| O‘zgaruvchi | Majburiy | Tavsif |
|-------------|----------|--------|
| `BOT_TOKEN` | Ha | @BotFather tokeni |
| `OWNER_ID`  | Ha | Egasi Telegram user ID |
| `DATABASE_PATH` | Yo‘q | Default: `data/bot.db` |
| `LOG_LEVEL` | Yo‘q | Default: `INFO` |
| `LEAD_RATE_LIMIT_PER_HOUR` | Yo‘q | Default: 10 |
| `BOT_DOMAIN` | Yo‘q | Masalan: postbot.rashidevs.uz |

---

## Buyruqlar

### Barcha foydalanuvchilar
- `/start` — botni boshlash

### Adminlar (va egasi)
- `/help` — buyruqlar ro‘yxati
- `/set_times 09:00 14:00 18:00` — nashr vaqtlari
- `/post_on` — kunlik nashrni yoqish
- `/post_off` — kunlik nashrni o‘chirish
- `/history` — postlar tarixi
- `/delete_post <id>` — postni o‘chirish
- Rasm yuborish — yangi kontent (aktiv post)
- Video yuborish — yangi kontent
- Rasm + caption `/set_banner` — asosiy banner
- Nashr guruhida: `/set_target_group`
- Leadlar guruhida: `/set_admin_group`

### Faqat egasi
- `/add_admin` — foydalanuvchi xabariga reply qilib yuborish
- `/remove_admin` — admin xabariga reply qilib yuborish
- `/list_admins` — adminlar ro‘yxati

---

## Rejalashtirilgan nashr

- Vaqtlar `schedules` jadvalida saqlanadi.
- Har safar bot ishga tushganda jadval DB dan yuklanadi.
- Har vaqtda faqat **bitta aktiv post** guruhga yuboriladi.
- Posting `/post_off` bilan o‘chirilganda nashr to‘xtaydi.

---

## Lead yig‘ish

- Guruhdagi postda **«Admin bilan bog‘lanish»** tugmasi botga link beradi.
- Foydalanuvchi botga xabar yuboradi → lead yoziladi va admin guruhiga yuboriladi.
- Admin guruhida **«Leadni olish»** — birinchi bosgan admin leadni oladi.

---

## VPS deploy (systemd)

1. Kodni serverga olib keling (masalan `/opt/post_management_bot`).
2. `.venv` yarating, `pip install -r requirements.txt`, `.env` sozlang.
3. `postbot.service` ni `/etc/systemd/system/` ga nusxalang.
4. `sudo systemctl daemon-reload && sudo systemctl enable postbot && sudo systemctl start postbot`
5. Loglar: `journalctl -u postbot -f`

---

## Docker (ixtiyoriy)

```bash
docker build -t postbot .
docker run -d --name postbot --restart unless-stopped -v $(pwd)/data:/app/data --env-file .env postbot
```

---

## Loyiha tuzilishi

```
bot/
  handlers/   — user, admin, owner
  services/   — content, leads, schedule, settings, admin, user
  database/   — connection, models
  scheduler/  — posting
  keyboards/  — inline
  middlewares/ — admin, owner
main.py
config.py
requirements.txt
```
