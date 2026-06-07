# Attendance & Leave Management Bot

A simple and reliable Attendance & Leave Management System built with Python, `python-telegram-bot`, and SQLite.

It is designed for small teams that want an easy replacement for manual WhatsApp attendance tracking.

## Features

### Employee
- `/start` to register and open the attendance menu
- Inline buttons for:
  - `Present`
  - `Leave`
  - `My Balance`
- One attendance submission per employee per day
- Automatic leave balance calculation for the current month

### Admin
- `/report` for today's attendance summary
- `/monthly` for a month-to-date summary of all employees
- `/employees` for all registered employees and their leave balances

## Business Rules

- Each employee gets `4` leaves per month by default
- Unused leaves do not carry forward
- Leave balance resets naturally every new month because usage is calculated month-by-month
- Duplicate attendance for the same employee and date is blocked

## Project Structure

```text
telegram_bot/
├── attendance_bot/
│   ├── __init__.py
│   ├── config.py
│   ├── db.py
│   ├── handlers.py
│   ├── keyboards.py
│   └── utils.py
├── .env.example
├── bot.py
├── README.md
└── requirements.txt
```

## Database Schema

### `employees`
- `id`
- `name`
- `telegram_id`

### `attendance`
- `id`
- `employee_id`
- `date`
- `status`

## Setup Instructions

1. Create and activate a virtual environment.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

2. Install dependencies.

```powershell
pip install -r requirements.txt
```

3. Create your environment file.

```powershell
Copy-Item .env.example .env
```

4. Add your Telegram bot token and admin Telegram user ID to `.env`.

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
ADMIN_TELEGRAM_IDS=123456789
DATABASE_PATH=attendance.db
MONTHLY_LEAVE_LIMIT=4
```

5. Run the bot.

```powershell
python bot.py
```

## How It Works

### Employee Flow
1. Employee sends `/start`
2. Bot registers the employee automatically using their Telegram profile name
3. Bot shows inline buttons
4. Employee taps `Present` or `Leave`
5. Bot saves the attendance in SQLite

### Leave Balance Logic
- Monthly leave limit is controlled by `MONTHLY_LEAVE_LIMIT`
- Leaves are counted only inside the current calendar month
- Remaining balance = `monthly limit - leaves used`

## Example Bot Messages

### `/start`

```text
Hi Rahul Sharma, your attendance bot is ready.

Use the buttons below to mark attendance, apply leave, or check your leave balance.
```

### `Present`

```text
Attendance marked as Present for 2026-06-07.
```

### `Leave`

```text
Leave marked for 2026-06-07.
Remaining leaves this month: 3
```

### `My Balance`

```text
Leave Balance
Total leaves allowed: 4
Leaves used: 1
Remaining leaves: 3
```

### `/report`

```text
Attendance Report for 2026-06-07
Present: 6
Leave: 2

Present Employees: Asha, Deepak, Kavya, Mohit, Rina, Yusuf
On Leave: Neha, Rahul
```

### `/monthly`

```text
Monthly Summary (2026-06-01 to 2026-06-07)
Asha: Present 5, Leave 1, Remaining Leave 3
Deepak: Present 6, Leave 0, Remaining Leave 4
Neha: Present 4, Leave 2, Remaining Leave 2
```

### `/employees`

```text
Registered Employees
Asha (Telegram ID: 111111111) - Used 1, Remaining 3
Deepak (Telegram ID: 222222222) - Used 0, Remaining 4
```

## Example Screenshots

You can use these message examples as screenshot references when presenting the project:
- Start menu with `Present`, `Leave`, and `My Balance` inline buttons
- Leave confirmation message showing updated balance
- Admin daily report output
- Admin monthly summary output

## Deployment on Render

Use a **Background Worker** service.

1. Push the project to GitHub
2. Create a new Render Background Worker
3. Set:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python bot.py`
4. Add environment variables:
   - `TELEGRAM_BOT_TOKEN`
   - `ADMIN_TELEGRAM_IDS`
   - `DATABASE_PATH=attendance.db`
   - `MONTHLY_LEAVE_LIMIT=4`

### Important Render Note
- Render local disk is not durable on some plans and redeploys
- For production, prefer a persistent disk or move SQLite to a managed database if long-term retention matters
- For a very small team and simple deployment, SQLite is still fine for a starter version

## Deployment on Railway

1. Push the project to GitHub
2. Create a new Railway project from the repository
3. Add environment variables:
   - `TELEGRAM_BOT_TOKEN`
   - `ADMIN_TELEGRAM_IDS`
   - `DATABASE_PATH=attendance.db`
   - `MONTHLY_LEAVE_LIMIT=4`
4. Set the start command to:

```text
python bot.py
```

## Reliability Notes

- SQLite keeps the solution simple and dependable
- Unique constraints prevent duplicate attendance entries
- Month-based balance calculation avoids manual leave-reset jobs
- Admin access is limited through `ADMIN_TELEGRAM_IDS`

## Future Improvements

- Export monthly report to CSV
- Support half-day leave
- Add holiday calendar support
- Add multiple admin roles
