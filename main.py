"""Core-Python Cold Email Bot.

Uses only Python's standard library. Start with: python main.py
"""
import csv
import getpass
import json
import random
import re
import smtplib
import ssl
import time
from datetime import date, datetime
from email.message import EmailMessage
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
TEMPLATE_DIR = ROOT / "templates"
CONTACTS_FILE = DATA_DIR / "contacts.csv"
SETTINGS_FILE = DATA_DIR / "settings.json"
HISTORY_FILE = DATA_DIR / "send_history.csv"
SUBJECT_FILE = TEMPLATE_DIR / "subject.txt"
BODY_FILE = TEMPLATE_DIR / "body.txt"
RESUME_FILE = ROOT / "resume" / "resume.pdf"

CONTACT_FIELDS = ["name", "email", "title", "company", "status", "sent_at", "error"]
EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def ensure_files():
    """Create required folders and starter files when they do not exist."""
    DATA_DIR.mkdir(exist_ok=True)
    TEMPLATE_DIR.mkdir(exist_ok=True)
    (ROOT / "resume").mkdir(exist_ok=True)

    if not SETTINGS_FILE.exists():
        settings = {
            "sender_name": "Your Name",
            "sender_email": "your_email@gmail.com",
            "portfolio_url": "https://your-portfolio.example",
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 465,
            "daily_limit": 20,
            "min_delay_seconds": 45,
            "max_delay_seconds": 90
        }
        save_settings(settings)

    if not SUBJECT_FILE.exists():
        SUBJECT_FILE.write_text(
            "Application for {{Title}} Role at {{Company}}",
            encoding="utf-8"
        )

    if not BODY_FILE.exists():
        BODY_FILE.write_text(
            "Hi {{Name}},\n\n"
            "I hope you are doing well.\n\n"
            "My name is {{sender_name}}, and I am reaching out to express "
            "my interest in opportunities at {{Company}}.\n\n"
            "You can find my portfolio here: {{portfolio_url}}\n\n"
            "I have attached my resume for your review.\n\n"
            "Thank you for your time.\n\n"
            "Best regards,\n{{sender_name}}\n",
            encoding="utf-8"
        )

    if not CONTACTS_FILE.exists():
        with CONTACTS_FILE.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=CONTACT_FIELDS)
            writer.writeheader()

    if not HISTORY_FILE.exists():
        with HISTORY_FILE.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(
                file, fieldnames=["date", "email", "status", "time"]
            )
            writer.writeheader()


def load_settings():
    with SETTINGS_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_settings(settings):
    """Write settings safely through a temporary file."""
    temporary = SETTINGS_FILE.with_suffix(".tmp")
    temporary.write_text(json.dumps(settings, indent=4), encoding="utf-8")
    temporary.replace(SETTINGS_FILE)


def normalize_email(value):
    return str(value or "").strip().lower()


def valid_email(value):
    return bool(EMAIL_PATTERN.fullmatch(normalize_email(value)))


