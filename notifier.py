from __future__ import print_function
import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from twilio.rest import Client

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/sheets.googleapis.com-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/spreadsheets.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'budget-notify'
WEEKLY_BUDGET = 100

TWILIO_SID = os.environ['TWILIO_SID']
TWILIO_TOKEN = os.environ['TWILIO_TOKEN']
SPREADSHEET_ID = os.environ['TRANSACTIONS_SPREADSHEET_ID']
NOTIFICATION_PHONE = os.environ['NOTIFICATION_PHONE']
TWILIO_PHONE = os.environ['TWILIO_PHONE']

TWILIO_CLIENT = Client(TWILIO_SID, TWILIO_TOKEN)


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'sheets.googleapis.com-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def main():

    values = get_raw_values()
    if not values:
        # log some error here?
        send_message("There was an error fetching budget data.")

    spent = get_this_week_spend(values)
    this_week = values[0][11];
    if spent > WEEKLY_BUDGET:
        excess = spent - WEEKLY_BUDGET
        # TODO: Random derogatory phrase
        send_message(this_week + ": DO YOU WANT THINGS?? You have exceeded your budget by $" + str(excess))
    if spent < WEEKLY_BUDGET:
        remaining = WEEKLY_BUDGET - spent
        send_message(this_week + ": You have $" + str(remaining) + " remaining this week.")
    if spent == WEEKLY_BUDGET:
        send_message(this_week + ": STOP!!! NO MORE FUNDS FOR THIS WEEK!")


def get_this_week_spend(values):
    # indices
    week = 11
    amount = 4

    this_week = values[0][week];
    total = 0;
    for row in values:
        if row[week] == this_week:
            if is_valid_expense(row):
                total += row[amount]
        else:
            return abs(total)

def get_raw_values():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discoveryUrl)
    rangeName = 'Transactions!A2:N100'
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range=rangeName, valueRenderOption='UNFORMATTED_VALUE', dateTimeRenderOption='FORMATTED_STRING').execute()
    return result.get('values', [])

def is_valid_expense(row):
    return row[4] < 0


def send_message(message):
    TWILIO_CLIENT.messages.create(
            to=NOTIFICATION_PHONE,
            from_=TWILIO_PHONE,
            body=message
            )


if __name__ == '__main__':
    main()
