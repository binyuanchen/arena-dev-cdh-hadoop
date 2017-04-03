#!/usr/bin/env python

import json
import base64
import urllib
import urllib2


class RestUtil(object):
    def __init__(self, username=None, password=None):
        if not username:
            raise RuntimeError("missing rest api username")
        self.username = username
        if not password:
            raise RuntimeError("missing rest api password")
        self.password = password

    def _populate_default_headers(self, headers):
        if not headers:
            headers = {}
        if 'Content-Type' not in headers:
            headers['Content-Type'] = 'application/json'
        if 'Authorization' not in headers:
            b64_auth = base64.b64encode('%s:%s' % (self.username, self.password))
            headers['Authorization'] = 'Basic %s' % b64_auth
        return headers

    def put(self, url=None, headers=None, params=None, body=None):
        headers = self._populate_default_headers(headers)
        if params:
            url += '?' + urllib.urlencode(params)
        print 'REST[put] - url = %s' % url
        print 'REST[put] - headers = %s' % headers
        print 'REST[put] - body = %s' % body
        response_body = None
        try:
            req = urllib2.Request(url, headers=headers)
            resp = None
            opener = urllib2.build_opener(urllib2.HTTPHandler)
            req.get_method = lambda: 'PUT'
            resp = opener.open(req, json.dumps(body))
            raw = resp.read()
            if raw:
                response_body = json.loads(raw)
                print 'REST[put] - response_body = %s' % response_body
        except urllib2.HTTPError, e:
            raise RuntimeError('rest call failed for url %s, status=%s, reason=%s' % (url, e.code, e.reason))

        return response_body

    def post(self, url=None, headers=None, params=None, body=None):
        headers = self._populate_default_headers(headers)
        if params:
            url += '?' + urllib.urlencode(params)
        print 'REST[post] - url = %s' % url
        print 'REST[post] - headers = %s' % headers
        print 'REST[post] - body = %s' % body
        response_body = None
        try:
            req = urllib2.Request(url, headers=headers)
            resp = None
            if body:
                resp = urllib2.urlopen(req, json.dumps(body))
            else:
                # handles also the cases when body = {}, None
                resp = urllib2.urlopen(req, json.dumps({}))
            raw = resp.read()
            if raw:
                response_body = json.loads(raw)
                print 'REST[post] - response_body = %s' % response_body
        except urllib2.HTTPError, e:
            raise RuntimeError('rest call failed for url %s, status=%s, reason=%s' % (url, e.code, e.reason))

        return response_body

    def get(self, url=None, headers=None, params=None):
        headers = self._populate_default_headers(headers)
        if params:
            url += '?' + urllib.urlencode(params)
        print 'REST[get] - url = %s' % url
        print 'REST[get] - headers = %s' % headers
        response_body = None

        try:
            req = urllib2.Request(url, headers=headers)
            resp = urllib2.urlopen(req)
            raw = resp.read()
            if raw:
                response_body = json.loads(raw)
                print 'REST[get] - response_body = %s' % response_body
        except urllib2.HTTPError, e:
            raise RuntimeError('REST[GET] failed, url=%s, status=%s, reason=%s' % (url, e.code, e.reason))

        return response_body
