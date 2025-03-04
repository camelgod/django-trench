import pytest

from django.contrib.auth import get_user_model

from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from rest_framework.test import APIClient

from tests.utils import PATH_AUTH_JWT_LOGIN, get_username_from_jwt, login
from trench.utils import user_token_generator


User = get_user_model()


@pytest.mark.django_db
def test_get_emphemeral_token(active_user_with_email_otp):
    response = login(active_user_with_email_otp)
    assert response.status_code == HTTP_200_OK
    assert (
        user_token_generator.check_token(
            user=None, token=response.data.get("ephemeral_token")
        )
        == active_user_with_email_otp
    )


@pytest.mark.django_db
def test_deactivated_user(deactivated_user_with_email_otp):
    response = login(deactivated_user_with_email_otp)
    assert response.status_code == HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_get_jwt_without_otp(active_user):
    response = login(active_user)
    assert response.status_code == HTTP_200_OK
    assert get_username_from_jwt(response) == getattr(
        active_user,
        User.USERNAME_FIELD,
    )


@pytest.mark.django_db
def test_login_disabled_user(inactive_user):
    """
    Default AUTHENTICATION_BACKEND rejects inactive users, so we test
    against an authentication error or account status.
    :param inactive_user:
    :return:
    """
    response = login(inactive_user)
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert (
        "Unable to login with provided credentials."
        or "User account is disabled." in response.data.get("non_field_errors")
    )


@pytest.mark.django_db
def test_login_missing_field(active_user):
    """
    Default LOGIN rejects wrong username users, so we test
    against an authentication error.
    :param active_user:
    :return:
    """
    client = APIClient()
    response = client.post(
        path=PATH_AUTH_JWT_LOGIN,
        data={
            "username": "",
            "password": "secretkey",
        },
        format="json",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert "This field may not be blank." in response.data.get(User.USERNAME_FIELD)


@pytest.mark.django_db
def test_login_wrong_password(active_user):
    """
    Default LOGIN rejects wrong password users, so we test
    against an authentication error.
    :param active_user:
    :return:
    """
    client = APIClient()
    response = client.post(
        path=PATH_AUTH_JWT_LOGIN,
        data={
            "username": getattr(
                active_user,
                User.USERNAME_FIELD,
            ),
            "password": "wrong",
        },
        format="json",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.data.get("error") == "Unable to login with provided credentials."
