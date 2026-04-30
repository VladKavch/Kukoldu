import os
import csv
import smtplib
from dotenv import load_dotenv
load_dotenv()  # завантажує .env з тієї ж папки де app_timer.py
import threading
import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from io import StringIO
from datetime import datetime, timedelta
from flask import Flask, render_template_string, request, jsonify, session, redirect
import sqlite3

app = Flask(__name__)
app.secret_key = 'ukd_secret_key_6000_full_sync'

DATABASE_FILE = 'database.db'

# ─── EMAIL CONFIG ─────────────────────────────────────────────────────────────
# Заповніть перед запуском:
EMAIL_SENDER   = os.environ.get('UKD_EMAIL',    '')
EMAIL_PASSWORD = os.environ.get('UKD_PASSWORD', '')
EMAIL_SMTP     = os.environ.get('UKD_SMTP',     'smtp.gmail.com')
EMAIL_PORT     = int(os.environ.get('UKD_PORT', '587'))

def send_nk_email(student_email: str, student_name: str,
                  subject_name: str, deadline_str: str):
    """Відправляє HTML-лист студенту про НК у фоновому потоці."""
    def _send():
        try:
            # Парсимо дедлайн для красивого відображення
            try:
                dl = datetime.fromisoformat(deadline_str)
                months_ua = ["Січня","Лютого","Березня","Квітня","Травня","Червня",
                             "Липня","Серпня","Вересня","Жовтня","Листопада","Грудня"]
                deadline_pretty = (
                    f"{dl.day} {months_ua[dl.month-1]} {dl.year} р. "
                    f"о {str(dl.hour).zfill(2)}:{str(dl.minute).zfill(2)}"
                )
                # Скільки днів залишилось
                days_left = (dl - datetime.now()).days
                days_text = f"{days_left} дн." if days_left > 0 else "менше доби"
            except Exception:
                deadline_pretty = deadline_str
                days_text = "4 тижні"

            html_body = f"""
<!DOCTYPE html>
<html lang="uk">
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f3f4f6;padding:40px 0;">
    <tr><td align="center">
      <table width="560" cellpadding="0" cellspacing="0"
             style="background:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,.10);">

        <!-- Шапка -->
        <tr>
          <td style="background:#4a0404;padding:32px 40px;text-align:center;">
            <p style="margin:0;font-size:11px;color:rgba(255,255,255,.5);
                      letter-spacing:3px;text-transform:uppercase;">Університет культури і дизайну</p>
            <h1 style="margin:10px 0 0;color:#ffffff;font-size:26px;font-weight:900;
                       letter-spacing:-1px;text-transform:uppercase;">УКД ПЛАТФОРМА</h1>
          </td>
        </tr>

        <!-- Червона смуга НК -->
        <tr>
          <td style="background:#8b0000;padding:14px 40px;text-align:center;">
            <span style="color:#fca5a5;font-size:13px;font-weight:700;
                         letter-spacing:2px;text-transform:uppercase;">
              &#9888; Нова академічна заборгованість
            </span>
          </td>
        </tr>

        <!-- Тіло -->
        <tr>
          <td style="padding:36px 40px 28px;">
            <p style="margin:0 0 6px;color:#6b7280;font-size:14px;">Вітаємо,</p>
            <h2 style="margin:0 0 28px;color:#111827;font-size:20px;font-weight:700;">
              {student_name}
            </h2>

            <!-- Картка предмету -->
            <table width="100%" cellpadding="0" cellspacing="0"
                   style="background:#fef2f2;border:2px solid #fca5a5;
                          border-radius:12px;margin-bottom:24px;">
              <tr>
                <td style="padding:20px 24px;">
                  <p style="margin:0 0 4px;font-size:11px;color:#ef4444;
                             text-transform:uppercase;letter-spacing:1px;font-weight:700;">
                    Предмет
                  </p>
                  <p style="margin:0;font-size:18px;font-weight:800;color:#7f1d1d;">
                    {subject_name}
                  </p>
                </td>
              </tr>
            </table>

            <!-- Дедлайн -->
            <table width="100%" cellpadding="0" cellspacing="0"
                   style="background:#f9fafb;border:1px solid #e5e7eb;
                          border-radius:12px;margin-bottom:28px;">
              <tr>
                <td style="padding:18px 24px;border-right:1px solid #e5e7eb;width:50%;">
                  <p style="margin:0 0 4px;font-size:11px;color:#9ca3af;
                             text-transform:uppercase;letter-spacing:1px;">Дедлайн відробки</p>
                  <p style="margin:0;font-size:15px;font-weight:700;color:#111827;">
                    {deadline_pretty}
                  </p>
                </td>
                <td style="padding:18px 24px;width:50%;text-align:center;">
                  <p style="margin:0 0 4px;font-size:11px;color:#9ca3af;
                             text-transform:uppercase;letter-spacing:1px;">Залишилось</p>
                  <p style="margin:0;font-size:22px;font-weight:900;color:#dc2626;">
                    {days_text}
                  </p>
                </td>
              </tr>
            </table>

            <p style="margin:0 0 24px;font-size:14px;color:#6b7280;line-height:1.6;">
              Щоб закрити заборгованість, зверніться до викладача
              і відробіть пропущене заняття <strong>до вказаного терміну</strong>.
              Після відробки викладач позначить НК як виконане в системі.
            </p>

            <table cellpadding="0" cellspacing="0" style="margin:0 auto;">
              <tr>
                <td style="background:#4a0404;border-radius:10px;padding:14px 36px;
                            text-align:center;">
                  <a href="http://localhost:5000/?tab=timers"
                     style="color:#ffffff;font-size:14px;font-weight:700;
                            text-decoration:none;letter-spacing:.5px;">
                    Переглянути мої НК →
                  </a>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- Підвал -->
        <tr>
          <td style="background:#f9fafb;border-top:1px solid #e5e7eb;
                     padding:18px 40px;text-align:center;">
            <p style="margin:0;font-size:12px;color:#9ca3af;">
              Автоматичне повідомлення від УКД Платформи &mdash; не відповідайте на цей лист.
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>
"""

            msg = MIMEMultipart('alternative')
            msg['Subject'] = f'⚠️ НК з предмету «{subject_name}» — УКД'
            msg['From']    = f'УКД Платформа <{EMAIL_SENDER}>'
            msg['To']      = student_email
            msg.attach(MIMEText(html_body, 'html', 'utf-8'))

            with smtplib.SMTP(EMAIL_SMTP, EMAIL_PORT, timeout=15) as smtp:
                smtp.ehlo()
                smtp.starttls()
                smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
                smtp.sendmail(EMAIL_SENDER, student_email, msg.as_string())

            print(f"[EMAIL] Відправлено до {student_email} ({subject_name})")
        except Exception as ex:
            print(f"[EMAIL ERROR] {ex}")

    threading.Thread(target=_send, daemon=True).start()

