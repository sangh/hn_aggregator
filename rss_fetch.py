#!/usr/bin/env python3

import fcntl, time, sys, os
import urllib.request
from email.utils import parsedate_to_datetime
import xml.parsers.expat


debug = False

pwd = os.path.dirname(os.path.realpath(sys.argv[0]))
current_dict = os.path.join(pwd, "current.dict")
idx_file = os.path.join(pwd, "last_clicked_idx")
lockfile = os.path.join(pwd, "lockfile")
if debug:
    parse_error_output_file = os.path.join(pwd, "GET_PARSE_ERROR.xml")

def calc_sleep(n_new, n_fetched, new_per):
    """Return a float number of hours to sleep based on the number of new
    items (from a total of n_fetched items download), or the percentage."""
    if False:
        # So, my fancy way of doing this wasn't really better than the
        # simple way below.
        if not hasattr(calc_sleep, "sleep_time_hours"):
            calc_sleep.sleep_time_hours = 1.5  # Starting sleep time.
        # Sleep for some amount of time using `new_perecent`.
        # Target is approximately 70 %, since if 90 % we take 1/3rd the time,
        # if 50 % we take 5/3rds the time, and scale from 1/3 to 5/3 inbetween,
        # capping if not in between.  The randdom part is just so the
        # resulting numbers are not even and we don't end up in a loop.
        # Liner scale:
        #   f(x) = C * (1 - (x - A) / (B - A)) + D * (x - A) / (B - A)
        # Which is:
        #   f(x) = x * (D - C) / (B - A) + C + A * (C - D) / (B - A)
        # So for (A, B) -> (C, D)  =  (50, 90) -> (5/3, 1/3)
        #   f(x) = 3.33333333 - 0.03333333 * x
        new_per = 3.33333333 - 0.03333333 * new_per
        if new_per > 1.7:
            new_per = 1.7
        elif new_per < 0.3:
            new_per = 0.3
        # Plus something between -0.128 and 0.127.
        new_per = new_per  + float(ord(os.urandom(1)) - 128) / 1000
        calc_sleep.sleep_time_hours = calc_sleep.sleep_time_hours * new_per
        return calc_sleep.sleep_time_hours
    else:
        # This is 5.8 + rand(-1.28, 1.27).
        max_sleep_time = 5.8 + float(ord(os.urandom(1)) - 128) / 100
        return float(n_fetched - n_new) * max_sleep_time / float(n_fetched)

    # If we get here, the big if didn't return anything.
    return 1.5  # Hours.


# If none of current dict, the idx or lock file exist, create them.
if not tuple(filter(os.path.exists, (current_dict, idx_file, lockfile))):
    lock = open(lockfile, "a")  # Will create if it doesn't exist.
    fcntl.flock(lock, fcntl.LOCK_EX)

    # We use append so that we don't clobber data if this is accidentally
    # called even though the result is that someone has to manually fix it.
    with open(idx_file, "a") as f:
        f.write("0.0")

    with open(current_dict, "a") as f:
        f.write('{}')

    fcntl.flock(lock, fcntl.LOCK_UN)
    lock.close()


def prn(s):
    print("%s:  %s" % (time.strftime("%Y-%m-%d %H:%M:%S"), s))

def dbg(s):
    global debug
    if(debug):
        prn(s)

