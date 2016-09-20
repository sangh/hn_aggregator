#!/usr/bin/env python3.4

from email.utils import parsedate_to_datetime
import fcntl, sys, time, html, cgi, os

#import cgitb
#cgitb.enable()

pwd = os.path.dirname(os.path.realpath(sys.argv[0]))
current_dict = os.path.join(pwd, "current.dict")
idx_file = os.path.join(pwd, "last_clicked_idx")
lockfile = os.path.join(pwd, "lockfile")


def p(l):
    """Print one line to stdout for CGI, can't use `print()` b/c it tries to
    figure out the console's encoding and use that."""
    sys.stdout.buffer.write(l.encode('UTF-8') + b'\n')

p('Content-Type: text/html; charset=UTF-8')
p('')


idx = None
try:
    idxs = cgi.FieldStorage().getlist("idx")
    if 1 == len(idxs):
        idx = float(idxs[0])
except:
    pass

if idx:
    lock = open(lockfile)
    fcntl.flock(lock, fcntl.LOCK_EX)
    f = open(idx_file, "w")
    f.write("%f" % (idx, ))
    f.close()
    fcntl.flock(lock, fcntl.LOCK_UN)
    lock.close()

else:
    lock = open(lockfile)
    fcntl.flock(lock, fcntl.LOCK_EX)

    f = open(current_dict, encoding='UTF-8')
    items = eval(f.read())
    f.close()

    f = open(idx_file, encoding='UTF-8')
    idx = float(f.read())
    f.close()

    fcntl.flock(lock, fcntl.LOCK_UN)
    lock.close()

    p('<!DOCTYPE html>')
    p('<html>')
    p('<meta http-equiv="content-type" content="text/html; charset=UTF-8"/>')
    p('<head>')
    p('  <title>hn links</title>')
    p('  <style>')
    p('    body {')
    p('      line-height: 1.5;')
    p('      font-size: 16.2px;')
    p('      font-family: ' + "'" + 'Times New Roman' + "',serif;")
    p('    }')
    p('    .link_display {')
    p('      font-size: 10px;')
    p('      color: LightGrey;')
    p('    }')
    p('    .idx {')
    p('      font-size: 10px;')
    p('      color: LightGrey;')
    p('      margin-left: 50px;')
    p('      margin-right: 10px;')
    p('    }')
    p('    a {')
    p('      color: Black;')
    p('    }')
    p('    a.old {')
    p('      color: LightGrey;')
    p('    }')
    p('    script {')
    p('      display: none;')
    p('    }')
    p('  </style>')
    p('  <script type="text/javascript">')
    p('    var current_idx = %f;' % (idx, ))
    p('    onclickfunc = function(idx) {')
    p('      var xmlHttp = new XMLHttpRequest();')
    p('      xmlHttp.open("GET", "?idx=" + idx, true);')
    p('      xmlHttp.send(null);')
    p('      current_idx = parseFloat(idx);')
    p('      var atags = document.getElementsByClassName("link");')
    p('      var i;')
    p('      for (i = 0; i < atags.length; i++) {')
    p('        var idx = parseFloat(atags[i].id);')
    p('        if (current_idx >= idx) {')
    p('          atags[i].classList.add("old");  // Will dedup.')
    p('        }')
    p('      }')
    p('    }')
    p('  </script>')
    p('</head>')
    p('<body>')

    for i in sorted(items.keys()):
        if i > idx:
            link = html.escape(items[i]['link'], True)
            title = html.escape(items[i]['title'], False)
            p('  <span class="idx">%11.2f (%s)</span>' % (
                i,
                time.strftime("%c", time.localtime(i)),
            ))
            p('  <a id="%11.2f" class="link" onclick="onclickfunc(this.id)" href="%s">' % (i, link, ))
            p('    %s' % (title, ))
            p('  </a><span class="link_display">(%s)</span><br/>' % (link, ))

    p('</body>')
    p('</html>')
