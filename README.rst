.. contents:: Table of Contents


Steam-Idle (OSX)
================

A small package to idle steam games for card drops.

Based on `SteamIdleMaster <https://github.com/jshackles/idle_master>`_.
This package has been optimised for usage on OSX, it only includes the python source
files and no longer contains the code for idling on windows.

Installation
============

To install this package on your machine simply run the following steps:

.. code:: bash

    $ git clone git@github.com:raphael-s/steam.idle.git
    $ cd steam.idle
    $ virtualenv-2.7 .
    $ source bin/activate
    $ pip install requests colorama BeautifulSoup4

You dont have to run `source bin/activate` everytime you want to use the idler, the start
script will already do that for you.

Usage
=====

To start idling, you first have to edit the ``settings.txt`` file.
In the file you have to set the values for ``sessionid`` and ``steamLogin``.
To get those values, you have to open a session on `SteamCommunity <http://steamcommunity.com/>`_.
After you signed into your account, you can get those two values from the cookies of the page.

Important:
You have to replace ``%7C%7C`` in the value for ``steamLogin`` with ``||``.

Before you can start idling, you have to run the Steam app on your machine.

If all those steps have been done, you can start to idle by simply running ``./idle``.
