Stupid Personal Hacker News Aggregator
=======================================

So, I'm apparently weirdly OCD about some random things; this is one
of them, and _you can safely ignore it_.

I used to sometimes read `hckrnews.com` and although they try to
remember your position it doesn't always work and never works across browsers.
What I wanted was a way that would remember where I was and when I clicked a
link invalidate it and all the links _before_ it.  The only way I could think
of to do this was host it myself.  I know, it's ridiculous and I should not be
that OCD about not missing (completely unimportant) things.

Anyway, I thought it would be quick and ended up taking many more hours than I
thought.  Oh well.  It isn't even done that well.  The parsing of the feed is
stupid, it's messy, and the the decision of how long to wait is naive.


It consists of two parts:

    *  `index.cgi`, which displays the current list (only items with larger
       indexes than the current index (which is based on pubDate)) and
       updates the idx when something is clicked on.
    *  `rss_fetch.py`, a python3 script to fetch the RSS, parse it, add links
       to the list of current links and remove any that are older than the
       index and not in the current fetched items.

There are created on first fetch and store the state:

    *  `current.dict`, which is the current list of links.  It needs to
       include everything in the last rss get so the fetch time can be
       adjusted to always have some overlap.  Links are unique if the link is
       identical and the id (pubDate) is the same.  Hopefully everything is
       small enough to fit into memory.
    *  `last_clicked_idx`, is the index of the last thing you read (or clicked
       on.
    *  `lockfile`, and empty file to do locking between the two parts.


Installation
============

I've only run this on an (old) version of Apache, there is nothing that off the
wall here so should work everywhere.  All you really need to do is drop the
two files `index.cgi` and `rss_fetch.py` (or git clone the project)
into some directory and run fetch
by hand in a loop in tmux, or with cron, or whatever.  It will create the
missing files and the history of entries and start fetching from RSS.

You probably also want to put some security in there so it doesn't get fetched
by spiders and all the other bits (apart from `index.cgi`) aren't accessible
at all.  My `.htaccess` looks like:

    Options ExecCGI
    AddType application/x-httpd-cgi .cgi
    AuthUserFile /path/to/password/file
    AuthGroupFile /dev/null
    AuthName "Password Hint"
    AuthType Basic

    <Limit GET>
        require valid-user
    </Limit>

    Order Deny,Allow
    Deny from all
    <Files index.cgi>
        Allow from all
    </Files>