def rss_fetch():
    """This function fetches the new items, returning it."""
    items = {}

    def add_item(pubDate, title, link):
        nonlocal items
        idx = float(parsedate_to_datetime(pubDate).timestamp())
        while idx in items:
            idx = idx + 0.1
        dbg("Adding item:  %11.1f \"%s\" %s" % (idx, title, link))
        items[idx] = {}
        items[idx]['title'] = title
        items[idx]['link'] = link

    state = ""  # state parser is in ("", "item", "title", "link", "pubDate")
    title = ""  # Currently parsing this title.
    link = ""  # " " " link
    pubDate = ""  # " " " pubDate (index)

    def start_element(name, attrs):
        nonlocal state
        nonlocal title
        nonlocal link
        nonlocal pubDate
        dbg("Start: %s %s  %s" %(name, str(attrs), str((state, title, link, pubDate))))
        if state == "":
            if name == "item":
                state = "item"
        elif state == "item":
            if name == "title":
                state = "title"
                if title:
                    prn("Two titles?")
                    sys.exit(1)
            elif name == "link":
                state = "link"
                if link:
                    prn("Two links?")
                    sys.exit(1)
            elif name == "pubDate":
                state = "pubDate"
                if pubDate:
                    prn("Two pubDates?")
                    sys.exit(1)


    def end_element(name):
        nonlocal state
        nonlocal title
        nonlocal pubDate
        nonlocal link
        dbg("End: %s  %s" % (name, str((state, title, link, pubDate))))
        if state == "item":
            if name == "item":
                if title == "":
                    prn("No title at end item.")
                    sys.exit(1)
                if link == "":
                    prn("No link at end item.")
                    sys.exit(1)
                if pubDate == "":
                    prn("No pubDate at end item.")
                    sys.exit(1)
                else:
                    add_item(pubDate, title, link)
                state = ""
                title = ""
                link = ""
                pubDate = ""
        elif state == "title":
            if name == "title":
                state = "item"
        elif state == "link":
            if name == "link":
                state = "item"
        elif state == "pubDate":
            if name == "pubDate":
                state = "item"

    def char_data(data):
        nonlocal state
        nonlocal title
        nonlocal pubDate
        nonlocal link
        dbg("Data: %s  %s)" % (str(data), str((state, title, link, pubDate))))
        if state == "title":
            title = title + data
        elif state == "link":
            link = link + data
        elif state == "pubDate":
            pubDate = pubDate + data


    p = xml.parsers.expat.ParserCreate("UTF-8")

    p.StartElementHandler = start_element
    p.EndElementHandler = end_element
    p.CharacterDataHandler = char_data

    with urllib.request.urlopen('https://news.ycombinator.com/rss') as f:
        xml_file = b""
        while True:
            r = f.read(255)
            if r:
                xml_file = xml_file + r
            else:
                break

        try:
            p.Parse(xml_file.decode("UTF-8"), True)
        except:
            dbg("Writing fetched RSS feed to file...")
            err_f = open(parse_error_output_file, "ab")
            err_f.write(b"GET URL: ")
            err_f.write(f.geturl().encode("UTF-8"))
            err_f.write(b"\nReturn Code: ")
            err_f.write(("%d\n" % (f.getcode(), )).encode("UTF-8"))
            err_f.write(b"Meta Info:\n")
            err_f.write(f.info().as_bytes(unixfrom=True))
            err_f.write(b"XML output:\n")
            err_f.write(xml_file)
            err_f.close()
            dbg("Done.")
            raise

    return items


while True:
    prn("Starting fetch...")
    fetched_items = rss_fetch()

    # First we open all the files, pull in the current_dict and current idx.
    lock = open(lockfile)
    fcntl.flock(lock, fcntl.LOCK_EX)

    f = open(current_dict, encoding='UTF-8')
    current_items = eval(f.read())
    f.close()

    f = open(idx_file, encoding='UTF-8')
    current_idx = float(f.read())
    f.close()


    links_set = set()
    for idx in current_items:
        links_set.add(current_items[idx]['link'])

    new_items = {}

    for idx in fetched_items:
        if not fetched_items[idx]['link'] in links_set:
            if idx > current_idx:
                new_items[idx] = fetched_items[idx]
            else:
                new_idx = current_idx + 0.1
                while new_idx in new_items:
                    new_idx = new_idx + 0.1
                new_items[new_idx] = fetched_items[idx]

    num_new_items = len(new_items)
    num_fetched_items = len(fetched_items)
    new_percent = 100.0 * (float(num_new_items) / float(num_fetched_items))
    prn("Done, %d of %d new items (%3.1f %%)." % (num_new_items, num_fetched_items, new_percent))

    # So now we want to write out the new file.  We take the current and new sets
    # and write out everything unless the link is NOT found in fetched AND is less
    # than or equal to the current idx.

    # Reuse links_set to be the set in fetched_items.
    links_set.clear()
    for idx in fetched_items:
        links_set.add(fetched_items[idx]['link'])

    write_out_items = {}
    for idx in current_items:
        if current_items[idx]['link'] in links_set:
            write_out_items[idx] = current_items[idx]
        elif idx > current_idx:
            write_out_items[idx] = current_items[idx]
    for idx in new_items:
        write_out_items[idx] = new_items[idx]

    f = open(current_dict, "w", encoding='UTF-8')
    f.write(str(write_out_items))
    f.close()

    # Unlock, finally!
    fcntl.flock(lock, fcntl.LOCK_UN)
    lock.close()


    # Clear all variables.
    links_set = set()
    new_items = {}
    current_items = {}
    current_idx = None
    write_out_items = {}
    fetched_items = {}

    sleep_hours = calc_sleep(num_new_items, num_fetched_items, new_percent)
    prn("Sleeping for %.2f hours." % (sleep_hours, ))
    time.sleep(60 * 60 * sleep_hours)
