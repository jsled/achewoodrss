PHONY: test publish

hostname = water

test:
	. v-$(hostname)-test/bin/activate && python3 -m pytest

publish:
	scp feed.py jsled@asynchronous.org:asynchronous.org/feeds/achewood.py