# ─── БД ───────────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def migrate_db(conn):
    """Оновлює стару схему БД до нової — безпечно, не видаляючи дані."""
    c = conn.cursor()

    # ── users: додаємо group_name якщо відсутня ──
    cols = {row[1] for row in c.execute("PRAGMA table_info(users)")}
    if 'group_name' not in cols:
        c.execute("ALTER TABLE users ADD COLUMN group_name TEXT DEFAULT ''")

    # ── grades: якщо стара структура (без date_col/is_nk) — перебудовуємо ──
    grade_cols = {row[1] for row in c.execute("PRAGMA table_info(grades)")}
    needs_rebuild = 'date_col' not in grade_cols or 'is_nk' not in grade_cols

    if needs_rebuild:
        # Зберігаємо старі дані
        old_rows = c.execute("SELECT * FROM grades").fetchall()
        old_col_names = [desc[0] for desc in c.description]

        c.execute("DROP TABLE grades")
        c.execute("""
            CREATE TABLE grades (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL REFERENCES users(id),
                subject_id INTEGER NOT NULL REFERENCES subjects(id),
                date_col   TEXT    NOT NULL DEFAULT '',
                grade      TEXT    DEFAULT NULL,
                is_nk      INTEGER DEFAULT 0,
                note       TEXT    DEFAULT '',
                updated_at TEXT    DEFAULT (datetime('now')),
                UNIQUE(student_id, subject_id, date_col)
            )
        """)

        # Мігруємо старі записи: grade_type стає date_col='' (загальний запис)
        if old_rows:
            for row in old_rows:
                row_d = dict(zip(old_col_names, row))
                grade_val = row_d.get('grade')
                # Стара оцінка була INTEGER 1-100, нова — TEXT або NULL
                grade_text = str(grade_val) if grade_val is not None else None
                try:
                    c.execute("""
                        INSERT OR IGNORE INTO grades
                            (student_id, subject_id, date_col, grade, is_nk, note, updated_at)
                        VALUES (?,?,?,?,0,?,?)
                    """, (
                        row_d['student_id'],
                        row_d['subject_id'],
                        row_d.get('grade_type', ''),
                        grade_text,
                        row_d.get('note', ''),
                        row_d.get('updated_at', ''),
                    ))
                except Exception:
                    pass

    # ── journal_dates: створюємо якщо відсутня ──
    tables = {row[0] for row in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if 'journal_dates' not in tables:
        c.execute("""
            CREATE TABLE journal_dates (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id INTEGER NOT NULL REFERENCES subjects(id),
                date_val   TEXT    NOT NULL,
                UNIQUE(subject_id, date_val)
            )
        """)

    conn.commit()


def init_db():
    conn = get_db()
    c = conn.cursor()

    c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            username  TEXT    NOT NULL UNIQUE,
            password  TEXT    NOT NULL,
            role      TEXT    NOT NULL CHECK(role IN ('ADMIN','TEACHER','STUDENT')),
            fullname  TEXT    NOT NULL,
            email     TEXT    NOT NULL UNIQUE,
            avatar    TEXT    DEFAULT 'https://cdn-icons-png.flaticon.com/512/354/354637.png',
            room      TEXT    DEFAULT '',
            course    TEXT    DEFAULT '1',
            specialty TEXT    DEFAULT 'IPZ',
            institution TEXT  DEFAULT 'Universytet',
            group_name TEXT   DEFAULT 'IPZ-21'
        );

        CREATE TABLE IF NOT EXISTS subjects (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT    NOT NULL,
            teacher_id INTEGER REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS absences (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL REFERENCES users(id),
            subject_id INTEGER NOT NULL REFERENCES subjects(id),
            deadline   TEXT    NOT NULL,
            status     TEXT    DEFAULT 'active'
        );

        CREATE TABLE IF NOT EXISTS creators (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            name  TEXT,
            role  TEXT,
            desc  TEXT,
            skills TEXT,
            avatar TEXT DEFAULT ''
        );
    """)

    # Міграція: оновлюємо стару схему якщо потрібно
    migrate_db(conn)
    c = conn.cursor()  # оновлюємо курсор після міграції

    if c.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        _seed(c)

    conn.commit()
    conn.close()

def _seed(c):
    c.executemany("INSERT INTO users (username,password,role,fullname,email,avatar,room,group_name) VALUES (?,?,?,?,?,?,?,?)", [
        ('admin',   '123', 'ADMIN',   'Адміністратор',       'admin@ukd.edu.ua',
         'https://cdn-icons-png.flaticon.com/512/6024/6024190.png', 'Деканат', ''),
        ('teacher', '123', 'TEACHER', 'проф. Іваненко О.М.', 'teacher@ukd.edu.ua',
         'https://cdn-icons-png.flaticon.com/512/1995/1995531.png', '402', ''),
        ('student', '123', 'STUDENT', 'Іван Студент',        'student@ukd.edu.ua',
         'https://cdn-icons-png.flaticon.com/512/354/354637.png', '', 'ІПЗ-21'),
        ('std_1',   '123', 'STUDENT', 'Петренко Олег Михайлович', 'petro@ukd.edu.ua',
         'https://cdn-icons-png.flaticon.com/512/354/354637.png', '', 'ІПЗ-21'),
        ('std_2',   '123', 'STUDENT', 'Сидоренко Марія Іванівна', 'sydo@ukd.edu.ua',
         'https://cdn-icons-png.flaticon.com/512/354/354637.png', '', 'ІПЗ-21'),
        ('std_3',   '123', 'STUDENT', 'Коваленко Андрій Петрович','koval@ukd.edu.ua',
         'https://cdn-icons-png.flaticon.com/512/354/354637.png', '', 'ІПЗ-21'),
        ('std_4',   '123', 'STUDENT', 'Мельник Юлія Степанівна',  'melnyk@ukd.edu.ua',
         'https://cdn-icons-png.flaticon.com/512/354/354637.png', '', 'ІПЗ-22'),
        ('std_5',   '123', 'STUDENT', 'Бондаренко Тарас Олегович','bond@ukd.edu.ua',
         'https://cdn-icons-png.flaticon.com/512/354/354637.png', '', 'ІПЗ-22'),
    ])
    teacher_id = c.execute("SELECT id FROM users WHERE username='teacher'").fetchone()[0]

    c.executemany("INSERT INTO subjects (name, teacher_id) VALUES (?,?)", [
        ('Загальновійськова підготовка', teacher_id),
        ('Програмування', teacher_id),
        ('Вища математика', teacher_id),
    ])

    # Demo dates for journal
    today = datetime.now()
    subj_ids = [r[0] for r in c.execute("SELECT id FROM subjects").fetchall()]
    for sid in subj_ids:
        for i in range(3):
            d = (today - timedelta(weeks=i*2)).strftime("%Y-%m-%d")
            c.execute("INSERT OR IGNORE INTO journal_dates (subject_id, date_val) VALUES (?,?)", (sid, d))

    c.executemany("INSERT INTO creators (name,role,desc,skills) VALUES (?,?,?,?)", [
        ('Сергій',  'Frontend Developer', 'Робить все на фронті',              'Python, Flask, JS'),
        ('Юрій',    'Beer Master',         'Відповідає за пивний баланс команди','Beer, JS, Memes'),
        ('Арсен',   'Timer Dev',           'Розробив систему таймерів',         'JavaScript, CSS3'),
        ('Михайло', 'Moral Support',       'Підтримує бойовий дух команди',     'TikTok, Debugging'),
        ('Шляпа',   'Coffee Maker',        'Робить каву для команди',           'Coffee, Data'),
    ])


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def db_rows(query, params=()):
    conn = get_db()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def db_one(query, params=()):
    conn = get_db()
    row = conn.execute(query, params).fetchone()
    conn.close()
    return dict(row) if row else None

def db_exec(query, params=()):
    conn = get_db()
    conn.execute(query, params)
    conn.commit()
    conn.close()

def sync_data_from_sheets():
    return False, "Google Sheets синхронізація недоступна"


# ─── HTML ─────────────────────────────────────────────────────────────────────

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Таймер но 6 тисяч | УКД</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        :root { --ukd-red: #4a0404; --ukd-bright: #8b0000; }
        body { background-color: var(--ukd-red); color: white; font-family: 'Inter', sans-serif; }
        .card { background: white; color: black; border-left: 8px solid black; transition: 0.3s; }
        .nav-btn.active { border-bottom: 2px solid white; font-weight: bold; }
        .accordion-content { max-height: 0; overflow: hidden; transition: 0.4s ease-out; }
        .accordion-item.active .accordion-content { max-height: 600px; padding-top: 20px; }
        .accordion-item.active .chevron { transform: rotate(180deg); }

        /* ── Журнал ── */
        .journal-wrap { overflow-x: auto; border-radius: 16px; border: 1px solid rgba(255,255,255,0.1); }
        .journal-tbl { border-collapse: collapse; min-width: 100%; font-size: 13px; }
        .journal-tbl th {
            background: #1a0000; color: #f87171;
            padding: 10px 12px; text-align: center;
            font-size: 11px; text-transform: uppercase;
            border: 1px solid rgba(255,255,255,0.08);
            white-space: nowrap;
        }
        .journal-tbl th.name-col { text-align: left; min-width: 200px; }
        .journal-tbl td {
            padding: 6px 8px;
            border: 1px solid rgba(255,255,255,0.07);
            text-align: center; vertical-align: middle;
        }
        .journal-tbl td.name-cell {
            text-align: left; font-weight: 600;
            padding-left: 12px; white-space: nowrap;
            background: #2a0000;
        }

        /* Клітинка оцінки */
        .grade-cell {
            background: transparent; border: none; outline: none;
            color: white; width: 52px;
            text-align: center; font-weight: 700;
            font-size: 14px; padding: 4px 2px;
            border-radius: 6px; cursor: pointer;
        }
        .grade-cell:focus { background: rgba(255,255,255,0.12); outline: 2px solid #f87171; }
        .grade-cell.has-grade { color: #86efac; }
        .grade-cell.has-nk    { color: #fca5a5; font-style: italic; }
        .grade-cell.empty     { color: rgba(255,255,255,0.15); }

        .group-badge {
            background: #3b0000; border: 1px solid #7f1d1d;
            color: #fca5a5; padding: 3px 12px;
            border-radius: 20px; font-size: 13px; font-weight: 700;
        }

        /* НК таймер */
        .nk-timer {
            font-family: monospace; font-size: 14px; font-weight: 700;
            background: #1a0000; border: 1px solid #7f1d1d;
            color: #fca5a5; padding: 4px 12px; border-radius: 8px;
            min-width: 130px; text-align: center;
        }
        .nk-timer.expired { color: #6b7280; border-color: #374151; background: #111; }

        /* Живий годинник */
        #live-clock { letter-spacing: 2px; }
    </style>
</head>
<body class="min-h-screen flex flex-col">

    <!-- Навігація -->
    <nav class="bg-black p-4 sticky top-0 z-50 shadow-2xl">
        <div class="container mx-auto flex justify-between items-center">
            <div class="flex items-center space-x-3 cursor-pointer" onclick="showTab('main')">
                <div class="bg-red-700 p-2 rounded-lg"><i class="fas fa-hourglass-half text-white"></i></div>
                <span class="text-xl font-black uppercase tracking-tighter">Таймер но 6 тисяч</span>
            </div>
            <div class="hidden md:flex space-x-6 items-center flex-grow justify-center">
                <button onclick="showTab('main')" id="btn-main" class="nav-btn active px-2 py-1">Головна</button>
                {% if session.get('role') %}
                    <button onclick="showTab('timers')" id="btn-timers" class="nav-btn px-2 py-1">Мої НК</button>
                    <button onclick="showTab('journal')" id="btn-journal" class="nav-btn px-2 py-1">
                        <i class="fas fa-book-open mr-1"></i>Журнал
                    </button>
                    {% if session.get('role') in ['ADMIN', 'TEACHER'] %}
                        <button onclick="showTab('admin')" id="btn-admin" class="nav-btn text-yellow-400 px-2 py-1">Керування</button>
                    {% endif %}
                    <button onclick="showTab('profile')" id="btn-profile" class="nav-btn px-2 py-1">Профіль</button>
                {% endif %}
                <button onclick="showTab('creators')" id="btn-creators" class="nav-btn px-2 py-1">Творці</button>
            </div>
            <div class="flex items-center space-x-4">
                {% if session.get('username') %}
                    <div class="flex items-center space-x-2">
                        <img src="{{ current_user.get('avatar', '') }}" class="w-8 h-8 rounded-full border border-white/50">
                        <a href="/logout" class="text-red-500 hover:text-white transition ml-4"><i class="fas fa-sign-out-alt text-xl"></i></a>
                    </div>
                {% else %}
                    <button onclick="toggleLogin(true)" class="bg-white text-black px-5 py-1.5 rounded-full font-bold">Вхід</button>
                {% endif %}
            </div>
        </div>
    </nav>

    <main class="container mx-auto px-4 py-10 flex-grow relative">

        <!-- Головна -->
        <section id="tab-main" class="tab-content max-w-4xl mx-auto">
            <div class="text-center mb-12">
                <h1 class="text-6xl font-black mb-4 uppercase tracking-tighter">УКД ПЛАТФОРМА</h1>
                <p class="opacity-60 italic">Офіційний сервіс моніторингу заборгованостей</p>
            </div>
            <div class="space-y-6">
                <div class="accordion-item bg-black/30 rounded-2xl p-6 border border-white/10" onclick="this.classList.toggle('active')">
                    <div class="flex justify-between items-center cursor-pointer">
                        <h3 class="text-2xl font-bold italic"><i class="fas fa-info-circle mr-3"></i>Про проект</h3>
                        <i class="fas fa-chevron-down chevron transition-transform"></i>
                    </div>
                    <div class="accordion-content opacity-70 text-lg">
                        "Таймер но 6 тисяч" — інноваційна система для студентів УКД для відстеження термінів відпрацювання НК та перегляду оцінок.
                    </div>
                </div>
                <div class="accordion-item bg-black/30 rounded-2xl p-6 border border-white/10" onclick="this.classList.toggle('active')">
                    <div class="flex justify-between items-center cursor-pointer">
                        <h3 class="text-2xl font-bold italic"><i class="fas fa-video mr-3"></i>Відео-гайд</h3>
                        <i class="fas fa-chevron-down chevron transition-transform"></i>
                    </div>
                    <div class="accordion-content text-center">
                        <p class="mb-6">Інструкція по роботі з сайтом:</p>
                        <a href="https://www.youtube.com/watch?v=YAgJ9XugGBo&t=5018s" target="_blank"
                           class="inline-flex items-center space-x-3 bg-red-600 px-10 py-4 rounded-full font-bold">
                            <i class="fab fa-youtube text-2xl"></i><span>ВІДКРИТИ НА YOUTUBE</span>
                        </a>
                    </div>
                </div>
            </div>
        </section>

        <!-- ═══════════════ ТАЙМЕРИ НК ═══════════════ -->
        <section id="tab-timers" class="tab-content hidden">
            <!-- Заголовок з живим годинником -->
            <div class="flex justify-between items-center mb-8 border-b border-white/10 pb-4">
                <h2 class="text-3xl font-black uppercase">Активні НК</h2>
                <div class="text-right bg-black/30 px-6 py-3 rounded-2xl border border-white/10">
                    <div class="text-3xl font-black font-mono text-red-400" id="live-clock">--:--:--</div>
                    <div class="text-xs opacity-40 mt-1" id="live-date">--.--.----</div>
                </div>
            </div>

            <div class="grid gap-4">
                {% for item in user_absences %}
                <div class="card p-6 rounded-2xl flex flex-col md:flex-row justify-between items-center shadow-lg">
                    <div class="flex items-center space-x-6 text-left w-full">
                        <div class="bg-red-800 text-white p-4 rounded-xl font-black text-xl w-16 h-16 flex items-center justify-center">НК</div>
                        <div class="flex-grow">
                            <h4 class="text-xl font-black uppercase leading-tight">{{ item.get('subject_name','???') }}</h4>
                            <p class="text-red-700 font-bold text-sm">{{ item.get('student_name','...') }}</p>
                            <p class="text-xs opacity-50 mt-1">
                                Дедлайн: <span class="font-bold text-black" data-deadline="{{ item.get('deadline','') }}"></span>
                            </p>
                        </div>
                    </div>
                    <div class="flex flex-col md:items-end mt-4 md:mt-0 space-y-2 w-full md:w-auto md:min-w-[160px]">
                        <div class="nk-timer" data-timer-until="{{ item.get('deadline','') }}">...</div>
                        {% if session.get('role') in ['ADMIN','TEACHER'] %}
                            <button onclick="resolveN({{ item.id }})"
                                    class="bg-green-600 hover:bg-green-500 text-white px-6 py-1.5 rounded-lg text-xs font-bold uppercase w-full transition">
                                ✓ Відпрацьовано
                            </button>
                        {% endif %}
                    </div>
                </div>
                {% endfor %}
                {% if not user_absences %}
                <div class="text-center opacity-50 py-20">
                    <i class="fas fa-check-circle text-5xl mb-4 text-green-400"></i>
                    <p class="text-xl">Немає активних заборгованостей</p>
                </div>
                {% endif %}
            </div>
        </section>

        <!-- ═══════════════ ЖУРНАЛ (по групах) ═══════════════ -->
        <section id="tab-journal" class="tab-content hidden">
            <div class="flex flex-wrap justify-between items-end gap-4 mb-6 border-b border-white/10 pb-4">
                <div>
                    <h2 class="text-3xl font-black uppercase">Журнал успішності</h2>
                    {% if session.get('role') == 'STUDENT' %}
                        <p class="opacity-40 text-sm mt-1">Перегляд власних оцінок</p>
                    {% else %}
                        <p class="opacity-40 text-sm mt-1">
                            Клацніть на клітинку → введіть оцінку (1–100) або <strong class="text-red-400">НК</strong> → Enter
                        </p>
                    {% endif %}
                </div>
                {% if session.get('role') in ['ADMIN','TEACHER'] %}
                <div class="flex gap-3 flex-wrap items-center">
                    <select id="filter-subject-journal" onchange="switchSubject(this.value)"
                            class="bg-black/40 border border-white/20 text-white rounded-xl px-4 py-2 font-bold text-sm">
                        {% for subj in all_subjects %}
                            <option value="{{ subj.id }}" {% if subj.id == current_subject_id %}selected{% endif %}>
                                {{ subj.name }}
                            </option>
                        {% endfor %}
                    </select>
                    <button onclick="addDateColumn()"
                            class="bg-red-900 hover:bg-red-700 text-white px-4 py-2 rounded-xl font-bold text-sm transition border border-red-700">
                        <i class="fas fa-plus mr-1"></i>Додати дату
                    </button>
                </div>
                {% endif %}
            </div>

            <!-- Таблиці по групах -->
            {% for group_name, group_data in journal_groups.items() %}
            <div class="mb-10">
                <div class="flex items-center gap-3 mb-3">
                    <span class="group-badge">{{ group_name }}</span>
                    <span class="opacity-40 text-sm">{{ group_data.students | length }} студентів</span>
                </div>
                <div class="journal-wrap">
                    <table class="journal-tbl">
                        <thead>
                            <tr>
                                <th class="name-col">№ / Студент</th>
                                {% for d in group_data.dates %}
                                <th>
                                    {{ d[8:10] }}.{{ d[5:7] }}<br>
                                    <span class="opacity-40" style="font-size:9px;">{{ d[:4] }}</span>
                                </th>
                                {% endfor %}
                                {% if session.get('role') in ['ADMIN','TEACHER'] %}
                                <th style="width:50px;opacity:0.4">НК</th>
                                {% endif %}
                            </tr>
                        </thead>
                        <tbody>
                        {% for i, student in enumerate(group_data.students) %}
                            <tr>
                                <td class="name-cell">
                                    <span class="opacity-30 mr-2 text-xs">{{ i+1 }}.</span>{{ student.fullname }}
                                </td>
                                {% for d in group_data.dates %}
                                {% set cell = group_data.cells.get((student.id, d), {}) %}
                                <td>
                                    {% if session.get('role') in ['ADMIN','TEACHER'] %}
                                        <input type="text"
                                            class="grade-cell {% if cell.get('is_nk') %}has-nk{% elif cell.get('grade') %}has-grade{% else %}empty{% endif %}"
                                            value="{{ 'НК' if cell.get('is_nk') else (cell.get('grade') or '') }}"
                                            placeholder="·"
                                            data-student="{{ student.id }}"
                                            data-subject="{{ current_subject_id }}"
                                            data-date="{{ d }}"
                                            onblur="saveCellGrade(this)"
                                            onkeydown="if(event.key==='Enter'){this.blur();}"
                                            title="Введіть оцінку (1-100) або НК">
                                    {% else %}
                                        <span class="font-bold {% if cell.get('is_nk') %}text-red-400{% elif cell.get('grade') %}text-green-400{% else %}opacity-20{% endif %}">
                                            {{ 'НК' if cell.get('is_nk') else (cell.get('grade') or '—') }}
                                        </span>
                                    {% endif %}
                                </td>
                                {% endfor %}
                                {% if session.get('role') in ['ADMIN','TEACHER'] %}
                                <td>
                                    <button onclick="addNkAbsence({{ student.id }}, {{ current_subject_id }}, '{{ student.fullname }}')"
                                            class="text-red-500 hover:text-red-300 text-xs font-bold px-1 py-1 rounded transition"
                                            title="Додати НК заборгованість">+НК</button>
                                </td>
                                {% endif %}
                            </tr>
                        {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
            {% endfor %}

            {% if not journal_groups %}
            <div class="text-center opacity-40 py-20">
                <i class="fas fa-users text-5xl mb-4"></i>
                <p class="text-xl">Немає груп або студентів</p>
            </div>
            {% endif %}
        </section>

        <!-- Керування -->
        <section id="tab-admin" class="tab-content hidden">
            <div class="grid lg:grid-cols-2 gap-8 mb-8">
                <div class="bg-black/20 p-8 rounded-3xl border border-white/10 text-center flex flex-col items-center">
                    <i class="fas fa-sync text-5xl text-blue-500 mb-6"></i>
                    <h3 class="text-2xl font-bold mb-4">Google Sheets</h3>
                    <button onclick="syncSheets()" id="sync-btn"
                            class="w-full bg-blue-600 py-4 rounded-xl font-black uppercase">Синхронізувати</button>
                </div>
                <div class="bg-black/20 p-8 rounded-3xl border border-white/10">
                    <h3 class="text-2xl font-bold mb-6 text-yellow-400">Додати Користувача</h3>
                    <form action="/api/add_user" method="POST" class="space-y-4">
                        <select name="role" onchange="toggleRegFields(this.value)"
                                class="w-full p-3 rounded-xl bg-white text-black font-bold">
                            <option value="STUDENT">Студент</option>
                            <option value="TEACHER">Викладач</option>
                            <option value="ADMIN">Адмін</option>
                        </select>
                        <input type="text"  name="fullname" placeholder="ПІБ" required
                               class="w-full p-3 rounded-xl bg-white text-black font-bold">
                        <input type="email" name="email" placeholder="Email" required
                               class="w-full p-3 rounded-xl bg-white text-black font-bold">
                        <input type="text" name="group_name" placeholder="Група (напр. ІПЗ-21)"
                               class="w-full p-3 rounded-xl bg-white text-black font-bold">
                        <div id="reg-teacher-fields" class="hidden">
                            <input type="text" name="room" placeholder="Кабінет"
                                   class="w-full p-3 rounded-xl bg-white text-black font-bold border-2 border-red-500">
                        </div>
                        <div class="flex space-x-2">
                            <input type="text" name="username" placeholder="Логін" required
                                   class="w-1/2 p-3 rounded-xl bg-white text-black">
                            <input type="text" name="password" placeholder="Пароль" required
                                   class="w-1/2 p-3 rounded-xl bg-white text-black">
                        </div>
                        <button class="w-full bg-green-600 text-white py-3 rounded-xl font-black uppercase">ЗБЕРЕГТИ</button>
                    </form>
                </div>
            </div>

            <!-- Email налаштування -->
            <div class="bg-black/20 p-8 rounded-3xl border border-white/10">
                <div class="flex items-center gap-4 mb-6">
                    <i class="fas fa-envelope text-3xl text-red-400"></i>
                    <div>
                        <h3 class="text-2xl font-bold text-red-300">Налаштування Email (Gmail)</h3>
                        <p class="text-xs opacity-40 mt-1">
                            Для відправки потрібен <strong>App Password</strong> — не звичайний пароль Gmail.
                            <a href="https://myaccount.google.com/apppasswords" target="_blank"
                               class="text-red-400 underline">Отримати тут →</a>
                        </p>
                    </div>
                </div>
                <div id="email-status-bar" class="hidden mb-4 p-3 rounded-xl text-sm font-bold text-center"></div>
                <div class="grid md:grid-cols-2 gap-4">
                    <div>
                        <label class="text-xs uppercase opacity-40 block mb-1">Gmail адреса відправника</label>
                        <input type="email" id="cfg-email" placeholder="yourschool@gmail.com"
                               class="w-full p-3 rounded-xl bg-black/40 border border-white/20 text-white font-bold">
                    </div>
                    <div>
                        <label class="text-xs uppercase opacity-40 block mb-1">App Password (16 символів)</label>
                        <div class="relative">
                            <input type="password" id="cfg-password" placeholder="xxxx xxxx xxxx xxxx"
                                   class="w-full p-3 rounded-xl bg-black/40 border border-white/20 text-white font-bold pr-12">
                            <button type="button" onclick="togglePwVis()"
                                    class="absolute right-3 top-1/2 -translate-y-1/2 text-white/40 hover:text-white">
                                <i class="fas fa-eye" id="pw-eye-icon"></i>
                            </button>
                        </div>
                    </div>
                </div>
                <div class="flex gap-3 mt-4">
                    <button onclick="saveEmailConfig()"
                            class="flex-1 bg-red-800 hover:bg-red-700 text-white py-3 rounded-xl font-black uppercase transition">
                        <i class="fas fa-save mr-2"></i>Зберегти
                    </button>
                    <button onclick="testEmailConfig()"
                            class="flex-1 bg-black/40 hover:bg-black/60 border border-white/20 text-white py-3 rounded-xl font-bold transition">
                        <i class="fas fa-paper-plane mr-2"></i>Тест-лист
                    </button>
                </div>
                <p id="email-current" class="mt-3 text-xs opacity-30 text-center"></p>
            </div>
        </section>

        <!-- Творці -->
        <section id="tab-creators" class="tab-content hidden text-center">
            <h2 class="text-4xl font-black mb-12 uppercase tracking-tighter">Команда проекту</h2>
            <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
                {% for dev in creators %}
                <div class="bg-white/5 p-8 rounded-3xl border border-white/10 hover:border-red-500 transition-all flex flex-col h-full">
                    <div class="w-16 h-16 bg-red-800 rounded-full mx-auto mb-4 flex items-center justify-center font-bold text-2xl shadow-lg overflow-hidden">
                        {% if dev.get('avatar') %}
                            <img src="{{ dev.get('avatar') }}" class="w-full h-full object-cover">
                        {% else %}
                            {{ dev.get('name','D')[0] }}
                        {% endif %}
                    </div>
                    <h4 class="font-bold text-xl">{{ dev.get('name','Розробник') }}</h4>
                    <p class="text-red-400 text-xs uppercase mb-4 tracking-widest">{{ dev.get('role','Dev') }}</p>
                    <p class="text-sm opacity-60 leading-relaxed mb-6">{{ dev.get('desc','') }}</p>
                    <div class="mt-auto pt-4 border-t border-white/10 text-left">
                        <span class="text-[10px] uppercase font-bold opacity-40 block mb-2">Навички</span>
                        <div class="text-xs font-mono text-gray-300">{{ dev.get('skills','') }}</div>
                    </div>
                </div>
                {% endfor %}
            </div>
        </section>

        <!-- Профіль -->
        {% if current_user %}
        <section id="tab-profile" class="tab-content hidden max-w-2xl mx-auto text-center">
            <div class="bg-white/10 p-12 rounded-[3rem] border border-white/20">
                <div class="relative inline-block mb-6">
                    <img src="{{ current_user.get('avatar','') }}" class="w-32 h-32 rounded-full border-4 border-white shadow-2xl">
                    <button onclick="toggleAvatarEdit(true)" class="absolute bottom-0 right-0 bg-red-700 p-2 rounded-full border-2 border-white">
                        <i class="fas fa-camera"></i>
                    </button>
                </div>
                <h2 class="text-4xl font-black uppercase">{{ current_user.get('fullname','') }}</h2>
                <p class="text-red-500 font-bold mb-2 uppercase tracking-widest">{{ current_user.get('role','') }}</p>
                {% if current_user.get('group_name') %}
                <span class="group-badge">{{ current_user.get('group_name') }}</span>
                {% endif %}
                <div id="avatar-edit" class="hidden mt-8">
                    <form action="/api/update_avatar" method="POST" class="flex flex-col space-y-3">
                        <input type="url" name="url" placeholder="URL нової аватарки"
                               class="p-3 rounded-xl bg-white text-black font-bold outline-none" required>
                        <button class="bg-white text-black py-2 rounded-xl font-black uppercase text-xs">Оновити</button>
                    </form>
                </div>
            </div>
        </section>
        {% endif %}
    </main>

    <!-- ══ МОДАЛКА НК ══ -->
    <div id="nk-modal" class="hidden fixed inset-0 bg-black/90 z-[100] flex items-center justify-center p-4">
        <div class="bg-[#1a0000] border border-red-900 text-white p-10 rounded-3xl w-full max-w-md relative shadow-2xl">
            <button onclick="closeNkModal()" class="absolute top-5 right-6 text-3xl hover:text-red-400">&times;</button>
            <h2 class="text-2xl font-black mb-2 uppercase">
                <i class="fas fa-exclamation-triangle mr-3 text-red-500"></i>Додати НК
            </h2>
            <p id="nk-student-name" class="opacity-60 mb-8 text-sm"></p>
            <div class="space-y-4">
                <div>
                    <label class="text-xs uppercase opacity-50 block mb-1">Дедлайн відпрацювання</label>
                    <input type="datetime-local" id="nk-deadline"
                           class="w-full p-3 rounded-xl bg-black/40 border border-white/20 text-white font-bold">
                    <p class="text-xs opacity-30 mt-1">За замовчуванням: 4 тижні від сьогодні</p>
                </div>
                <button onclick="saveNkAbsence()"
                        class="w-full bg-red-700 hover:bg-red-600 text-white py-3 rounded-xl font-black uppercase transition">
                    Зафіксувати НК
                </button>
            </div>
        </div>
    </div>

    <!-- ══ МОДАЛКА ЛОГІНУ ══ -->
    <div id="login-modal" class="hidden fixed inset-0 bg-black/90 z-[100] flex items-center justify-center p-4">
        <div class="bg-white text-black p-10 rounded-3xl w-full max-w-sm relative shadow-2xl">
            <button onclick="toggleLogin(false)" class="absolute top-4 right-4 text-2xl hover:text-red-600">&times;</button>
            <h2 class="text-3xl font-black mb-8 text-center uppercase tracking-tighter">ВХІД УКД</h2>
            <form action="/login" method="POST" class="space-y-4">
                <input type="email" name="email" placeholder="Email" required
                       class="w-full border-2 p-4 rounded-xl font-bold outline-none">
                <input type="password" name="pass" placeholder="Пароль" required
                       class="w-full border-2 p-4 rounded-xl font-bold outline-none">
                <button class="w-full bg-black text-white py-4 rounded-xl font-black uppercase">Увійти</button>
            </form>
        </div>
    </div>

    <script>
    // ══════════════════════════════════════════
    // ЖИВИЙ ГОДИННИК — прив'язаний до системного часу
    // ══════════════════════════════════════════
    (function startClock() {
        const pad = n => String(n).padStart(2, '0');
        function tick() {
            const now = new Date();
            const clockEl = document.getElementById('live-clock');
            const dateEl  = document.getElementById('live-date');
            if (clockEl) clockEl.textContent =
                `${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`;
            if (dateEl) dateEl.textContent =
                `${pad(now.getDate())}.${pad(now.getMonth()+1)}.${now.getFullYear()}`;
        }
        tick();
        // Синхронізуємо з початком кожної секунди
        const delay = 1000 - (Date.now() % 1000);
        setTimeout(function loop() {
            tick();
            setTimeout(loop, 1000);
        }, delay);
    })();

    // ══════════════════════════════════════════
    // ТАЙМЕРИ НК — оновлюються кожну секунду
    // ══════════════════════════════════════════
    (function startTimers() {
        const pad = n => String(n).padStart(2, '0');
        function updateTimers() {
            document.querySelectorAll('[data-timer-until]').forEach(badge => {
                const deadline = new Date(badge.dataset.timerUntil);
                if (isNaN(deadline)) { badge.textContent = '—'; return; }
                const diff = Math.floor((deadline - Date.now()) / 1000);
                if (diff > 0) {
                    const days = Math.floor(diff / 86400);
                    const h    = Math.floor((diff % 86400) / 3600);
                    const min  = Math.floor((diff % 3600) / 60);
                    const sec  = diff % 60;
                    badge.textContent = days > 0
                        ? `${days}д ${pad(h)}:${pad(min)}:${pad(sec)}`
                        : `${pad(h)}:${pad(min)}:${pad(sec)}`;
                    badge.classList.remove('expired');
                } else {
                    badge.textContent = 'ЧАС ВИЙШОВ';
                    badge.classList.add('expired');
                }
            });
        }
        updateTimers();
        const delay = 1000 - (Date.now() % 1000);
        setTimeout(function loop() {
            updateTimers();
            setTimeout(loop, 1000);
        }, delay);
    })();

    // Відображення дат дедлайнів
    const MONTHS_UA = ["Січня","Лютого","Березня","Квітня","Травня","Червня",
                       "Липня","Серпня","Вересня","Жовтня","Листопада","Грудня"];
    document.querySelectorAll('[data-deadline]').forEach(el => {
        const d = new Date(el.dataset.deadline);
        if (!isNaN(d)) {
            const pad = n => String(n).padStart(2,'0');
            el.textContent = `${d.getDate()} ${MONTHS_UA[d.getMonth()]} о ${pad(d.getHours())}:${pad(d.getMinutes())}`;
        }
    });

    // ══════════════════════════════════════════
    // НАВІГАЦІЯ
    // ══════════════════════════════════════════
    function showTab(id) {
        document.querySelectorAll('.tab-content').forEach(t => t.classList.add('hidden'));
        document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
        const tab = document.getElementById('tab-' + id);
        if (tab) tab.classList.remove('hidden');
        const btn = document.getElementById('btn-' + id);
        if (btn) btn.classList.add('active');
    }
    function toggleLogin(s)      { document.getElementById('login-modal').classList.toggle('hidden', !s); }
    function toggleAvatarEdit(s) { document.getElementById('avatar-edit').classList.toggle('hidden', !s); }
    function toggleRegFields(r)  { document.getElementById('reg-teacher-fields').classList.toggle('hidden', r !== 'TEACHER'); }
    function syncSheets() {
        const btn = document.getElementById('sync-btn');
        btn.innerText = "Синхронізація..."; btn.disabled = true;
        fetch('/api/sync_sheets').then(r=>r.json()).then(d=>{ alert(d.message); location.reload(); })
            .catch(()=>{ alert("Помилка"); btn.innerText="Синхронізувати"; btn.disabled=false; });
    }
    function resolveN(id) {
        fetch('/api/resolve/'+id).then(r=>r.json()).then(d=>{ if(d.success) location.reload(); });
    }

    // ══════════════════════════════════════════
    // ЖУРНАЛ — збереження клітинок
    // ══════════════════════════════════════════
    function saveCellGrade(input) {
        const raw  = input.value.trim();
        const isNk = raw.toUpperCase() === 'НК' || raw.toUpperCase() === 'NK';
        const num  = isNk ? null : (raw === '' ? null : parseInt(raw, 10));

        if (!isNk && raw !== '' && (isNaN(num) || num < 1 || num > 100)) {
            input.style.outline = '2px solid orange';
            setTimeout(() => { input.style.outline = ''; }, 1500);
            return;
        }

        // Оновлюємо вигляд
        input.classList.remove('has-grade','has-nk','empty');
        if      (isNk) { input.classList.add('has-nk');   input.value = 'НК'; }
        else if (num)  { input.classList.add('has-grade'); input.value = num; }
        else           { input.classList.add('empty');     input.value = ''; }

        fetch('/api/save_cell_grade', {
            method: 'POST',
            headers: {'Content-Type':'application/json'},
            body: JSON.stringify({
                student_id: input.dataset.student,
                subject_id: input.dataset.subject,
                date_col:   input.dataset.date,
                grade:      isNk ? null : (num || null),
                is_nk:      isNk ? 1 : 0
            })
        }).then(r=>r.json()).then(d=>{
            if (!d.success) alert('Помилка збереження: ' + (d.message || ''));
        });
    }

    function switchSubject(subjId) {
        window.location.href = '/?tab=journal&subject=' + subjId;
    }

    function addDateColumn() {
        const sel = document.getElementById('filter-subject-journal');
        const subjId = sel ? sel.value : null;
        if (!subjId) { alert('Оберіть предмет'); return; }
        const now = new Date();
        const pad = n => String(n).padStart(2,'0');
        const def = `${now.getFullYear()}-${pad(now.getMonth()+1)}-${pad(now.getDate())}`;
        const date = prompt('Введіть дату стовпця (РРРР-ММ-ДД):', def);
        if (!date) return;
        fetch('/api/add_date_column', {
            method: 'POST',
            headers: {'Content-Type':'application/json'},
            body: JSON.stringify({ subject_id: subjId, date_val: date })
        }).then(r=>r.json()).then(d=>{
            if (d.success) location.reload();
            else alert('Помилка: ' + (d.message || ''));
        });
    }

    // ══════════════════════════════════════════
    // НК МОДАЛКА
    // ══════════════════════════════════════════
    let _nkSid = null, _nkSubj = null;

    function addNkAbsence(studentId, subjectId, studentName) {
        _nkSid  = studentId;
        _nkSubj = subjectId;
        document.getElementById('nk-student-name').textContent = studentName;
        // Дедлайн = 4 тижні від зараз
        const d   = new Date(Date.now() + 28 * 24 * 3600 * 1000);
        const pad = n => String(n).padStart(2,'0');
        document.getElementById('nk-deadline').value =
            `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T23:59`;
        document.getElementById('nk-modal').classList.remove('hidden');
    }

    function closeNkModal() { document.getElementById('nk-modal').classList.add('hidden'); }

    function saveNkAbsence() {
        const deadline = document.getElementById('nk-deadline').value;
        if (!deadline) { alert('Вкажіть дедлайн'); return; }
        fetch('/api/add_absence', {
            method: 'POST',
            headers: {'Content-Type':'application/json'},
            body: JSON.stringify({ student_id: _nkSid, subject_id: _nkSubj, deadline })
        }).then(r=>r.json()).then(d=>{
            if (d.success) { closeNkModal(); location.reload(); }
            else alert('Помилка: ' + (d.message || ''));
        });
    }

    // ══════════════════════════════════════════
    // Ініціалізація з URL параметрів
    // ══════════════════════════════════════════
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('tab')) showTab(urlParams.get('tab'));

    // ══════════════════════════════════════════
    // EMAIL CONFIG (адмін-панель)
    // ══════════════════════════════════════════
    function togglePwVis() {
        const inp  = document.getElementById('cfg-password');
        const icon = document.getElementById('pw-eye-icon');
        if (inp.type === 'password') { inp.type = 'text';     icon.className = 'fas fa-eye-slash'; }
        else                         { inp.type = 'password'; icon.className = 'fas fa-eye'; }
    }

    function showEmailStatus(msg, ok) {
        const bar = document.getElementById('email-status-bar');
        if (!bar) return;
        bar.textContent = msg;
        bar.style.background = ok ? '#14532d' : '#7f1d1d';
        bar.style.color = ok ? '#86efac' : '#fca5a5';
        bar.classList.remove('hidden');
        setTimeout(() => bar.classList.add('hidden'), 4000);
    }

    function saveEmailConfig() {
        const email = document.getElementById('cfg-email').value.trim();
        const pw    = document.getElementById('cfg-password').value.trim();
        if (!email || !pw) { showEmailStatus('Заповніть обидва поля', false); return; }
        fetch('/api/set_email_config', {
            method: 'POST',
            headers: {'Content-Type':'application/json'},
            body: JSON.stringify({ email, password: pw })
        }).then(r=>r.json()).then(d=>{
            showEmailStatus(d.message || (d.success ? 'Збережено' : 'Помилка'), d.success);
            if (d.success) loadEmailCurrent();
        });
    }

    function testEmailConfig() {
        showEmailStatus('Відправляємо тест...', true);
        fetch('/api/test_email').then(r=>r.json()).then(d=>{
            showEmailStatus(d.message || (d.success ? 'Лист відправлено!' : 'Помилка'), d.success);
        });
    }

    function loadEmailCurrent() {
        fetch('/api/get_email_config').then(r=>r.json()).then(d=>{
            const el = document.getElementById('email-current');
            if (el && d.email) el.textContent = 'Поточний відправник: ' + d.email;
        });
    }

    // Завантажуємо поточний email при відкритті сторінки
    loadEmailCurrent();
    </script>
</body>
</html>
"""

# ─── ROUTES ───────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    current_user   = None
    user_absences  = []
    journal_groups = {}
    current_subject_id = 0

    app.jinja_env.globals['enumerate'] = enumerate

    if 'user_id' in session:
        current_user = db_one("SELECT * FROM users WHERE id=?", (session['user_id'],))

        # ── НК заборгованості ──
        if session.get('role') in ['ADMIN', 'TEACHER']:
            user_absences = db_rows("""
                SELECT a.id, a.deadline, s.name as subject_name,
                       u.fullname as student_name
                FROM absences a
                JOIN subjects s ON s.id=a.subject_id
                JOIN users u    ON u.id=a.student_id
                WHERE a.status='active'
                ORDER BY a.deadline
            """)
        else:
            user_absences = db_rows("""
                SELECT a.id, a.deadline, s.name as subject_name,
                       u.fullname as student_name
                FROM absences a
                JOIN subjects s ON s.id=a.subject_id
                JOIN users u    ON u.id=a.student_id
                WHERE a.status='active' AND a.student_id=?
                ORDER BY a.deadline
            """, (session['user_id'],))

        # ── Журнал по групах ──
        all_subjects_list = db_rows("SELECT id, name FROM subjects ORDER BY name")
        sel_subj = request.args.get('subject')
        if sel_subj:
            current_subject_id = int(sel_subj)
        elif all_subjects_list:
            current_subject_id = all_subjects_list[0]['id']

        if current_subject_id:
            dates = [r['date_val'] for r in db_rows(
                "SELECT date_val FROM journal_dates WHERE subject_id=? ORDER BY date_val",
                (current_subject_id,)
            )]

            grades_raw = db_rows(
                "SELECT student_id, date_col, grade, is_nk FROM grades WHERE subject_id=?",
                (current_subject_id,)
            )
            grades_map = {(g['student_id'], g['date_col']): g for g in grades_raw}

            if session.get('role') in ['ADMIN', 'TEACHER']:
                students = db_rows(
                    "SELECT id, fullname, group_name FROM users WHERE role='STUDENT' ORDER BY group_name, fullname"
                )
            else:
                students = db_rows(
                    "SELECT id, fullname, group_name FROM users WHERE role='STUDENT' AND id=?",
                    (session['user_id'],)
                )

            from collections import defaultdict
            groups_tmp = defaultdict(list)
            for s in students:
                gname = s.get('group_name') or 'Без групи'
                groups_tmp[gname].append(s)

            for gname in sorted(groups_tmp):
                journal_groups[gname] = {
                    'students': groups_tmp[gname],
                    'dates':    dates,
                    'cells':    grades_map
                }

    all_subjects = db_rows("SELECT id, name FROM subjects ORDER BY name")
    creators     = db_rows("SELECT * FROM creators")

    return render_template_string(
        HTML_TEMPLATE,
        user_absences=user_absences,
        journal_groups=journal_groups,
        current_subject_id=current_subject_id,
        all_subjects=all_subjects,
        creators=creators,
        current_user=current_user
    )


@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    pw    = request.form.get('pass')
    user  = db_one("SELECT * FROM users WHERE email=? AND password=?", (email, pw))
    if user:
        session.update({'user_id': user['id'], 'role': user['role'], 'username': user['username']})
    return redirect('/')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


@app.route('/api/sync_sheets')
def sync_sheets():
    if session.get('role') not in ['ADMIN', 'TEACHER']:
        return jsonify({'success': False, 'message': 'Відмовлено'})
    ok, msg = sync_data_from_sheets()
    return jsonify({'success': ok, 'message': msg})


@app.route('/api/resolve/<int:abs_id>')
def resolve(abs_id):
    if session.get('role') not in ['ADMIN', 'TEACHER']:
        return jsonify({'success': False}), 403
    db_exec("UPDATE absences SET status='resolved' WHERE id=?", (abs_id,))
    return jsonify({'success': True})


@app.route('/api/add_user', methods=['POST'])
def add_user():
    if session.get('role') not in ['ADMIN', 'TEACHER']:
        return redirect('/')
    try:
        conn = get_db()
        conn.execute("""
            INSERT INTO users (username,password,role,fullname,email,room,group_name)
            VALUES (?,?,?,?,?,?,?)
        """, (
            request.form.get('username'),
            request.form.get('password'),
            request.form.get('role', 'STUDENT'),
            request.form.get('fullname'),
            request.form.get('email'),
            request.form.get('room', ''),
            request.form.get('group_name', ''),
        ))
        conn.commit()
        conn.close()
    except Exception:
        pass
    return redirect('/?tab=admin')


@app.route('/api/update_avatar', methods=['POST'])
def update_avatar():
    if 'user_id' not in session:
        return redirect('/')
    db_exec("UPDATE users SET avatar=? WHERE id=?",
            (request.form.get('url'), session['user_id']))
    return redirect('/?tab=profile')


@app.route('/api/save_cell_grade', methods=['POST'])
def save_cell_grade():
    if session.get('role') not in ['ADMIN', 'TEACHER']:
        return jsonify({'success': False, 'message': 'Доступ заборонено'}), 403
    data = request.get_json()
    try:
        student_id = int(data['student_id'])
        subject_id = int(data['subject_id'])
        date_col   = data['date_col']
        grade_val  = data.get('grade')
        is_nk      = int(data.get('is_nk', 0))

        if grade_val is not None:
            grade_val = int(grade_val)
            if not (1 <= grade_val <= 100):
                return jsonify({'success': False, 'message': 'Оцінка 1–100'})

        conn = get_db()
        conn.execute("""
            INSERT INTO grades (student_id, subject_id, date_col, grade, is_nk, updated_at)
            VALUES (?,?,?,?,?,datetime('now'))
            ON CONFLICT(student_id, subject_id, date_col)
            DO UPDATE SET grade=excluded.grade, is_nk=excluded.is_nk, updated_at=datetime('now')
        """, (student_id, subject_id, date_col, grade_val, is_nk))
        conn.commit()
        conn.close()

        # Якщо НК — автоматично додаємо заборгованість на 4 тижні + надсилаємо email
        if is_nk:
            deadline = (datetime.now() + timedelta(weeks=4)).strftime("%Y-%m-%dT23:59")
            existing = db_one(
                "SELECT id FROM absences WHERE student_id=? AND subject_id=? AND status='active'",
                (student_id, subject_id)
            )
            if not existing:
                db_exec(
                    "INSERT INTO absences (student_id, subject_id, deadline) VALUES (?,?,?)",
                    (student_id, subject_id, deadline)
                )
                # Надсилаємо email студенту
                student = db_one("SELECT fullname, email FROM users WHERE id=?", (student_id,))
                subject = db_one("SELECT name FROM subjects WHERE id=?", (subject_id,))
                if student and subject and student.get('email'):
                    send_nk_email(
                        student_email=student['email'],
                        student_name=student['fullname'],
                        subject_name=subject['name'],
                        deadline_str=deadline
                    )

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/add_date_column', methods=['POST'])
def add_date_column():
    if session.get('role') not in ['ADMIN', 'TEACHER']:
        return jsonify({'success': False, 'message': 'Доступ заборонено'}), 403
    data = request.get_json()
    try:
        db_exec(
            "INSERT OR IGNORE INTO journal_dates (subject_id, date_val) VALUES (?,?)",
            (int(data['subject_id']), data['date_val'])
        )
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/add_absence', methods=['POST'])
def add_absence():
    if session.get('role') not in ['ADMIN', 'TEACHER']:
        return jsonify({'success': False, 'message': 'Доступ заборонено'}), 403
    data = request.get_json()
    try:
        student_id = int(data['student_id'])
        subject_id = int(data['subject_id'])
        deadline   = data['deadline']
        db_exec(
            "INSERT INTO absences (student_id, subject_id, deadline) VALUES (?,?,?)",
            (student_id, subject_id, deadline)
        )
        # Надсилаємо email студенту
        student = db_one("SELECT fullname, email FROM users WHERE id=?", (student_id,))
        subject = db_one("SELECT name FROM subjects WHERE id=?", (subject_id,))
        if student and subject and student.get('email'):
            send_nk_email(
                student_email=student['email'],
                student_name=student['fullname'],
                subject_name=subject['name'],
                deadline_str=deadline
            )
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/set_email_config', methods=['POST'])
def set_email_config():
    if session.get('role') not in ['ADMIN', 'TEACHER']:
        return jsonify({'success': False, 'message': 'Доступ заборонено'}), 403
    data = request.get_json()
    email    = data.get('email', '').strip()
    password = data.get('password', '').strip()
    if not email or not password:
        return jsonify({'success': False, 'message': 'Заповніть обидва поля'})
    global EMAIL_SENDER, EMAIL_PASSWORD
    EMAIL_SENDER   = email
    EMAIL_PASSWORD = password
    return jsonify({'success': True, 'message': f'Збережено: {email}'})


@app.route('/api/get_email_config')
def get_email_config():
    if session.get('role') not in ['ADMIN', 'TEACHER']:
        return jsonify({'email': ''})
    masked = EMAIL_SENDER if EMAIL_SENDER != 'your_gmail@gmail.com' else ''
    return jsonify({'email': masked})


@app.route('/api/test_email')
def test_email():
    if session.get('role') not in ['ADMIN', 'TEACHER']:
        return jsonify({'success': False, 'message': 'Доступ заборонено'}), 403
    if EMAIL_SENDER == 'your_gmail@gmail.com' or EMAIL_PASSWORD == 'your_app_password_here':
        return jsonify({'success': False, 'message': 'Спочатку збережіть реальний email та пароль'})
    try:
        user = db_one("SELECT email, fullname FROM users WHERE id=?", (session['user_id'],))
        send_nk_email(
            student_email=user['email'],
            student_name=user['fullname'],
            subject_name='Тестовий предмет',
            deadline_str=(datetime.now() + timedelta(weeks=4)).strftime("%Y-%m-%dT23:59")
        )
        return jsonify({'success': True, 'message': f'Тест-лист відправлено на {user["email"]}'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
