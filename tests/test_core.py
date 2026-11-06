import sys
import tempfile
import unittest
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

import main


class CorePythonBotTests(unittest.TestCase):
    def test_email_validation(self):
        self.assertTrue(main.valid_email("Person@example.com"))
        self.assertFalse(main.valid_email("not-an-email"))

    def test_template_rendering(self):
        contact = {
            "name": "Asha",
            "company": "Example Ltd",
            "title": "HR Manager"
        }
        settings = {
            "sender_name": "Balaji",
            "portfolio_url": "https://example.com"
        }
        result = main.render_text(
            "Hi {{Name}} from {{Company}} - {{Title}} - {{sender_name}} - {{portfolio_url}}",
            contact,
            settings
        )
        self.assertEqual(
            result,
            "Hi Asha from Example Ltd - HR Manager - Balaji - https://example.com"
        )

    def test_normalize_email(self):
        self.assertEqual(main.normalize_email("  TEST@Example.com "), "test@example.com")


if __name__ == "__main__":
    unittest.main()
