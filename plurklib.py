"""
    Copyright (c) 2010 Kurt Karakurt <kurt.karakurt@gmail.com>
    Modified by Mnjul/purincess (Min-Zhong Lu) for use in the plurakup (plurk backup) project.

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
import sys
import urllib
import json
if sys.version[:1] == '3':
    import http.cookiejar
elif sys.version[:1] == '2':
    import urllib2
    import cookielib
else:
    raise PlurklibError("Your python interpreter is too old. Please consider upgrading.")

class PlurklibError(Exception):
    
    def __init__(self, value):
        self.value = value
        
    def __str__(self):
        return repr(self.value)

class PlurkAPI:

    def __init__(self, key):
        """ Required parameters:
                key: Your Plurk API key.
        """
        self._api_key = key
        self._username = None
        self._password = None
        #self._logged_in = False
        #self._uid = -1
        # self._friends = {}

    def _call_api(self, apirequest, parameters, https=False):
        """ Send a request to Plurk API and decode response.
            Required parameters:
                apirequest: The path to API's function, like: 'API/Users/logout'
                parameters: The parameters of the request, that sends like POST
            Optional parameters:
                https: If it's set to True, then HTTPS and SSL are used for the API call.
            Successful return:
                The parsed dict object is returned for further processing.
        """
        if sys.version[:1] == '3':
            return self._python3_call_api(apirequest, parameters, https)
        elif sys.version[:1] == '2': 
            return self._python2_call_api(apirequest, parameters, https)
        else:
            raise PlurklibError("Your python interpreter is too old. Please consider upgrading.")
        
    def _python2_call_api(self, apirequest, parameters, https=False):
        parameters['api_key'] = self._api_key
        post = urllib.urlencode(parameters)
        if https:
            request = urllib2.Request(url = 'https://www.plurk.com' + apirequest, data = post)
        else:
            request = urllib2.Request(url = 'http://www.plurk.com' + apirequest, data = post)
        try:
            response = urllib2.urlopen(request)
        except urllib2.HTTPError as message:
            if message.code == 400:
                response = json.loads(message.fp.read().decode("utf-8"))
                return response
            else:
                raise message

        if apirequest == '/API/Users/login':
            cookies = cookielib.CookieJar()
            opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookies))
            urllib2.install_opener(opener)
            cookies.extract_cookies(response, request)
        result = json.loads(response.read().decode("utf-8"))
        return result
        
    def _python3_call_api(self, apirequest, parameters, https=False):
        parameters['api_key'] = self._api_key
        post = urllib.parse.urlencode(parameters).encode("utf-8")
        if https:
            request = urllib.request.Request(url = 'https://www.plurk.com' + apirequest, data = post)
        else:
            request = urllib.request.Request(url = 'http://www.plurk.com' + apirequest, data = post)
        try:
            response = urllib.request.urlopen(request)
        except urllib.error.HTTPError as message:
            if message.code == 400:
                response = json.loads(message.fp.read().decode("utf-8"))
                return response
            else:
                raise message
            
        if apirequest == '/API/Users/login':
            cookies = http.cookiejar.CookieJar()
            opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookies))
            urllib.request.install_opener(opener)
            cookies.extract_cookies(response, request)
        result = json.loads(response.read().decode("utf-8"))
        return result

#=================================== Users ===================================

    def login(self, username, password, no_data=None):
        """ Log in to Plurk. Login an already created user. Using HTTPS.
            Login creates a session cookie, which can be used to access the other methods.
            Required parameters:
                username: The user's nick name or email.
                password: The user's password.
            Optional parameters:
                no_data: If it's set to "1" then the common data is not returned.
            Successful return:
                The data of /API/Profile/getOwnProfile if no_data isn't set. 
                If no_data is set to "1" then {'success_text': 'ok'} is returned.
            Error returns:
                {'error_text': 'Invalid login'}
                {'error_text': 'Too many logins'}
        """
        self._username = username
        self._password = password
        parameters = {'username': username, 
                      'password': password} 
        if no_data != None:
            parameters['no_data'] = no_data
        request = '/API/Users/login'
        response = self._call_api(request, parameters, True)
        return response

    def logout(self):
        """ Logout from Plurk.
            Successful return:
                {'success_text': 'ok'} if the user is logged out.
        """
        parameters = {}
        request = '/API/Users/logout'
        response = self._call_api(request, parameters)
        return response

#=================================== Timeline ===================================

    def getOwnPlurks(self, offset = None, limit = 20):
        parameters = {'offset': offset,
                  'limit': limit,
                  'only_user': "yes",
                  'favorers_detail': "true",
                  'limited_detail': "true",
                  'replurkers_detail': "true"}
        request = '/API/Timeline/getPlurks'
        response = self._call_api(request, parameters)
        return response

#=================================== Responses ===================================

    def getResponses(self, plurk_id, from_response):
        """ Fetches responses for plurk with plurk_id and some basic info about the users.
            Required parameters:
                plurk_id: The plurk that the responses belong to.
                from_response: Only fetch responses from an offset - could be 5, 10 or 15.
            Successful return:
                Returns a dict object of responses, friends (users that has posted responses) 
                and responses_seen (the last response that the logged in user has seen) e.g. 
                {'friends': {'3': ...}, 
                 'responses_seen': 2, 
                 'responses': [{'lang': 'en', 'content_raw': 'Reforms...}}
            Error returns:
                {'error_text': 'Requires login'}
                {'error_text': 'Invalid data'}
                {'error_text': 'Plurk not found'}
                {'error_text': 'No permissions'}
        """
        parameters = {'plurk_id': plurk_id,
                      'from_response': from_response}
        request = '/API/Responses/get'
        response = self._call_api(request, parameters)
        return response

