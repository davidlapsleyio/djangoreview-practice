import pytest

from users.models import User


@pytest.mark.django_db
class TestUserModel:
    def test_create_user(self):
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="securepass123",
            address="123 Main St",
            phone="555-0100",
        )
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.address == "123 Main St"
        assert user.phone == "555-0100"
        assert user.check_password("securepass123")

    def test_user_str(self):
        user = User(username="testuser")
        assert str(user) == "testuser"
