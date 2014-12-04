# encoding: utf-8
import csv
import fcntl
import math
import optparse
import os
import subprocess
import struct
import sys
import termios
import tty
try:
    from urllib.parse import quote_plus
except ImportError:
    from urllib import quote_plus


CONFIG_FILE = 'videos.cfg'
SOUND_SUFFIXES = ['wav', 'mp3', 'ogg']
CACHE_DIR = 'cache'
YOUTUBE = 'http://www.youtube.com/watch?v=%s'
HERE = os.path.dirname(os.path.abspath(__file__))


def read(path):
    cfg = {}
    with open(path) as f:
        reader = csv.DictReader(f,
                 fieldnames='key,loc,title,start,length,format'.split(','))
        for line in reader:
            if line['key'].startswith('#'):
                continue
            if line['key'] in cfg:
                raise ValueError("duplicate hotkey `%s' in line %d" %
                        (line['key'], reader.line_num))
            loc = line['loc']
            line['uri'] = uri = loc if '.' in loc else YOUTUBE % loc
            line['title'] = line['title'].decode('utf-8')
            # By happy coincidence, quote_plus cannot contain any of quvi's
            # --exec specifiers (%u, %t, %e, and %h.  Instead of %eX it uses
            # %EX.)  Let's hope `HERE` does not contain any as well.
            line['path'] = os.path.join(HERE, CACHE_DIR, quote_plus(uri))
            cfg[line['key']] = line
    return cfg


def setup(videos):
    try:
        os.makedirs(os.path.join(HERE, CACHE_DIR))
    except OSError:
        pass

    for video in videos.values():
        if os.path.exists(video['path']):
            continue
        cmd = ['quvi', '--feature', '-verify', video['uri'],
               '--exec', 'wget %%u -O %s' % video['path']]
        if video['format']:
            cmd.extend(['--format', video['format']])
        ret = subprocess.call(cmd)
        if ret == 0x41:  # QUVI_NOSUPPORT, libquvi does not support the host
            # Maybe we can just download the bare resource.
            subprocess.call(['wget', video['uri'], '-O', video['path']])


def loop(videos):
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    tty.setraw(fd)

    try:
        while 1:
            ch = sys.stdin.read(1)
            if ch == '\x03':  # Ctrl-C
                break
            if ch in videos:
                video = videos[ch]
                play(video)
    finally:
        tty.setcbreak(fd)
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def play(video):
    cmd = ['mplayer', '-fs', video['path']]
    if video['start']:
        cmd.extend(['-ss', video['start']])
    if video['length']:
        cmd.extend(['-endpos', video['length']])
    subprocess.call(cmd,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def usage(videos):
    """
    ┏━━━┱──────────────┐
    ┃ x ┃ First title  │
    ┃ y ┃ Second title │
    ┗━━━┹──────────────┘

    """
    # $COLUMNS
    width, = struct.unpack('xxh', fcntl.ioctl(0, termios.TIOCGWINSZ, '0000'))

    # Sort by title length so subsequent columns are guaranteed to have the
    # longest item at their very top.
    out = videos.values()
    out.sort(key=lambda v: len(v['title']), reverse=True)
    total = len(out)

    # Responsive design for terminals, fuckyeah
    for cols in range(total, 0, -1):
        # First, and longest, item of the `i`th column.
        column = lambda i: int(math.ceil(float(i) * total / cols))
        rows = column(1)
        pads = [len(out[column(i)]['title']) for i in xrange(cols)]

        # The number of columns is too damn high.
        # Some columns are empty and can still be removed.
        if rows * cols - total >= rows:
            continue

        realw = sum(pads) + len(u"┏━━━┱──┐ ") * cols
        if realw < width:
            break

    # Header
    for j in xrange(cols):
        print u"┏━━━┱─" + u"─"*pads[j] + u"─┐",
    print

    # Body
    for i in xrange(rows):
        for j in xrange(cols):
            try:
                video = out[j * rows + i]
            except IndexError:
                video = dict(key=' ', title='', loc='')
            is_sound = any(video['loc'].endswith('.' + suf)
                           for suf in SOUND_SUFFIXES)
            print u"┃ %s ┃%s%-*s │" % (
                    video['key'], ' ~'[is_sound], pads[j], video['title']),
        print

    # Footer
    for j in xrange(cols):
        print u"┗━━━┹─" + u"─"*pads[j] + u"─┘",
    print


def main(argv):
    parser = optparse.OptionParser()
    parser.add_option('-s', '--setup',
            action='store_true', dest='setup', default=False,
            help="download all video files")
    parser.add_option('-k', '--key',
            help="only play a single video")
    options, args = parser.parse_args(argv)

    videos = read(args[0] if args else os.path.join(HERE, CONFIG_FILE))

    if options.key:
        play(videos[options.key])
    elif options.setup:
        setup(videos)
    else:
        usage(videos)
        loop(videos)


if __name__ == '__main__':
    main(sys.argv[1:])
