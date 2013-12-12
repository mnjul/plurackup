### Moved from [Google Code](https://code.google.com/p/plurackup/)

Notice
======

**Plurk has released its own backup function (for those with Karma > 50 and registered for over 90 days). Its results are pretty neat but  the whole backup process seems to take quite long (it took about a day for the backup of my nearly-3000 plurks to deliver to my mailbox; this plurackup tool takes just a few minutes).**

Introduction
============

This is a plurk backup tool written in python, which backups all your
plurks. The tool is multi-threaded with several threads to download
plurks and responses simultaneously, speeding up the backup process.

This tool is intended _for personal use_. You need your login
credentials to backup your plurks. Also, only plurks by you will be
backed-up; those from your friends and whom you follow will not be
backed-up.

The project incorporates the [plurklib](http://code.google.com/p/plurklib/) library. It is both python 2
and python 3-compatible (python 2.7 recommended).

Quick Guide
===========

Preparation
-----------

* **You need your own Plurk API key** to use this tool. Get yours at [Plurk's official API page](http://www.plurk.com/API/1.0/#key).
* Insert your Plurk API key in [plurackup.py](https://github.com/mnjul/plurackup/blob/master/plurackup.py)'s `_apiKey` variable. Alternatively, input your Plurk API key after you run the script. 

Usage
-----

* Run the python script: `python plurackup.py` 
* Select output format by inputting:
   * `X` for XML, which stores content_raw, without any emoticons or thumbnails for videos, is suitable for further parsing, and is not very human-readable.
   * `H` for HTML, which stores human-readable contents, with emoticons and thumbnails for videos. Links are `<a>`-tagged too.
   * `B` for both formats.
* Input timezone offset for HTML format:
   * If you select the HTML output format, a timezone offset can be applied to the fetched timestamps. Plurk server stores timestamps in UTC.
   * This backup tool tries to automatically determine a correct timezone offset, but you may override the default value.`\
   * Format is `±hh:mm`, and acceptable values go like: `8:00`, `+3:30`, `-1:15`
* Enter the output filename
   * .xml and/or .html will be appended. Just press enter if you wish to use your plurk username as the filename.
   * _Existing files will be overwritten_
* Type in your login credentials. Your password will not be shown on the screen; your login credentials will be sent through HTTPS encrypted.
* Backup progress will be indicated. After fetching, your complete plurk backup will be saved in the filename indicated .

Notes
=====

* As always, I appreciate your using this tool and any feedback is welcomed.
* A stylesheet file will be needed for the HTML format to facilitate pretty output. A default style.css is included in this project package; the content of the stylesheet will be copied into the output HTML during the back-up process and is not needed for final browsing.
* You can also specify your own CSS file in [plurackup.py](https://github.com/mnjul/plurackup/blob/master/plurackup.py).

* I wish to provide GUI frontend in the future.
