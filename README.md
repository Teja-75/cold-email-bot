# Core Python Cold Email Bot

A beginner-friendly command-line cold email project built using **only Python's standard library**.

There is no Flask, React, SQLAlchemy, pandas, Jinja2, dotenv, or other third-party package.

## Python tools used

- `csv` — read and write contacts
- `json` — save sender settings
- `pathlib` — work with files and folders
- `re` — basic email validation
- `smtplib` and `ssl` — connect to Gmail SMTP securely
- `email.message.EmailMessage` — construct email messages
- `getpass` — ask for the app password without displaying it
- `datetime` — record sending dates and times
- `time` and `random` — pause between messages
- `unittest` — test core functions

## Requirements

- Python 3.10 or later
- A Gmail account with 2-Step Verification and a Gmail App Password for real sending
- Internet connection for real sending

No `pip install` command is required.

## Run

Open this folder in VS Code or a terminal:

```powershell
python main.py
```

The program creates missing data files and template files automatically.

## Menu

1. View/edit sender name, sender email, and portfolio URL.
2. Edit the email subject and body directly in the terminal.
3. Preview a personalized email for a selected contact.
4. Import contacts from a CSV file.
5. View the first 30 contacts.
6. Run a practice campaign or send real emails.
7. Exit.

## Contact CSV format

The project includes `data/contacts.csv`. You can import another CSV with these columns:

```csv
name,email,title,company
Asha Rao,asha@example.com,HR Manager,Example Technologies
Ravi Kumar,ravi@example.com,Recruiter,Northwind Systems
```

Common alternatives such as `full name`, `email address`, `role`, and `company name` are also recognized.

Duplicate email addresses are skipped.

## Edit sender details

Choose menu option 1. The values are saved in `data/settings.json`.

## Edit the email

Choose menu option 2. Enter the subject and body. Type `END` on a line by itself to finish each field.

Available placeholders:

- `{{Name}}`
- `{{Company}}`
- `{{Title}}`
- `{{sender_name}}`
- `{{portfolio_url}}`

Choose menu option 3 to preview the personalized result before sending.

## Gmail SMTP setup

1. Enable 2-Step Verification in your Google Account.
2. Create an App Password at https://myaccount.google.com/apppasswords.
3. Set your Gmail address using menu option 1.
4. When you choose real sending, enter the App Password at the hidden prompt.

The app password is not stored in a project file. Do not use your normal Gmail password.

Default SMTP configuration:
- Host: `smtp.gmail.com`
- Port: `465` (SSL)

If you change the sender email, use the App Password belonging to that same Gmail account.

## Resume attachment

Put your own PDF at:

```text
resume/resume.pdf
```

If the file is absent, the email is sent without an attachment.

## Safety

- Start with Practice mode.
- Real sending requires typing an explicit confirmation.
- The daily attempt limit defaults to 20 and is recorded in `data/send_history.csv`.
- Failed/uncertain attempts count toward the limit.
- If the SMTP connection fails during submission, the contact is marked `unknown`; the program stops the batch rather than automatically retrying a possibly accepted message.
- Only contact people where you have a legitimate reason to do so. Follow applicable privacy, anti-spam, and email-provider policies, and include an opt-out route where required.
- `sent` means the SMTP server accepted the message for submission. It does not confirm inbox delivery.

## Project structure

```text
Core_Python_Cold_Email_Bot/
├── main.py
├── README.md
├── data/
│   ├── contacts.csv
│   ├── settings.json
│   └── send_history.csv
├── templates/
│   ├── subject.txt
│   └── body.txt
├── resume/
│   └── README.txt
└── tests/
    └── test_core.py
```

## Run tests

```powershell
python -m unittest discover -s tests -v
```

The tests use only the standard library.
