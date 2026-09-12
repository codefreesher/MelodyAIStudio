"""Account profile validation and mock backend updates."""

import unittest

from app.core.exceptions import AuthenticationError
from app.providers.mock.auth_provider import MockAuthProvider
from app.services.account_service import AccountService


class AccountProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.provider = MockAuthProvider()
        self.service = AccountService(self.provider)
        self.user = self.provider.authenticate("demo", "123456")

    def test_updates_username_and_password(self) -> None:
        updated = self.service.update(
            self.user,
            {
                "username": "thien123",
                "current_password": "123456",
                "new_password": "654321",
                "confirm_password": "654321",
            },
        )
        self.assertEqual(updated.username, "thien123")
        self.assertEqual(self.provider.authenticate("demo", "654321").username, "thien123")

    def test_rejects_wrong_current_password(self) -> None:
        with self.assertRaisesRegex(AuthenticationError, "không đúng"):
            self.service.update(
                self.user,
                {
                    "username": "thien123",
                    "current_password": "wrong",
                    "new_password": "",
                    "confirm_password": "",
                },
            )

    def test_rejects_password_mismatch(self) -> None:
        with self.assertRaisesRegex(AuthenticationError, "không khớp"):
            self.service.update(
                self.user,
                {
                    "username": "thien123",
                    "current_password": "123456",
                    "new_password": "654321",
                    "confirm_password": "654322",
                },
            )


if __name__ == "__main__":
    unittest.main()
