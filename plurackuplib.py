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

import cgi
import copy
import datetime
import re
import threading
import codecs

import plurklib

class PlurackupLibError(Exception):
    def __init__(self, value):
        self._value = value
        
    def __str__(self):
        return repr(self.value)
        

class _FileFrontInterface:
    def __init__(self):
        raise NotImplementedError("_FileFrontInterface is an interface.")
        
    def prepare(self):
        raise NotImplementedError("_FileFrontInterface is an interface.")

    def postpare(self):
        raise NotImplementedError("_FileFrontInterface is an interface.")
        
    def writePlurks(self, plurks, people):
        raise NotImplementedError("_FileFrontInterface is an interface.")


class _MultipleFileFront(_FileFrontInterface):
    def __init__(self):
        self._fileFronts = set()
        
    def attachFileFront(self, fileFront):
        self._fileFronts.add(fileFront)
    
    def prepare(self):
        for fileFront in self._fileFronts:
            fileFront.prepare()

    def postpare(self):
        for fileFront in self._fileFronts:
            fileFront.postpare()
        
    def writePlurks(self, plurks, people):
        for fileFront in self._fileFronts:
            fileFront.writePlurks(plurks, people)
            
        
class _XMLFileFront(_FileFrontInterface):
    """
        <plurk id="" posted_time="" lang="">
            <qualifier>CDATA</qualifier>
            <qualifier_translated>CDATA</qualifier_translated>
            <content_raw>CDATA</content_raw>
            <responses>
                <response id="" posted_time="UTC_TIME" lang="" username="" displayname="">
                    <qualifier>CDATA</qualifier>
                    <qualifier_translated>CDATA</qualifier_translated>
                    <content_raw>CDATA</content_raw>
                </response>
            </responses>
            <favorers>
                <favorer username="" displayname="" <!-- OR unknown_user="unknown_user" --> />
            </favorers>
            <replurkers>
                <replurker username="" displayname="" <!-- OR unknown_user="unknown_user" --> />
            </replurkers>
            <limited_tos>
                <friends />
                <!-- OR -->
                <limited_to username="" displayname="" <!-- OR unknown_user="unknown_user" --> />
            </limited_tos>
        </plurk>
    """    
    def __init__(self, filename):
        self._filename = filename
        self._outfile = None
        
    def prepare(self):
        self._outfile = codecs.open(self._filename + ".xml", "w", "utf-8")
        self._outfile.write('<?xml version="1.0" encoding="utf-8"?>\n')
        self._outfile.write('<plurks>\n')
        
    def writePlurks(self, plurks, people):
        # since there is no xml manipulation, let's output the file plain-text-ly, and not using any dom modules
        for plurk in plurks:
            self._outfile.write('\t<plurk id="{0}" posted_time="{1}" lang="{2}" favorite_count="{3}" replurkers_count="{4}">\n'.format(str(plurk["plurk_id"]), plurk["posted_time"], plurk["lang"], plurk["favorite_count"], plurk["replurkers_count"]))
            self._outfile.write((b'\t\t<qualifier>' + cgi.escape(plurk["qualifier"]).encode("utf-8") + b'</qualifier>\n').decode("utf-8"))
            self._outfile.write((b'\t\t<qualifier_translated>' + cgi.escape(plurk["qualifier_translated"]).encode("utf-8") + b'</qualifier_translated>\n').decode("utf-8"))
            self._outfile.write((b'\t\t<content_raw><![CDATA[' + plurk["content_raw"].replace("]]>","]]]]><![CDATA[>").encode("utf-8") + b']]></content_raw>\n').decode("utf-8"))
            self._outfile.write('\t\t<responses>\n')
            for response in plurk["responses"]:
                if response["uid"] in people:
                    username = people[response["uid"]]["username"]
                    displayname = people[response["uid"]]["displayname"] if people[response["uid"]]["displayname"] != "" else username                    
                    self._outfile.write('\t\t\t<response id="{0}" posted_time="{1}" lang="{2}" username="{3}"'.format(str(response["rid"]), response["posted_time"], response["lang"], username))
                    self._outfile.write((b' displayname="' + cgi.escape(displayname, True).encode("utf-8") + b'">\n').decode("utf-8"))
                else:
                    self._outfile.write('\t\t\t<response id="{0}" posted_time="{1}" lang="{2}" unknown_user="unknown_user">\n'.format(str(response["rid"]), response["posted_time"], response["lang"]))                    
                self._outfile.write((b'\t\t\t\t<qualifier>' + cgi.escape(response["qualifier"]).encode("utf-8") + b'</qualifier>\n').decode("utf-8"))
                self._outfile.write((b'\t\t\t\t<qualifier_translated>' + cgi.escape(response["qualifier_translated"]).encode("utf-8") + b'</qualifier_translated>\n').decode("utf-8"))
                self._outfile.write((b'\t\t\t\t<content_raw><![CDATA[' + response["content_raw"].replace("]]>","]]]]><![CDATA[>").encode("utf-8") + b']]></content_raw>\n').decode("utf-8"))
                self._outfile.write('\t\t\t</response>\n')
                              
            self._outfile.write('\t\t</responses>\n')
            
            def outputMiscPeople(peopleTypeSingular, plurkKeyUsesPlural, breakCallback = None):
                self._outfile.write('\t\t<' + peopleTypeSingular + 's>\n')
                if not breakCallback is None:
                    if breakCallback(plurk[peopleTypeSingular + ("s" if plurkKeyUsesPlural else "")]):
                        return
                    
                for miscPerson in plurk[peopleTypeSingular + ("s" if plurkKeyUsesPlural else "")]:
                    if not miscPerson in people:
                        self._outfile.write('\t\t\t<' + peopleTypeSingular + ' unknown_user="unknown_user" />\n')
                    else:
                        username = people[miscPerson]["username"]
                        displayname = people[miscPerson]["displayname"] if people[miscPerson]["displayname"] != "" else username
                        self._outfile.write((b'\t\t\t<' + peopleTypeSingular.encode("ascii") + b' username="' + cgi.escape(username, True).encode("utf-8") + b'" displayname="' + cgi.escape(displayname, True).encode("utf-8") + b'" />\n').decode("utf-8"))
    
                self._outfile.write('\t\t</' + peopleTypeSingular + 's>\n')
                
            def checkAudienceListForFriend(audienceList):
                if len(audienceList) > 0 and audienceList[0] == 0:
                    self._outfile.write('\t\t\t<friends />\n')
                    return True
                return False

            outputMiscPeople("favorer", True)
            outputMiscPeople("replurker", True)
            outputMiscPeople("limited_to", False, checkAudienceListForFriend)
            
            self._outfile.write('\t</plurk>\n')
        
    def postpare(self):
        self._outfile.write('</plurks>')
        self._outfile.close()
        
        
