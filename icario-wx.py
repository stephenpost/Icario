import csv
import os.path
from datetime import datetime
import logging
import requests
from logging.handlers import RotatingFileHandler
import simplejson as json
import sys


logformatter = logging.Formatter('%(asctime)s [%(levelname)-5.5s]  %(message)s')
logger = logging.getLogger('icario-wx')
logger.setLevel(logging.INFO)

filehandler = logging.handlers.RotatingFileHandler('{0}.log'.format('icario-wx'), mode='w',
                                                   maxBytes=5 * 1024 * 1024, backupCount=2, encoding=None, delay=0)
filehandler.setFormatter(logformatter)
logger.addHandler(filehandler)

consolehandler = logging.StreamHandler(sys.stdout)
consolehandler.setFormatter(logformatter)
logger.addHandler(consolehandler)


class WxData:
    def __init__(self, datetime, temperature, condition, contact_method):
        self.datetime = datetime
        self.temperature = temperature
        self.condition = condition
        self.contact_method = contact_method



def init():
    return True

def get_data_from_api():
    apiurl = 'http://api.openweathermap.org/data/2.5/forecast?q=minneapolis,us&units=imperial&APPID=09110e603c1d5c272f94f64305c09436'

    try:
        r = requests.get(
            apiurl,
            timeout=30
        )
        data = json.loads(r.text)
        return data['list']

    except requests.exceptions.Timeout as t:
        logger.error("Request to API timeout: %s" % t)
        logger.error("Requested URL: %s" % apiurl)

    except requests.exceptions.RequestException as e:
        logger.error("Request exception: %s" % e)


def process_wx_data(wx_data):
    wxdatalist = []
    for wxdata in wx_data:
        contact_preferece = ''
        wx_condition = ''
        wx_dt = wxdata['dt_txt']
        wx_temp = wxdata['main']['temp']
        for wx in wxdata['weather']:
            wx_condition = wx['main']

        if float(wx_temp) > 75.0 and wx_condition.lower == 'clear':
            contact_preferece = 'Text Message'
        elif 55.0 <= float(wx_temp) <= 75.0:
            contact_preferece = 'EMail'
        elif float(wx_temp) < 55.0 or wx_condition.lower == 'rain':
            contact_preferece = 'Phone Call'
        else:
            contact_preferece = 'Undefined'

        logger.info('-------------------------------')
        logger.info('wx_dt: ' + wx_dt)
        logger.info('wx_temp: ' + str(wx_temp))
        logger.info('wx_condition: ' + wx_condition)
        logger.info('preferred contact method: ' + contact_preferece)

        wxdatalist.append(WxData(wx_dt, wx_temp, wx_condition, contact_preferece))
    return wxdatalist


def write_output_file(wxobject_list):
    now = datetime.now()
    output_file = 'preferred-contact-' + now.strftime('%Y%m%d-%H%M%S') + '.csv'
    f = open(output_file, 'w')
    filewriter = csv.writer(f)
    filewriter.writerow(['timestamp', 'temperature', 'wx condition', 'preferred contact method'])
    for wxobject in wxobject_list:
        filewriter.writerow([wxobject.datetime, wxobject.temperature, wxobject.condition, wxobject.contact_method])
    f.close()


if __name__ == '__main__':
    init()
    wx_data_list = get_data_from_api()
    wxdata_object_list = process_wx_data(wx_data_list)
    write_output_file(wxdata_object_list)
    print()
