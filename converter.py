#!python3

import datetime
import re
import sys

'''

convert a dump of Achewood.html to prints en-route to re-producing an rss feed

python3 converter.py < Achewood.html > achewood.index

'''


def month_name_to_number(name):
    if name == 'January':
        return 1
    elif name == 'February':
        return 2
    elif name == 'March':
        return 3
    elif name == 'April':
        return 4
    elif name == 'May':
        return 5
    elif name == 'June':
        return 6
    elif name == 'July':
        return 7
    elif name == 'August':
        return 8
    elif name == 'September':
        return 9
    elif name == 'October':
        return 10
    elif name == 'November':
        return 11
    elif name == 'December':
        return 12

def main():
    monthRe = re.compile(r'''<h3><a name=[^>]+>(?P<month>[a-zA-Z]+) (?P<year>[0-9]+)</a></h3>''')
    dayRe = re.compile(r'''class="archiveDate">(?P<day>[a-zA-Z]+), (?P<mon>[a-zA-Z]+) (?P<dom>\d+).*''')
    stripRe = re.compile(r'''class="archiveLink"><a href="(?P<url>[^"]+)">(?P<title>[^>]+)</a>.*''')

    year = 0
    month = 0
    day = 0
    url = ''
    title = ''

    for line in sys.stdin.readlines():
        # print(f'got line {line}')
        monthMatch = monthRe.search(line)
        if monthMatch:
            # print('month match')
            month = monthMatch.group('month')
            year = monthMatch.group('year')
        dayMatch = dayRe.search(line)
        if dayMatch:
            # print('dom match')
            day = dayMatch.group('dom')
        stripMatch = stripRe.search(line)
        if stripMatch:
            url = stripMatch.group('url')
            title = stripMatch.group('title')
            strip_date = datetime.date(int(year), int(month_name_to_number(month)), int(day))
            start_date = datetime.date(2001, 10, 1)
            request_date = datetime.date(2024, 12, 16)
            request_offset = request_date - start_date
            strip_offset = strip_date - start_date
            print(f'''{year}-{month_name_to_number(month)}-{day} {strip_offset.days} {url} {title}''')

if __name__ == '__main__':
    main()