class _HTMLFileFront(_FileFrontInterface):
    def __init__(self, filename, username, displayName, htmlTimeOffsetSign, htmlTimeOffsetHour, htmlTimeOffsetMinute, cssFilename, outLogFunc):
        self._filename = filename
        self._outfile = None
        self._username = username
        self._displayName = displayName
        self._htmlTimeOffsetSign = htmlTimeOffsetSign
        self._htmlTimeOffsetHour = htmlTimeOffsetHour
        self._htmlTimeOffsetMinute = htmlTimeOffsetMinute
        self._cssFilename = cssFilename
        self._outLogFunc = outLogFunc
        self._unknownUserDisplayName = "Unknown Plurker"
        
    def prepare(self):
        try:
            cssFile = codecs.open(self._cssFilename, "r", "utf-8")
        except IOError:
            self._outLogFunc("** Warning: Could not open stylesheet file; the output HTML will be ugly.")
            cssContent = ""
        else:
            cssContent = cssFile.read()
            cssFile.close()
        
        self._outfile = codecs.open(self._filename + ".html", "w", "utf-8")
        self._outfile.write('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">\n')
        self._outfile.write('<html xmlns="http://www.w3.org/1999/xhtml">\n')
        self._outfile.write('\t<head>\n')
        self._outfile.write('\t\t<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />\n')
        self._outfile.write((b'\t\t<title>' + self._displayName.encode("utf-8") + b'\'s plurk Backup</title>\n').decode("utf-8"))
        self._outfile.write('\t\t<style type="text/css">\n')
        self._outfile.write(cssContent)
        self._outfile.write('\t\t</style>\n')
        self._outfile.write('\t</head>\n')
        self._outfile.write('\t<body>\n')
        self._outfile.write((b'\t\t<h1>' + self._displayName.encode("utf-8") + b'\'s plurk Backup</h1>\n').decode("utf-8"))
        self._outfile.write('\t\t<p class="smallnote">\n')
        self._outfile.write('\t\t\tClick on a plurk\'s timestamp to go to its page on plurk.com .\n')
        self._outfile.write('\t\t</p>\n')
        
    def writePlurks(self, plurks, people):
        timeZoneDelta = datetime.timedelta(hours = self._htmlTimeOffsetHour, minutes = self._htmlTimeOffsetMinute)

        # since there is no html manipulation, let's output the file plain-text-ly, and not using any dom modules
        for plurk in plurks:
            plurkTime = datetime.datetime.strptime(plurk["posted_time"], "%a, %d %b %Y %H:%M:%S %Z")
            if self._htmlTimeOffsetSign == 1:
                plurkTime += timeZoneDelta
            else:
                plurkTime -= timeZoneDelta
                
            plurk_id = plurk["plurk_id"]
            b36chars = '0123456789abcdefghijklmnopqrstuvwxyz'
            plurkID36 = ""
            while plurk_id:
                plurk_id, mod = divmod(plurk_id, 36)
                plurkID36 = b36chars[mod] + plurkID36

            self._outfile.write('\n')
            self._outfile.write('\t\t<div class="plurk_block">\n')
            self._outfile.write('\t\t\t<table class="pb_plurk">\n')
            self._outfile.write('\t\t\t\t<tr>\n')
            self._outfile.write((b'\t\t\t\t\t<td class="pb_plurk_name_qualifier"><a href="http://www.plurk.com/' + cgi.escape(self._username, True).encode("ascii") + b'" class="plurk_name">' + cgi.escape(self._displayName).encode("utf-8") + b'</a> <span class="' + ((b"qualifier qualifier_" + cgi.escape(plurk["qualifier"], True).encode("utf-8")) if plurk["qualifier"] != "" and plurk["qualifier"] != ":" else b"" ) + b'">' + cgi.escape(plurk["qualifier_translated"]).encode("utf-8") + b'</span></td>\n').decode("utf-8"))
            self._outfile.write((b'\t\t\t\t\t\t<td class="pb_plurk_content">' + plurk["content"].encode("utf-8") + b'<br />\n').decode("utf-8"))
            self._outfile.write('\t\t\t\t\t\t\t<p class="pb_plurk_timestamp_and_other_stats"><a href="http://www.plurk.com/p/' + plurkID36 + '">' + plurkTime.strftime("%Y-%m-%d %H:%M:%S") + '</a> - ' + str(len(plurk["responses"])) + ' response(s) - ' + str(plurk["favorite_count"]) + ' favorite(s) - ' + str(plurk["replurkers_count"]) + ' replurker(s)</p>\n')
            self._outfile.write('\t\t\t\t\t\t</td>\n')
            self._outfile.write('\t\t\t\t</tr>\n')
            self._outfile.write('\t\t\t</table>\n')
            self._outfile.write('\t\t\t\n')
            self._outfile.write('\t\t\t<hr class="pb_hr" />\n')
            self._outfile.write('\t\t\t\n')
            
            self._outfile.write('\t\t\t<div class="pb_responseoffset">\n')
            
            rowAlternating = 0
            for response in plurk["responses"]:
                responseTime = datetime.datetime.strptime(response["posted_time"], "%a, %d %b %Y %H:%M:%S %Z")
                if self._htmlTimeOffsetSign == 1:
                    responseTime += timeZoneDelta
                else:
                    responseTime -= timeZoneDelta                
                
                if not response["uid"] in people:
                    self._outfile.write('\t\t\t\t<table class="pb_response pb_response_bg' + str(rowAlternating) + ' pb_response_unknown_user">\n')
                    self._outfile.write('\t\t\t\t\t<tr>\n')
                    self._outfile.write('\t\t\t\t\t\t<td class="pb_response_name_qualifier"><span class="plurk_name">' + self._unknownUserDisplayName + '</span>')
                else:
                    username = people[response["uid"]]["username"]
                    displayname = people[response["uid"]]["displayname"] if people[response["uid"]]["displayname"] != "" else username
                    self._outfile.write('\t\t\t\t<table class="pb_response pb_response_bg' + str(rowAlternating) + '">\n')
                    self._outfile.write('\t\t\t\t\t<tr>\n')
                    self._outfile.write((b'\t\t\t\t\t\t<td class="pb_response_name_qualifier"><a href="http://www.plurk.com/' + cgi.escape(username, True).encode("utf-8") + b'" class="plurk_name">' + cgi.escape(displayname).encode("utf-8") + b'</a>').decode("utf-8"))

                self._outfile.write((b' <span class="' + ((b"qualifier qualifier_" + cgi.escape(response["qualifier"], True).encode("utf-8")) if response["qualifier"] != "" and response["qualifier"] != ":" else b"" ) + b'">' + cgi.escape(response["qualifier_translated"]).encode("utf-8") + b'</span></td>\n').decode("utf-8"))
                self._outfile.write((b'\t\t\t\t\t\t<td class="pb_response_content">' + response["content"].encode("utf-8") + b'<br />\n').decode("utf-8"))
                self._outfile.write('\t\t\t\t\t\t\t<p class="pb_response_timestamp">' + responseTime.strftime("%Y-%m-%d %H:%M:%S") + '</p>\n')
                self._outfile.write('\t\t\t\t\t\t</td>\n')
                self._outfile.write('\t\t\t\t\t</tr>\n')
                self._outfile.write('\t\t\t\t</table>\n')

                rowAlternating = (rowAlternating + 1) % 2
                              
            self._outfile.write('\t\t\t</div>\n')
            self._outfile.write('\t\t\t<hr class="pb_hr" />\n')
            self._outfile.write('\t\t\t<table class="pb_misc_people">\n')
            
            def outputMiscPeople(plurkKey, typeText, breakCallback = None):
                if len(plurk[plurkKey]) > 0:
                    self._outfile.write('\t\t\t\t<tr>\n')
                    self._outfile.write('\t\t\t\t\t<th>' + typeText + '</th>\n')
                    self._outfile.write('\t\t\t\t\t<td>\n')
                    
                    if not breakCallback is None:
                        if breakCallback(plurk[plurkKey]):
                            return
    
                    buffer_to_write = '\t\t\t\t\t\t'
                    for miscPerson in plurk[plurkKey]:
                        if not miscPerson in people:
                            buffer_to_write += '<span class="plurk_name">' + self._unknownUserDisplayName + '</span>, '
                        else:
                            username = people[miscPerson]["username"]
                            displayname = people[miscPerson]["displayname"] if people[miscPerson]["displayname"] != "" else username
                            buffer_to_write += (b'<a href="http://www.plurk.com/' + cgi.escape(username, True).encode("utf-8") + b'" class="plurk_name">' + cgi.escape(displayname).encode("utf-8") + b'</a>, ').decode("utf-8")
                    buffer_to_write = buffer_to_write[:-2]    # get rid of trailing ", "...stupid but works
                    self._outfile.write(buffer_to_write + '\n')
                    self._outfile.write('\t\t\t\t\t</td>\n')
                    self._outfile.write('\t\t\t\t</tr>\n')  
                
            def checkAudienceListForFriend(audienceList):
                if audienceList[0] == 0:
                    self._outfile.write('\t\t\t\t\t\t(friends)\n')
                    return True
                return False

            outputMiscPeople("favorers", "Favorers")
            outputMiscPeople("replurkers", "Replurkers")
            outputMiscPeople("limited_to", "Audience", checkAudienceListForFriend)

            self._outfile.write('\t\t\t</table>\n')
            self._outfile.write('\t\t</div>\n')        
        
    def postpare(self):
        self._outfile.write('\t</body>\n')
        self._outfile.write('</html>')
        self._outfile.close()        


