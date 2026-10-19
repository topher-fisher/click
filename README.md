# Click CLI Calendar Application

A clean, modular command-line interface (CLI) calendar and agenda tracking application built with **Python**, **Click**, and a local **SQLite** database layer. It features precise single-day lookups, automated visual monthly summaries, conflict warning alerts, and robust recurring event patterns.

## ✨ Features

*   **SQLite Datastore:** Stores your structured timeline safely without third-party server overhead or heavy background processing.
*   **Smart Parsing Syntax:** Accepts literal calendar dates (`YYYY-MM-DD`) or fast semantic shortcuts (`today`, `tomorrow`).
*   **Flexible Time Handling:** Supports designated standard meeting timeframes or quick comprehensive `--all-day` flags.
*   **Recurrence Logic:** Handles complex scheduling overhead by duplicating daily, weekly, or monthly event matching flags effortlessly.
*   **Non-Blocking Conflict Checks:** Identifies overlapping intervals instantly, warning you before writing to disk without breaking your workflow.

---

## 🚀 Installation & Prerequisites

This application uses Python 3.11+ and relies on the `click` toolkit interface package. SQLite utilities run out-of-the-box natively without external database dependencies.

1. **Clone or locate your directory:**
   ```bash
   cd ~/at-home-work/click
   ```

2. **Install the CLI wrapper dependencies:**
   ```bash
   pip install click
   ```

3. **Verify installation:**
   ```bash
   python3 calendar_cli.py --help
   ```

---

## 🛠️ Usage Examples

### 1. View Visual Month Summary
Displays a clean textual calendar grid, accompanied by an ordered list of matched standard or recurring actions. Leaving out the year and month will default automatically to your system's current live tracking month.
```bash
# View the current month automatically
python3 calendar_cli.py show

# Look up an explicit month profile
python3 calendar_cli.py show 2026 10
```

### 2. Check a Single Day Breakdown
Pulls up an isolated list of assignments chronologically sorted by start intervals using exact strings or friendly nicknames.
```bash
python3 calendar_cli.py day today
python3 calendar_cli.py day tomorrow
python3 calendar_cli.py day 2026-10-14
```

### 3. Add New Items (With Time Slots or All-Day Flags)
Create entries using target time boundaries or all-day configurations. If a new block matches an ongoing event, the console prints a yellow conflict log statement but saves your entry anyway.
```bash
# Add a fixed-hour session
python3 calendar_cli.py add today "Sync Alignment" --start 09:00 --end 10:00

# Add an item with automated daily recurrence
python3 calendar_cli.py add tomorrow "Lunch Break" --start 12:00 --end 13:00 --recur daily

# Add an All-Day Event
python3 calendar_cli.py add 2026-10-14 "Wedding Anniversary" --all-day
```

### 4. Edit Existing Items
Modify event descriptions without restructuring stored timeframe indices. Use the system identifier keys (`id`) printed in the lists.
```bash
python3 calendar_cli.py edit 1 "Updated Anniversary Title"
```

### 5. Remove Events
Permanently drop a row index out of the local database sequence by specifying its transaction ID value.
```bash
python3 calendar_cli.py remove 1
```

---

## 🗃️ Database Engine Structure
The script auto-creates a local transactional data wrapper named `calendar.db` inside your active source root folder. Rows map directly under these specifications:

| Column Name | Storage Type | Details / Format Configurations |
| :--- | :--- | :--- |
| `id` | `INTEGER` | Primary auto-incrementing record key identifier |
| `date_str` | `TEXT` | Static launch tracking timestamp (`YYYY-MM-DD`) |
| `start_time` | `TEXT` | 24-hour hour boundary format (`HH:MM`) |
| `end_time` | `TEXT` | 24-hour end boundary format (`HH:MM`) |
| `title` | `TEXT` | Custom description data text block |
| `recurrence`| `TEXT` | Algorithmic configuration limits (`none`, `daily`, `weekly`, `monthly`) |
