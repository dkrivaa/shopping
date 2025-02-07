import gspread
import os
import json
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
import base64
from datetime import datetime


load_dotenv()


# Get Google sheet
def google_sheet():
    # Get the Base64-encoded secret from the environment variable
    encoded_credentials = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
    # Decode it back to JSON format
    decoded_credentials = base64.b64decode(encoded_credentials).decode("utf-8")
    # Load the credentials as a dictionary
    creds_dict = json.loads(decoded_credentials)
    # Define scopes
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    # Authenticate using the credentials dictionary and defined scopes
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(creds)
    # gc = gspread.service_account(filename='handy-tiger-450017-i3-6522178cef82.json')
    book = client.open('googlebase')
    sheet = book.worksheet('shopping')
    return sheet


# Get last existing order _id
def last_id() -> int:
    sheet = google_sheet()
    # Get all values from column A
    column_a = sheet.col_values(1)  # Column index 1 corresponds to column 'A'
    # Get the last non-empty value
    if column_a:
        last_value = column_a[-1]  # Last non-empty value
        if last_value == '_id':
            last_value = 0
        return int(last_value)
    else:
        return 0


# Add new order
def add_order(order: list):
    sheet = google_sheet()
    # Add id for new order
    _id = last_id() + 1
    order.insert(0, _id)
    # Add order date for new order
    order_date = datetime.today().strftime("%d-%m-%Y")
    order.insert(1, order_date)
    # Add active status to new order
    order.append(1)
    # Append new order to Google sheet
    sheet.append_row(order)


# Update order status
def update_status(_id):
    sheet = google_sheet()
    cell = sheet.find(str(_id), in_column=1)
    cell_address = f'E{cell.row}'
    sheet.update_acell(cell_address, 2)


# Update order amount
def update_amount(_id, new_amount):
    sheet = google_sheet()
    cell = sheet.find(str(_id), in_column=1)
    cell_address = f'D{cell.row}'
    if new_amount is not None:
        sheet.update_acell(cell_address, new_amount)


# Get all active orders
def get_orders() -> list[list[str]]:
    sheet = google_sheet()
    all_rows = sheet.get_all_values()
    active_rows = [row for row in all_rows if row[4] == str(1)]
    return active_rows