class _DataStorage:
    """
        content is used for the pretty-output HTML file output.
        content_raw is used for raw XML file output.
        
        plurks: [{plurk_id, posted_time, lang, qualifier, qualifier_translated, content, content_raw, responses: RESPONSES_LIST}, {}]
        RESPONSES_LIST: [{rid, uid, posted_time, lang, qualifier, qualifier_translated, content, content_raw}, {}]
        people: {id: {username, displayname}}   # displayname = username if displayname == ""
        # id's are integers, not strings.
        # people who have responded may have had their plurk accounts deleted - check for key not found.
    """
    def __init__(self):
        self._plurks = []   # old-entry-first
        self._people = {}
        
    def addPlurks(self, plurks):
        # the passed-in plurks are new-entry-first order, so we do some reversal
        plurksCopy = copy.copy(plurks)
        plurksCopy.reverse()
        plurksCopy.extend(self._plurks)
        self._plurks = plurksCopy
        
    def addPeople(self, people):
        self._people.update(people)
        
    def flushToFileFront(self, fileFront):
        fileFront.writePlurks(self._plurks, self._people)
        self._plurks = []
        self._people = {}


class BackupAgent:
    class _ResponseFetcher(threading.Thread):
        def __init__(self, associatedPlurk, backupAgent, addPeopleLock, addPeopleFunc):
            threading.Thread.__init__(self)
            self._associatedPlurk = associatedPlurk
            self._backupAgent = backupAgent
            self._addPeopleLock = addPeopleLock
            self._addPeopleFunc = addPeopleFunc
            
        def run(self):
            # sometimes we receive 500 Internal Server Error so we have to retry
            grRes = {}
            while not "responses" in grRes:
                grRes = self._backupAgent._plurkObj.getResponses(self._associatedPlurk["plurk_id"], 0)
            
            responses = BackupAgent._extractResponsesFromGetResponsesRes(grRes)
            self._addPeopleLock.acquire()
            self._addPeopleFunc(BackupAgent._extractPeopleFromGetResponsesRes(grRes))
            self._addPeopleLock.release()
            self._associatedPlurk["responses"] = responses
            self._backupAgent._outLogFunc("Consumed plurk posted at: " + self._associatedPlurk["posted_time"])

    
    def __init__(self, apiKey, outLogFunc, quesAskFunc, outFilename = "", xmlOut = False, htmlOut = True, htmlTimeOffsetSign = 1, htmlTimeOffsetHour = 0, htmlTimeOffsetMinute = 0, cssFilename = "style.css", plurksPerRequest = 50):
        self._plurkObj = plurklib.PlurkAPI(apiKey)
        self._outLogFunc = outLogFunc
        self._quesAskFunc = quesAskFunc
        self._outFilename = outFilename
        if (not xmlOut) and (not htmlOut):
            raise PlurackupLibError("Both xmlOut and htmlOut are False - Dunno what to output")
            
        self._xmlOut = xmlOut
        self._htmlOut = htmlOut
        self._htmlTimeOffsetSign = 1 if htmlTimeOffsetSign >= 0 else -1
        self._htmlTimeOffsetHour = htmlTimeOffsetHour
        self._htmlTimeOffsetMinute = htmlTimeOffsetMinute
        self._cssFilename = "style.css" if cssFilename == "" else cssFilename
        self._plurksPerRequest = plurksPerRequest
    
    @staticmethod
    def _arrayizeAudienceFromPlurkLimitedTo(limitedToString):
        return [] if limitedToString == None or limitedToString == "" else [int(audience) for audience in re.findall("\d+", limitedToString)]

    @staticmethod    
    def _extractPlurksFromGetPlurksRes(gpRes):
        return [{"plurk_id": plurk["plurk_id"], "posted_time": plurk["posted"], "lang": plurk["lang"], "qualifier": plurk["qualifier"], "qualifier_translated": plurk["qualifier_translated"] if "qualifier_translated" in plurk else plurk["qualifier"], "favorite_count": plurk["favorite_count"], "favorers": plurk["favorers"], "replurkers_count": plurk["replurkers_count"], "replurkers": plurk["replurkers"], "limited_to": BackupAgent._arrayizeAudienceFromPlurkLimitedTo(plurk["limited_to"]) if "limited_to" in plurk else [], "content_raw": plurk["content_raw"], "content": plurk["content"]} for plurk in gpRes["plurks"]]

    @staticmethod
    def _extractResponsesFromGetResponsesRes(grRes):
        return [{"rid": response["id"], "uid": response["user_id"], "posted_time": response["posted"], "lang": response["lang"], "qualifier": response["qualifier"], "qualifier_translated": response["qualifier_translated"] if "qualifier_translated" in response else response["qualifier"], "content_raw": response["content_raw"], "content": response["content"]} for response in grRes["responses"]]

    @staticmethod
    def _extractPeopleFromGetResponsesRes(grRes):
        return {} if isinstance(grRes["friends"], list) else {person["uid"]: {"username": person["nick_name"], "displayname": person["display_name"] if "display_name" in person else person["nick_name"]} for person in grRes["friends"].values()}
    
    @staticmethod
    def _extractPeopleFromGetPlurksRes(gpRes):
        return {} if isinstance(gpRes["plurk_users"], list) else {person["id"]: {"username": person["nick_name"], "displayname": person["display_name"] if "display_name" in person else person["nick_name"]} for person in gpRes["plurk_users"].values()}

    def doBackup(self, username, password):
        self._outLogFunc("Logging in...")
        loginRes = self._plurkObj.login(username, password)
        if "error_text" in loginRes:
            self._outLogFunc("Login failed.")
            return
        
        displayName = loginRes["user_info"]["display_name"] if "display_name" in loginRes["user_info"] and loginRes["user_info"]["display_name"] != "" else username
        
        self._outLogFunc((b"Login was successful; Display name: " + displayName.encode("utf-8")).decode("utf-8"))
        
        filename = self._outFilename if self._outFilename != "" else username
        
        dataStorage = _DataStorage()
        addPeopleLock = threading.RLock()
        
        responseFetchers = []
        
        self._outLogFunc("Begin to fetch plurks and responses...")
       
        # add one day to get around any timezone issues (yeah, though we have UTC-12 through UTC+14 = 26 hours, though.)
        currentOffsetDateTime = (datetime.datetime.now() + datetime.timedelta(1))
        while True: # break when gpRes has zero content
            gpRes = self._plurkObj.getOwnPlurks(currentOffsetDateTime.strftime("%Y-%m-%dT%H:%M:%S"), self._plurksPerRequest)
            if len(gpRes["plurks"]) == 0:
                break
            
            plurks = BackupAgent._extractPlurksFromGetPlurksRes(gpRes)
            
            addPeopleLock.acquire()
            dataStorage.addPeople(BackupAgent._extractPeopleFromGetPlurksRes(gpRes))
            addPeopleLock.release()
            
            for plurk in plurks:
                responseFetcher = BackupAgent._ResponseFetcher(plurk, self, addPeopleLock, lambda people: dataStorage.addPeople(people))
                responseFetcher.start()
                responseFetchers.append(responseFetcher)
                
            dataStorage.addPlurks(plurks)
        
            currentOffsetDateTime = datetime.datetime.strptime(plurks[len(plurks) - 1]["posted_time"], "%a, %d %b %Y %H:%M:%S %Z")
            

        self._outLogFunc("Waiting for outstanding response fetcher threads to join...")
        for responseFetcher in responseFetchers:
            responseFetcher.join()
        
        self._outLogFunc("Fetching is done. Logging out.")
        self._plurkObj.logout()
        
        fileFronts = _MultipleFileFront()
        if self._xmlOut:
            fileFronts.attachFileFront(_XMLFileFront(filename))
        if self._htmlOut:
            fileFronts.attachFileFront(_HTMLFileFront(filename, username, displayName, self._htmlTimeOffsetSign, self._htmlTimeOffsetHour, self._htmlTimeOffsetMinute, self._cssFilename, self._outLogFunc))
        
        self._outLogFunc("Writing to file...")
        fileFronts.prepare()
        dataStorage.flushToFileFront(fileFronts)
        fileFronts.postpare()

        self._outLogFunc("Your plurks are now backed up in " + filename + ".xml and/or " + filename + ".html .")
