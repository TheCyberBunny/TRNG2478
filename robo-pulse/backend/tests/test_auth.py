"""
Robopulse command center
Day 10 - tests for the auth/token endpoint
"""

from tests.conftest import auth_header

#Happy path test - for when the correct username + password is provided
async def test_login_succeeds_with_correct_credentials(client, seeded_users):
    response = await client.post(
        "/auth/token",
        data={"username": "test_admin", "password": "pw"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


#Sad path test - for when the correct username but wrong password is provided
async def test_login_fails_with_wrong_password(client, seeded_users):
    response = await client.post(
        "/auth/token",
        data={"username": "test_admin", "password": "wrong-password"},
    )
    assert response.status_code == 401

#RBAC test for the registration endpoint
async def test_register_requires_fleet_admin(client, seeded_users):
    payload = {"username": "new_user", "password": "SomePass123!", "role": "Field Operator"}

    #assert that an operator will fail
    operator_response = await client.post(
        "/auth/register", json=payload, headers=auth_header(seeded_users["operator"])
    )
    assert operator_response.status_code == 403

    #assert that an admin will succeed
    admin_response = await client.post(
        "/auth/register", json=payload, headers=auth_header(seeded_users["admin"])
    )
    assert admin_response.status_code == 201