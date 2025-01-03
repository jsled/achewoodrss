#!/home/jsled/asynchronous.org/feeds/v-achewood/bin/python3

from dataclasses import dataclass
import datetime
from enum import Enum
from feedgen.feed import FeedGenerator as AtomGenerator
import logging
import os
import textwrap
import time
from urllib.parse import urlparse, parse_qs

# TODO: add "days-since-original" and "percentage" to the feed body

'''
License: MIT

return one of either:

- an html page describing the parameters allowable to create a feed url
- a feed, based on those parameters

- parameters
  - startAsOfDate: the epoch date at which /this/ feed starts; the first post of the original feed will be published as-of this date, and all subsequent posts will index off that epoch
  - pace:
    - =original: the original feed will be published on the same schedule as it was originally published ... if there's a 2-week break in the feed, this feed won't update for 2 weeks
    - =daily: the original feed will be published every day, no matter what the original schedule on which it was published.
  - width: the number of feed items to return; defaults to 20
  - __dateOverride: [DEBUG] don't use the current time, instead use the defined dateOverride for logic
'''

@dataclass
class FeedPost:
    url: str # url lib?
    # postId: str # later
    publish_datetime: datetime.datetime
    title: str
    # body: str


class FeedIndexReader:
    # FIXME: "-> Iterable[str]"?
    def __init__(self, line_iterable):
        # TODO: should would be nice to have linenumbers and such
        self._posts = [self._parse_line(line) for line in line_iterable]

    def _parse_line(self, line:str) -> FeedPost:
        parts = line.split(' ')
        (date_str, offset_str, url_str, title) = (parts[0], parts[1], parts[2], ' '.join(parts[3:]))
        # date = datetime.datetime.strptime('1985-04-12T23:20:50.52', '%Y-%m-%dT%H:%M:%S.%f')
        publish_datetime = datetime.datetime.strptime(date_str, '%Y-%m-%d')
        post = FeedPost(url_str, publish_datetime, title)
        return post

    @property
    def posts(self):
        return self._posts

# if ?? no arguments:
#   return html page / form
#

# validate params/formats?

# origFeed <- load(...)
# feedAsOfDate <- _dateOverride or time.now()
# feedDaysSinceStart <- feedAsOfDate - startAsOfDate ... coerce to days
# feedDateAfterOriginal <- origFeed[0].pubishDate + feedDaysSinceStart

# latestIndex <- {
#   if pace == "original": find the index of the first post /after/ feedAsOfDate {
#      return origFeed.indexOf( lambda p: p.postDate > feedDateAfterOriginal )
#   }
#   elif pace==daily: directly index based on the number of days in feedAsOfDate {
#      return feedDaysSinceStart
#   }
# }

# lower_bound = max(0, (latestIndex - width)) # + 1?
# upper_bound = latestIndex

# current_feed <- slice origFeed[lower_bound:upper_bound]

# render(current_feed)

@dataclass
class FormatMixin:
    format_str: str

class Format (FormatMixin, Enum):
    rfc3339 = '%Y-%m-%d'


@dataclass
class PaceMixin:
    label: str

class Pace (PaceMixin, Enum):
    original = 'original'
    daily = 'daily'


@dataclass
class ParamMixin:
    param_name: str

class Params (ParamMixin, Enum):
    start_as_of_date = 'startAsOfDate'
    date_override = '__dateOverride'
    pace = 'pace' # values = Pace enum values


class CgiSupport:
    def __init__(self):
        pass

    def exists(self, param_name:str):
        try:
            query_params = parse_qs(os.environ['QUERY_STRING'])
            logging.debug(f'keys: {query_params.keys()=}')
            return param_name in query_params.keys()
        except KeyError as no_such_key:
            return False

    def get(self, param_name:str):
        query_params = parse_qs(os.environ['QUERY_STRING'])
        return query_params[param_name][0]

cgi = CgiSupport()


