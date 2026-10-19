import calendar
from datetime import datetime, date, timedelta
import sqlite3
import click

DB_FILE = "calendar.db"

def get_db_connection():
    """Establishes and returns a connection to the SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Creates the events table if it does not already exist."""
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_str TEXT NOT NULL,         -- Format: YYYY-MM-DD
                start_time TEXT NOT NULL,       -- Format: HH:MM
                end_time TEXT NOT NULL,         -- Format: HH:MM
                title TEXT NOT NULL,
                recurrence TEXT DEFAULT 'none'  -- 'none', 'daily', 'weekly', 'monthly'
            )
        """)
        conn.commit()

def parse_relative_date(date_input):
    """Converts literal strings like 'today' or 'tomorrow' into YYYY-MM-DD format."""
    normalized = date_input.lower().strip()
    if normalized == "today":
        return date.today().strftime("%Y-%m-%d")
    elif normalized == "tomorrow":
        return (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    return date_input

def is_matching_recurrence(event_date_str, target_date_str, recurrence):
    """Checks if a recurring event falls on a specific target date."""
    try:
        event_date = datetime.strptime(event_date_str, "%Y-%m-%d").date()
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
    except ValueError:
        return False

    if target_date < event_date:
        return False

    if recurrence == 'daily':
        return True
    elif recurrence == 'weekly':
        return event_date.weekday() == target_date.weekday()
    elif recurrence == 'monthly':
        return event_date.day == target_date.day
    
    return False

def check_conflicts(date_str, start_str, end_str):
    """Scans the database for any overlapping events on the target date."""
    new_start = datetime.strptime(start_str, "%H:%M").time()
    new_end = datetime.strptime(end_str, "%H:%M").time()
    conflicts = []

    with get_db_connection() as conn:
        events = conn.execute("SELECT * FROM events").fetchall()

    for ev in events:
        if ev['date_str'] == date_str or is_matching_recurrence(ev['date_str'], date_str, ev['recurrence']):
            ev_start = datetime.strptime(ev['start_time'], "%H:%M").time()
            ev_end = datetime.strptime(ev['end_time'], "%H:%M").time()
            
            if new_start < ev_end and new_end > ev_start:
                conflicts.append(ev)
                
    return conflicts

@click.group()
def cli():
    """A clean CLI calendar application with SQLite and recurring event support."""
    init_db()

@cli.command()
@click.argument("year", type=int, required=False)
@click.argument("month", type=int, required=False)
def show(year, month):
    """Display a visual month calendar alongside all active events.
    
    If YEAR and MONTH are omitted, defaults to the current month.
    
    Examples:\n
      python calendar_cli.py show\n
      python calendar_cli.py show 2026 10
    """
    if year is None or month is None:
        today = date.today()
        year = year or today.year
        month = month or today.month

    cal = calendar.TextCalendar(calendar.SUNDAY)
    click.echo(cal.formatmonth(year, month))
    
    click.echo(f"--- Events for {year:04d}-{month:02d} ---")
    found = False
    
    with get_db_connection() as conn:
        events = conn.execute("SELECT * FROM events").fetchall()

    num_days = calendar.monthrange(year, month)[1]
    for day in range(1, num_days + 1):
        target_str = f"{year:04d}-{month:02d}-{day:02d}"
        day_events = []
        
        for ev in events:
            if ev['date_str'] == target_str or is_matching_recurrence(ev['date_str'], target_str, ev['recurrence']):
                day_events.append(ev)
                
        day_events.sort(key=lambda x: x['start_time'])
        
        for ev in day_events:
            is_all_day = (ev['start_time'] == "00:00" and ev['end_time'] == "23:59")
            time_tag = "[All Day]" if is_all_day else f"{ev['start_time']}-{ev['end_time']}"
            rec_tag = f" [{ev['recurrence']}]" if ev['recurrence'] != 'none' else ""
            click.echo(f"  * {target_str} @ {time_tag}: ({ev['id']}) {ev['title']}{rec_tag}")
            found = True
                
    if not found:
        click.echo("  No events scheduled for this month.")

@cli.command()
@click.argument("date_str")
def day(date_str):
    """View all events scheduled for a single specific day.
    
    Examples:\n
      python calendar_cli.py day today\n
      python calendar_cli.py day 2026-10-12
    """
    target_date = parse_relative_date(date_str)
    click.echo(f"--- Events for {target_date} ({date_str.lower()}) ---")
    found = False
    
    with get_db_connection() as conn:
        events = conn.execute("SELECT * FROM events").fetchall()

    day_events = []
    for ev in events:
        if ev['date_str'] == target_date or is_matching_recurrence(ev['date_str'], target_date, ev['recurrence']):
            day_events.append(ev)
            
    day_events.sort(key=lambda x: x['start_time'])
    
    for ev in day_events:
        is_all_day = (ev['start_time'] == "00:00" and ev['end_time'] == "23:59")
        time_tag = "[All Day]" if is_all_day else f"{ev['start_time']}-{ev['end_time']}"
        rec_tag = f" [{ev['recurrence']}]" if ev['recurrence'] != 'none' else ""
        click.echo(f"  * {time_tag}: ({ev['id']}) {ev['title']}{rec_tag}")
        found = True
            
    if not found:
        click.echo("  No events scheduled for this day.")

@cli.command()
@click.argument("date_str")
@click.argument("title")
@click.option("--start", default=None, help="Start time formatted as HH:MM")
@click.option("--end", default=None, help="End time formatted as HH:MM")
@click.option("--all-day", is_flag=True, help="Flag to make the event span all day.")
@click.option("--recur", type=click.Choice(['none', 'daily', 'weekly', 'monthly']), default='none', 
              help="Set an optional recurrence pattern.")
def add(date_str, title, start, end, all_day, recur):
    """Add a new single or recurring event to the calendar.
    
    Examples:\n
      python calendar_cli.py add today "Company Holiday" --all-day\n
      python calendar_cli.py add 2026-10-12 "Team Workshop" --start 09:00 --end 17:00
    """
    target_date = parse_relative_date(date_str)
    
    if all_day:
        start_time, end_time = "00:00", "23:59"
    else:
        if not start or not end:
            raise click.UsageError("You must provide --start and --end times unless using --all-day.")
        start_time, end_time = start, end
    
    conflicts = check_conflicts(target_date, start_time, end_time)
    if conflicts:
        click.secho("\n⚠️  WARNING: Schedule Conflict Detected!", fg="yellow", bold=True)
        for c in conflicts:
            click.secho(f"  Overlaps with: ({c['id']}) '{c['title']}'", fg="yellow")
        click.echo("  Proceeding to save event anyway...\n")

    with get_db_connection() as conn:
        conn.execute(
            "INSERT INTO events (date_str, start_time, end_time, title, recurrence) VALUES (?, ?, ?, ?, ?)",
            (target_date, start_time, end_time, title, recur)
        )
        conn.commit()
    click.secho(f"✅ Successfully added event: '{title}' on {target_date} (All-day: {all_day})", fg="green")

@cli.command()
@click.argument("event_id", type=int)
@click.argument("new_title")
def edit(event_id, new_title):
    """Modify the title of an existing event by its unique ID.
    
    Examples:\n
      python calendar_cli.py edit 1 "Updated Holiday Name"
    """
    with get_db_connection() as conn:
        cursor = conn.execute("UPDATE events SET title = ? WHERE id = ?", (new_title, event_id))
        conn.commit()
        
        if cursor.rowcount > 0:
            click.echo(f"Event {event_id} successfully updated to '{new_title}'.")
        else:
            click.echo(f"Error: No event found with ID {event_id}.")

@cli.command()
@click.argument("event_id", type=int)
def remove(event_id):
    """Permanently delete an event by its unique ID.
    
    Examples:\n
      python calendar_cli.py remove 1
    """
    with get_db_connection() as conn:
        cursor = conn.execute("DELETE FROM events WHERE id = ?", (event_id,))
        conn.commit()
        
        if cursor.rowcount > 0:
            click.echo(f"Event {event_id} has been removed.")
        else:
            click.echo(f"Error: No event found with ID {event_id}.")

if __name__ == "__main__":
    cli()
