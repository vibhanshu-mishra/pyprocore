"""Print safe, local enterprise authentication guidance."""

from pyprocore.auth.permissions import explain_app_connection_issue, explain_environment_mismatch

if __name__ == "__main__":
    print(explain_app_connection_issue("client_credentials"))
    print(explain_environment_mismatch("https://login.procore.com", "https://api.procore.com"))