class FeedGenerator:
    def __init__(self):
        with open('achewood.index', 'r') as f:
            reader = FeedIndexReader([l.strip() for l in f.readlines()])
            self._posts = reader.posts
        if not cgi.exists(Params.start_as_of_date.param_name):
            raise Exception('400: no start_as_of_date param')

        # FIXME
        self._width = 10

        start_as_of_date_param_str = cgi.get(Params.start_as_of_date.param_name)
        self._feedAsOfDate = datetime.datetime.now()
        self._startAsOfDate = datetime.datetime.strptime(start_as_of_date_param_str, Format.rfc3339.format_str)
        logging.debug(f'''test stdout {os.environ['QUERY_STRING']} {Params.date_override.param_name}''')
        if cgi.exists(Params.date_override.param_name):
            override_param_str = cgi.get(Params.date_override.param_name)
            self._feedAsOfDate = datetime.datetime.strptime(override_param_str, Format.rfc3339.format_str)
            logging.debug(f'''date_override: {self._feedAsOfDate=}''')
        # "today", but 23:59:59
        self._feedAsOfDate = self._feedAsOfDate.replace(hour=23, minute=59, second=59)
        logging.debug(f'''{self._feedAsOfDate=} {self._startAsOfDate=}''')
        self._feedDaysSinceStartDelta = self._feedAsOfDate - self._startAsOfDate
        self._feedDateAfterOriginal = self._posts[0].publish_datetime + self._feedDaysSinceStartDelta
        pace = Pace.original.value
        if cgi.exists(Params.pace.param_name):
            pace = Pace[cgi.get(Params.pace.param_name)]
        upper_bound = 0
        if pace == Pace.original.value:
            index_after = [i for i,p in enumerate(self._posts) if p.publish_datetime >= self._feedDateAfterOriginal][0]
            real_index = index_after - 1
            upper_bound = real_index
            pass
        elif pace == Pace.daily.value:
            upper_bound = self._feedDaysSinceStartDelta.days
        lower_bound = max(0, upper_bound - self._width)
        upper_bound = upper_bound + 1
        self._feed_posts = self._posts[lower_bound:upper_bound]

    @property
    def feed_posts(self):
        return self._feed_posts

    @property
    def atom(self):
        assert self._feed_posts
        gen = AtomGenerator()
        gen.id('https://achewood.com/')
        gen.title('Achewood, Replayed')
        gen.author({'name': 'Chris Onstad'})
        gen.link(href='https://achewood.com/')
        for post in self._feed_posts:
            entry = gen.add_entry()
            entry.id(post.url)
            entry.title(post.title)
            entry.link(href=post.url)
            # entry.pubDate(post.publish_datetime)
        s = gen.atom_str(pretty=True)
        return s.decode('utf-8')


    def go(self):
        print('Content-Type: application/atom+xml\n\n')
        print(self.atom)


def config_logging():
    logging.basicConfig(format='{asctime} {levelname:>7}: {msg}', style='{', level=logging.INFO, datefmt='%Y-%m-%dT%H:%M:%S')
    logging.Formatter.converter = time.gmtime
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    logging.getLogger('').addHandler(ch)

if __name__ == '__main__':
    config_logging()
    if not cgi.exists(Params.start_as_of_date.param_name):
        now_str = datetime.datetime.now().strftime('%Y-%m-%d')
        print('Content-Type: text/html\n\n')
        print(textwrap.dedent(f'''\
        <html>
        <body>
        <h1>Achewood, Replayed</h1>
        <form method=GET>
           Start As Of Date: <input name="startAsOfDate" value="{now_str}"/><br/>
           Pace: <select name="pace"><br/>
             <option value="{Pace.original.value}">Original Pacing: include pauses and gaps in the original feed; replay it as originally posted.</option>
             <option value="{Pace.daily.value}">Daily Pacing: ignore all pauses and gaps in the original feed; every day a new post.</option>
           </select><br/>
           <input type=submit value="create that feed!"/>
        </form>


        <hr/>

        made with &hearts; by <a href="https://asynchronous.org/">jsled</a> | <a href="https://github.com/jsled/achewoodrss">github.com/jsled/achewoodrss</a>
        </body>
        </html>'''))
    else:
        FeedGenerator().go()
