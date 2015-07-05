#!/usr/bin/python2

import httplib2
import os
import sys
import dateutil.parser
import time
from pytz import UTC

from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools

import datetime

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Google Calendar API Quickstart'
CAL = "TV"
POLL_TIME = 600

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
                                   'calendar-quickstart.json')

    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatability with Python 2.6
            credentials = tools.run(flow, store)
        print 'Storing credentials to ' + credential_path
    return credentials

def get_events(calendar_name, ts):
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)

    isots = ts.isoformat()
    cal_list = service.calendarList().list().execute().get('items')
    for cal in cal_list:
        if cal["summary"] == calendar_name:
            cid = cal["id"]
    if cid is None:
        raise RuntimeError("Calendario non trovato")

    eventsResult = service.events().list(
        calendarId=cid, timeMin=isots, maxResults=10, singleEvents=True,
        orderBy='startTime').execute()
    events = eventsResult.get('items', [])

    res = []
    for event in events:
        start = dateutil.parser.parse(event['start'].get('dateTime', event['start'].get('date')))
        end = dateutil.parser.parse(event['end'].get('dateTime', event['end'].get('date')))
        if start >= ts:
            res.append((event['summary'], start, end))
    return res

class App:
    def __init__(self):
        self.q = []
        self.pi = "pi" in sys.argv
        self.sleep_time = 1
        self.update_events_time = 600
        self.last_update = datetime.datetime(1900, 1, 1)
        self.offset = 0

    def now(self):
        return UTC.localize(datetime.datetime.utcnow() + datetime.timedelta(seconds = self.offset))

    def execute(self, event):
        ts, cmd, parms = event
        sys = None
        if cmd == "rec":
            sys = 'registra "%s"' % parms
        elif cmd == "stop":
            sys = "stop"
        elif cmd == "wakeup":
            sys = "wakeup"
        if sys:
            os.system("nohup %s&" % sys)

    def main(self):
        next_update = self.now() - datetime.timedelta(seconds = 1)
        while True:
            now = self.now()
            for e in self.q:
                events = [e for e in self.q if e[0] <= now]
                for e in events:
                    self.execute(e)
                if events:
                    self.q = [e for e in self.q if e[0] > now]
            if now > next_update:
                events = get_events("TV", next_update)
                next_update = next_update + datetime.timedelta(seconds=self.update_events_time)
                for parms, start, end in events:
                    if start < next_update:
                        if self.pi:
                            self.q.append((start, "wakeup"))
                        else:
                            self.q.append((start, "rec", parms))
                            self.q.append((end, "stop", None))
            time.sleep(self.sleep_time)

if __name__ == '__main__':
    App().main()

