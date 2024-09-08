import datetime
from feed import FeedIndexReader, FeedGenerator
import os
import pytest
import textwrap

def test_FeedIndexReader():
    # yyyy-mm-dd {days-since-start} {url} {title...}
    data = textwrap.dedent('''\
    2001-10-1 0 https://achewood.com/2001/10/01/title.html Philippe is standing on it
    2001-10-2 1 https://achewood.com/2001/10/02/title.html Téodor's birthday presents
    2001-10-3 2 https://achewood.com/2001/10/03/title.html The new catalog has arrived
    2001-10-4 3 https://achewood.com/2001/10/04/title.html Who ate my 'shrooms?
    2001-10-5 4 https://achewood.com/2001/10/05/title.html A call to Modemtown
    2001-10-8 7 https://achewood.com/2001/10/08/title.html Someone is at the door''')
    reader = FeedIndexReader(data.split('\n'))
    posts = reader.posts
    assert len(posts) == 6, "six items"
    assert datetime.datetime.strftime(posts[0].publish_datetime, '%Y-%m-%d') == '2001-10-01', "correct date parsing"
    assert posts[1].title == '''Téodor's birthday presents'''
    assert posts[2].url == '''https://achewood.com/2001/10/03/title.html'''


def test_FeedGeneratorFirstDay(monkeypatch):
    monkeypatch.setenv('QUERY_STRING', 'startAsOfDate=2024-09-07&__dateOverride=2024-09-07')
    gen = FeedGenerator()
    assert len(gen.feed_posts) == 1


def test_FeedGeneratorSecondDay(monkeypatch):
    monkeypatch.setenv('QUERY_STRING', 'startAsOfDate=2024-09-07&__dateOverride=2024-09-08')
    gen = FeedGenerator()
    assert len(gen.feed_posts) == 2


def test_FeedGeneratorFourthDay(monkeypatch):
    monkeypatch.setenv('QUERY_STRING', 'startAsOfDate=2024-08-01&__dateOverride=2024-08-04')
    gen = FeedGenerator()
    assert len(gen.feed_posts) == 4

