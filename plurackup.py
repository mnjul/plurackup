"""
    Copyright (c) 2011-2013 Mnjul/purincess (Min-Zhong Lu)
    With plurklib from Kurt Karakurt (http://code.google.com/p/plurklib/)

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
    THE SOFTWARE.
"""
from __future__ import print_function

# Please use your own API key retrieved from http://www.plurk.com/API/1.0/#key
_apiKey = ''

# If you wish to use your own CSS file for HTML outputs, specify the file here
# Default is style.css
cssFilename = ''

# Set up "how many plurks should each request to server return?"
# This affects parallelism of this script (the larger the value, the more parallelism). The author hasn't tried any value > 50.
plurksPerRequest = 50



"""
"""
"""
"""

import re
import time
import getpass

import plurackuplib

# raw_input became input in python3, but python2 actually had input on its own..
if "raw_input" in vars(__builtins__):
    input = raw_input

def _outLog(message):
    print(message)

def _quesAsk(question):
    return input(question)

print("""========================================
plurackup Plurk Backup Tool.
----------------------------------------
- Please note: this backup tool will backup only your plurks and their responses, and not plurks by your friends or those who you follow.
=========================================""")

if _apiKey == "":
    _apiKey = input("Plurk API Key is undefined. Please input your API key retrieved from http://www.plurk.com/API/1.0/#key :")
    print("========================================")

print("OUTPUT FORMAT")
print("----------------------------------------")
print("- There are two output formats available.")
print("-- The XML format stores raw_content plurks and respopnses, and is suitable for further parsing but not very human-readable.")
print("-- The HTML format is suitable for immediate browsing without further parsing.")
print("----------------------------------------")
formatRaw = input("- Please select your output format. X for XML, H for HTML, and B for both.\n- Default is [H]TML: ")
formatRaw = formatRaw[:1].upper()

xmlOutput = False
htmlOutput = False

if formatRaw == "X" or formatRaw == "B":
    xmlOutput = True
if formatRaw == "H" or formatRaw == "B":
    htmlOutput = True
    
if not xmlOutput and not htmlOutput:
    htmlOutput = True

print("========================================")

zoneOffsetHour = 0
zoneOffsetMin = 0
zoneOffsetSign = 0

if htmlOutput:
    if time.localtime().tm_isdst and time.daylight:
        zoneOffsetMin = -time.altzone / 60
    else:
        zoneOffsetMin = -time.timezone / 60
    
    zoneOffsetHour = int(zoneOffsetMin / 60)
    zoneOffsetMin = zoneOffsetMin % 60
    zoneOffsetSign = 1 if zoneOffsetHour >= 0 else -1
    zoneOffsetHour = zoneOffsetHour * zoneOffsetSign

    print("TIMEZONE SETTING")
    print("----------------------------------------")
    print("- For HTML output, you can specify a timezone offset to be applied to the timestamps returned from Plurk server (which is UTC)")
    print("- According to your computer's configuration, the offset by default is: " + ("+" if zoneOffsetSign == 1 else "-") + str(zoneOffsetHour) + ":" + "%02d" % zoneOffsetMin)
    # plus minus sign in utf-8 is 0xc2b1 (c2 being control code, b1 is actual sign)
    # python2's raw_input is not happy with non-ascii prompt so...
    print(b"- Please input your desired timezone offset if you wish to override the default (format: \xc2\xb1hh:mm): ".decode("utf-8"), end="")
    timezoneRaw = input("")
    timezoneMatch = re.match(r"([+-]?)(\d\d?)(:(\d\d?))?", timezoneRaw)
    if timezoneMatch != None:
        zoneOffsetSign = -1 if timezoneMatch.group(1) == "-" else 1
        zoneOffsetHour = int(timezoneMatch.group(2), 10)
        zoneOffsetMin = int(timezoneMatch.group(4), 10)
        
    print("========================================")


print("OUTPUT FILENAME")
print("----------------------------------------")

outFilename = input("- The default output filename is your plurk username. *Existing files will be overwritten*\n- Enter output filename if you wish to override the default; .xml and/or .html will be appended: ")

print("========================================")
print("LOGIN CREDENTIALS")
print("----------------------------------------")

backupAgent = plurackuplib.BackupAgent(_apiKey, _outLog, _quesAsk, outFilename, xmlOutput, htmlOutput, zoneOffsetSign, zoneOffsetHour, zoneOffsetMin, cssFilename, plurksPerRequest)

print("- Please have your login credentials ready. Your username and password will be sent through HTTPS (encrypted).")

print("----------------------------------------")

username = input("Your plurk username: ")
password = getpass.getpass("Your plurk password: ")

print("========================================")

backupAgent.doBackup(username, password)

_apiKey = ""
backAgent = None
username = ""
password = ""
