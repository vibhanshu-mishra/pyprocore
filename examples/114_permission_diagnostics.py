"""Interpret example Procore errors locally; no API request is made."""

from pyprocore.auth.permissions import explain_auth_error, explain_permission_error

if __name__ == "__main__":
    print(explain_auth_error(401, {"message": "Unauthorized"}, "client_credentials"))
    print(explain_permission_error(403, {"message": "Forbidden"}, "authorization_code"))
