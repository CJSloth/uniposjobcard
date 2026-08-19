from nicegui import ui

# Simple session store for the local app
current_user = {
    "is_logged_in": False,
    "email": "",
    "name": "",
    "technician_mapping": "C.J. Celliers"  # Defaults to your profile
}

def login_user(email, name):
    current_user["is_logged_in"] = True
    current_user["email"] = email
    current_user["name"] = name
    ui.notify(f'Welcome back, {name}!', type='positive')

def logout_user():
    current_user["is_logged_in"] = False
    current_user["email"] = ""
    current_user["name"] = ""
    ui.notify('Logged out successfully.', type='info')