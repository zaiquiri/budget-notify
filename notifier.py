#!/usr/bin/env python

from __future__ import print_function
import httplib2
import os
import calendar

from apiclient import discovery
from datetime import datetime
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from twilio.rest import Client

Logger = open('/home/pi/projects/budget-notify/log.txt', 'a')
LOG_TIME_FORMAT = "%m/%d/%y %H:%M"
Logger.write("[" + datetime.now().strftime(LOG_TIME_FORMAT) + "] Starting script...\n")

try:
  import argparse
  flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except:
  flags = None


SCOPES = 'https://www.googleapis.com/auth/spreadsheets.readonly'
CLIENT_SECRET_FILE = '/home/pi/projects/budget-notify/client_secret.json'
APPLICATION_NAME = 'budget-notify'
WEEKLY_BUDGET = 100

SPREADSHEET_ID = os.environ['TRANSACTIONS_SPREADSHEET_ID']
NOTIFICATION_PHONE = os.environ['NOTIFICATION_PHONE']
TWILIO_SID = os.environ['TWILIO_SID']
TWILIO_TOKEN = os.environ['TWILIO_TOKEN']
TWILIO_PHONE = os.environ['TWILIO_PHONE']
TWILIO_CLIENT = Client(TWILIO_SID, TWILIO_TOKEN)

INVALID_PAYMENTS = [
    "PAYROLL",
    "Monthly Interest Paid",
    "Manhatanville Mezz",
    "Withdrawal to 360 Savings",
    "Withdrawal from CAPITAL ONE ONLINE PMT",
    "Withdrawal from CITI CARD ONLINE PAYMENT",
    "Withdrawal from CHASE CREDIT CRD EPAY",
    "ONLINE PAYMENT, THANK YOU",
    "Payment Thank You - Web",
    "CITICARDS CASH REWARD"]

def get_credentials():
    credential_path = '/home/pi/projects/budget-notify/credentials.json'
    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
	Logger.write("[" + datetime.now().strftime(LOG_TIME_FORMAT) + "] No stored credentials, starting client-secret flow...\n")
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
	credentials = tools.run_flow(flow, store, flags)
    return credentials

def main():
    values = get_raw_values()
    if not values:
	Logger.write("[" + datetime.now().strftime(LOG_TIME_FORMAT) + "] There was an error fetching data from Sheets.\n")
        send_message("There was an error fetching budget data.")

    spent = get_this_week_spend(values)
    this_week = values[0][11];
    latest_day = calendar.day_name[datetime.strptime(values[0][0], '%m/%d/%Y').weekday()]
    send_message("Week " + this_week + ": As of " + latest_day + " you've spent " + '${:,.2f}'.format(spent))

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
    for desc in INVALID_PAYMENTS:
        if row[3].lower().find(desc.lower()) != -1:
            return False
    return True;

def send_message(message):
    Logger.write("[" + datetime.now().strftime(LOG_TIME_FORMAT) + "] Sending message...\n")
    TWILIO_CLIENT.messages.create(
            to=NOTIFICATION_PHONE,
            from_=TWILIO_PHONE,
            body=message
            )

if __name__ == '__main__':
    main()
