A soundboard for terminals
##########################

The soundboard requires a very simple configuration file with a *hotkey*,
*URL*, *start position*, *length*, and optionally a *format* delimited by
commas.  The *URL* has special support for YouTube_ links where you only need
the identifier, not the full URL.

.. _Youtube: https://www.youtube.com/

Have a look at ``videos.cfg`` or the others in the ``contrib/`` folder for some
examples.  Once you have a configuration you are happy with, the soundboard
will preprocess all the videos::

  python soundboard.py --setup my_videos.cfg

Supplying a configuration file is optional, by default it will use the shipped
``videos.cfg``.  When the preprocessing stage has finished you can start the
soundboard::

  python soundboard.py my_videos.cfg

In this interactive terminal application, you have to press any one *hotkey*
and the corresponding video will start.  It can happen that some videos get
assigned a different hotkey than the one you defined:  If two entries share the
same hotkey, the later one will be automatically reassigned another free
hotkey.  If you want to disable that behaviour, supply ``--no-resolve`` to the
application.

The following programs will be run as external processes, so you need to have
them available on your system:

:Dependencies:
  - `mplayer <https://mplayerhq.hu>`_
  - `quvi <https://quvi.sourceforge.net/>`_
  - `wget <https://www.gnu.org/software/wget/>`_
