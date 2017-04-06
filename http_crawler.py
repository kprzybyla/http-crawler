#!/usr/bin/env python
#!coding=utf-8

# MIT License

# Copyright (c) 2017 Krzysztof Przybyła

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""

    Simple HTTPCrawler for downloading given file or directory via URL

    @python             2.7.*
    @requirements       [enum, lxml]
    @website            https://github.com/kprzybyla/http-crawler

"""

import os
import re
import enum
import urllib
import urlparse

from lxml import html

URLType = enum.Enum('UrlType', ['none', 'file', 'directory'])

class HTTPCrawler(object):

    @staticmethod
    def download(url, path):

        url_type = HTTPCrawler._discover_url(url)

        if url_type is URLType.none:
            return

        if url_type is URLType.file:
            HTTPCrawler._download_file(url, path)
            return

        HTTPCrawler._create_path(path)

        for url, path in HTTPCrawler._list_directory(url, path):
            HTTPCrawler.download(url, path)

    @staticmethod
    def _download_file(url, path):

        try:
            urllib.urlretrieve(url, path)
        except urllib.ContentTooShortError:
            raise HTTPCrawlerError('Couldn\'t download file from "{}" to "{}" due to file content being too short'
                                   .format(url, path))
        except Exception as e:
            raise HTTPCrawlerError('Couldn\'t download file from "{}" to "{}" due to unexpected error: "{}"'
                                   .format(url, path, e))

    @staticmethod
    def _discover_url(url):

        if HTTPCrawler._endswith(url, ['^.*\.\w+$']):
            return URLType.file

        try:
            tree = html.parse(url)
        except IOError:
            return URLType.none

        if HTTPCrawler._is_index_of(url, tree):
            return URLType.directory

        return URLType.file

    @staticmethod
    def _list_directory(url, path):

        content = []

        for a_object in html.parse(url).xpath('//a'):

            if a_object.get('href') in ['./', '../']:
                continue

            a_object_url = urlparse.urljoin(HTTPCrawler._normalize_url(url), a_object.get('href'))
            a_object_path = os.path.join(path, a_object.text)

            content.append((a_object_url, a_object_path))

        return content

    @staticmethod
    def _normalize_url(url):

        if url[-1] != '/':
            return url + '/'

        return url

    @staticmethod
    def _is_index_of(url, tree):

        url_a = urllib.unquote(url[url.replace('://', 'xxx').index('/'):])
        dir_title = '/html/head/title[contains(text(), "Index of {}")]'.format(url_a)

        return tree.xpath(dir_title)

    @staticmethod
    def _create_path(path):

        if not os.path.exists(path):

            try:
                os.makedirs(path)
            except:
                raise HTTPCrawlerError('Couldn\'t create directory structure')

        if not os.path.isdir(path):
            raise HTTPCrawlerError('Path is not a directory')

    @staticmethod
    def _endswith(string, list_of_matches):

        for match in list_of_matches:
            if re.match(match, string):
                return True
        else:
            return False

class HTTPCrawlerError(Exception):
    __module__ = Exception.__module__