def load_contacts():
    with CONTACTS_FILE.open("r", newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def save_contacts(contacts):
    """Replace the contacts CSV with the current in-memory records."""
    temporary = CONTACTS_FILE.with_suffix(".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=CONTACT_FIELDS)
        writer.writeheader()
        for contact in contacts:
            writer.writerow({field: contact.get(field, "") for field in CONTACT_FIELDS})
    temporary.replace(CONTACTS_FILE)


def import_contacts():
    path_text = input("Path to contacts CSV: ").strip().strip('"')
    source = Path(path_text).expanduser()
    if not source.is_file():
        print("File not found.")
        return

    existing = load_contacts()
    known_emails = {normalize_email(row.get("email")) for row in existing}
    added = 0
    skipped = 0

    try:
        with source.open("r", newline="", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            if not reader.fieldnames:
                print("CSV must contain a header row.")
                return

            for raw in reader:
                # Accept common column names from different CSV exports.
                lowered = {
                    str(key or "").strip().lower(): str(value or "").strip()
                    for key, value in raw.items()
                }
                email = normalize_email(
                    lowered.get("email")
                    or lowered.get("email address")
                    or lowered.get("e-mail")
                )
                if not valid_email(email) or email in known_emails:
                    skipped += 1
                    continue

                contact = {
                    "name": lowered.get("name") or lowered.get("full name") or "there",
                    "email": email,
                    "title": lowered.get("title") or lowered.get("role") or lowered.get("designation") or "",
                    "company": lowered.get("company") or lowered.get("company name") or "",
                    "status": "pending",
                    "sent_at": "",
                    "error": ""
                }
                existing.append(contact)
                known_emails.add(email)
                added += 1
    except (OSError, csv.Error) as error:
        print(f"Could not import CSV: {error}")
        return

    save_contacts(existing)
    print(f"Imported {added} contacts. Skipped {skipped} invalid/duplicate rows.")


def edit_sender_profile():
    settings = load_settings()
    print("\nLeave a field blank to keep its current value.")
    for key, label in [
        ("sender_name", "Sender display name"),
        ("sender_email", "Sender Gmail address"),
        ("portfolio_url", "Portfolio URL")
    ]:
        current = settings.get(key, "")
        value = input(f"{label} [{current}]: ").strip()
        if value:
            if key == "sender_email" and not valid_email(value):
                print("That email address does not look valid. Keeping the old value.")
                continue
            settings[key] = value

    save_settings(settings)
    print("Sender profile saved.")


def edit_template_file(path, label):
    print(f"\nEditing {label}.")
    print("Enter the new content. Type END on a line by itself to save.")
    print("To keep the current content, just press Enter at the first prompt.")
    first_line = input("> ")
    if not first_line:
        print("No changes made.")
        return

    lines = [first_line]
    while True:
        line = input()
        if line == "END":
            break
        lines.append(line)

    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"{label} saved.")


def edit_email_template():
    edit_template_file(SUBJECT_FILE, "email subject")
    edit_template_file(BODY_FILE, "email body")


def render_text(template, contact, settings):
    """Replace the supported placeholders without any template package."""
    values = {
        "Name": contact.get("name") or "there",
        "Company": contact.get("company") or "your company",
        "Title": contact.get("title") or "suitable",
        "sender_name": settings.get("sender_name", ""),
        "portfolio_url": settings.get("portfolio_url", "")
    }

    rendered = template
    for key, value in values.items():
        rendered = rendered.replace("{{" + key + "}}", str(value))
    return rendered


def preview_email():
    contacts = load_contacts()
    if not contacts:
        print("No contacts available. Import a CSV first.")
        return

    for index, contact in enumerate(contacts[:10], start=1):
        print(f"{index}. {contact.get('name')} <{contact.get('email')}>")
    choice = input("Choose a contact number (default 1): ").strip()
    try:
        selected = contacts[int(choice) - 1] if choice else contacts[0]
    except (ValueError, IndexError):
        print("Invalid selection.")
        return

    settings = load_settings()
    subject_template = SUBJECT_FILE.read_text(encoding="utf-8")
    body_template = BODY_FILE.read_text(encoding="utf-8")
    print("\n" + "=" * 60)
    print("TO:", selected.get("email"))
    print("SUBJECT:", render_text(subject_template, selected, settings))
    print("-" * 60)
    print(render_text(body_template, selected, settings))
    print("=" * 60)


def count_attempts_today():
    today = date.today().isoformat()
    count = 0
    if not HISTORY_FILE.exists():
        return count
    with HISTORY_FILE.open("r", newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            if row.get("date") == today:
                count += 1
    return count


def record_attempt(email, status):
    now = datetime.now()
    with HISTORY_FILE.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file, fieldnames=["date", "email", "status", "time"]
        )
        writer.writerow({
            "date": now.date().isoformat(),
            "email": email,
            "status": status,
            "time": now.isoformat(timespec="seconds")
        })


def make_message(settings, contact, subject, body):
    message = EmailMessage()
    message["From"] = f"{settings['sender_name']} <{settings['sender_email']}>"
    message["To"] = contact["email"]
    message["Subject"] = subject
    message.set_content(body)

    if RESUME_FILE.is_file():
        with RESUME_FILE.open("rb") as file:
            message.add_attachment(
                file.read(),
                maintype="application",
                subtype="pdf",
                filename=RESUME_FILE.name
            )
    return message


def send_campaign():
    settings = load_settings()
    contacts = load_contacts()
    pending = [
        contact for contact in contacts
        if contact.get("status", "pending") == "pending"
        and valid_email(contact.get("email"))
    ]

    if not pending:
        print("There are no valid pending contacts.")
        return

    already_attempted = count_attempts_today()
    daily_limit = int(settings.get("daily_limit", 20))
    remaining = max(0, daily_limit - already_attempted)

    if remaining == 0:
        print(f"Daily attempt limit ({daily_limit}) has already been reached.")
        return

    batch = pending[:remaining]
    print(f"\nPending contacts: {len(pending)}")
    print(f"Daily attempts already used: {already_attempted}/{daily_limit}")
    print(f"This run can process up to: {len(batch)} contacts")

    mode = input("Choose mode: [P]ractice or [S]end real emails: ").strip().lower()
    if mode not in {"p", "s"}:
        print("Cancelled.")
        return

    if mode == "p":
        for contact in batch:
            print(f"[PRACTICE] Would send to {contact['name']} <{contact['email']}>")
        print("Practice finished. No email was sent and no status was changed.")
        return

    print("\nOnly send to people you have a legitimate reason to contact.")
    print("The attempt limit counts failures too. Unknown outcomes are not retried.")
    confirm = input(f"Type SEND {len(batch)} to confirm: ").strip()
    if confirm != f"SEND {len(batch)}":
        print("Sending cancelled.")
        return

    smtp_password = getpass.getpass("Gmail App Password (input hidden): ")
    if not smtp_password:
        print("No password entered.")
        return

    host = settings.get("smtp_host", "smtp.gmail.com")
    port = int(settings.get("smtp_port", 465))
    context = ssl.create_default_context()
    subject_template = SUBJECT_FILE.read_text(encoding="utf-8")
    body_template = BODY_FILE.read_text(encoding="utf-8")

    try:
        server = smtplib.SMTP_SSL(host, port, context=context, timeout=30)
        server.login(settings["sender_email"], smtp_password)
    except (OSError, smtplib.SMTPException) as error:
        print(f"Could not connect/authenticate with SMTP: {error}")
        return

    try:
        for contact in batch:
            email = normalize_email(contact["email"])
            subject = render_text(subject_template, contact, settings)
            body = render_text(body_template, contact, settings)
            status = "unknown"

            # Record the attempt before network submission. This prevents a
            # crash/restart from silently exceeding the daily attempt cap.
            record_attempt(email, "attempted")
            try:
                message = make_message(settings, contact, subject, body)
                server.send_message(message)
                status = "sent"
                contact["status"] = "sent"
                contact["sent_at"] = datetime.now().isoformat(timespec="seconds")
                contact["error"] = ""
                print(f"Accepted by SMTP: {email}")
            except (OSError, smtplib.SMTPException) as error:
                # SMTP can fail after the server has accepted the message.
                # Mark it unknown rather than automatically retrying.
                status = "unknown"
                contact["status"] = "unknown"
                contact["error"] = str(error)
                print(f"Unknown outcome for {email}: {error}")
                save_contacts(contacts)
                record_attempt(email, status)
                break
            finally:
                save_contacts(contacts)

            record_attempt(email, status)
            if contact is not batch[-1]:
                low = max(0, int(settings.get("min_delay_seconds", 45)))
                high = max(low, int(settings.get("max_delay_seconds", 90)))
                delay = random.randint(low, high)
                print(f"Waiting {delay} seconds before the next email...")
                time.sleep(delay)
    finally:
        try:
            server.quit()
        except (OSError, smtplib.SMTPException):
            pass

    print("Campaign finished. Check contact statuses and send_history.csv.")


def show_contacts():
    contacts = load_contacts()
    print(f"\nTotal contacts: {len(contacts)}")
    for contact in contacts[:30]:
        print(
            f"{contact.get('status', 'pending'):8} | "
            f"{contact.get('name', '')[:24]:24} | "
            f"{contact.get('email', '')}"
        )
    if len(contacts) > 30:
        print(f"... and {len(contacts) - 30} more.")


def main():
    ensure_files()
    while True:
        print("\n" + "=" * 48)
        print("       CORE PYTHON COLD EMAIL BOT")
        print("=" * 48)
        print("1. View / edit sender profile")
        print("2. Edit email subject and body")
        print("3. Preview personalized email")
        print("4. Import contacts from CSV")
        print("5. View contacts")
        print("6. Run campaign (practice or real)")
        print("7. Exit")

        choice = input("\nChoose an option: ").strip()
        if choice == "1":
            edit_sender_profile()
        elif choice == "2":
            edit_email_template()
        elif choice == "3":
            preview_email()
        elif choice == "4":
            import_contacts()
        elif choice == "5":
            show_contacts()
        elif choice == "6":
            send_campaign()
        elif choice == "7":
            print("Goodbye.")
            break
        else:
            print("Choose a number from 1 to 7.")


if __name__ == "__main__":
    ensure_files()
    main()
