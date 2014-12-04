import csv
import itertools
import os
import subprocess
import sys
import termios
import tty

CONFIG_FILE = 'videos.cfg'
YOUTUBE = 'http://www.youtube.com/watch?v=%s'


def read(path):
    with open(path) as f:
        lines = itertools.chain(["key,uri,title,start,length,format"], f)
        reader = csv.DictReader(lines)
        return dict((line['key'], line) for line in reader)


def setup(videos):
    try:
        os.makedirs('cache')
    except OSError:
        pass

    for video in videos.values():
        cmd = ['quvi', YOUTUBE % video['uri'],
                '--exec', 'wget %%u -O cache/%s' % video['uri']]
        if video['format']:
            cmd.extend(['--format', video['format']])
        subprocess.call(cmd)


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
                subprocess.call(['mplayer', '-fs', 'cache/%s' % video['uri'],
                        '-ss', video['start'], '-endpos', video['length']],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    finally:
        tty.setcbreak(fd)
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def main(args):
    videos = read(CONFIG_FILE)

    for video in videos.values():
        print "%s:  %s" % (video['key'], video['title'])

    if args == ['setup']:
        setup(videos)
    else:
        loop(videos)


if __name__ == '__main__':
    main(sys.argv[1:])