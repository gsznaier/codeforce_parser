'''

Scrapy spider to scrape codeforces successful submissions.
NOTE: Robots.txt is set to False

How to use

1. Change the PAGE_LIMIT according to your need
2. Change LANGUAGE to desired one by checking with codeforces language options


'''

from scrapy.http import FormRequest
from urllib.request import urlopen

import scrapy
import json

'''possible language choices:
   "c.gcc":GNU C
   "c.gcc11": GNU C11
   "cpp.clang++-diagnose": Clang++17 Diagnostics
   "cpp.g++": GNU C++
   "cpp.g++11": GNU C++11
   "cpp.g++14": GNU C++14
   "cpp.g++17": GNU C++17
   "cpp.g++17-drmemory": GNU C++17 Diagnostics
   "cpp.ms": MS C++
   "csharp.mono": Mono C#
   "d": D
   "go":Go
   "haskell.ghc": Haskell
   "java8": Java 8
   "kotlin": Kotlin
   "ocaml": Ocaml
   "pas.dpr": Delphi
   "pas.fpc": FPC
   "pas.pascalabc": PascalABC.NET
   "perl.5": Perl
   "php.5":PHP
   "python.2":Python 2
   "python.3": Python 3
   "python.pypy2": PyPy 2
   "python.pypy3": PyPy 3
   "ruby.1": Ruby
   "rust": Rust
   "scala": Scala
   "v8.3": JavaScript
   "v8.nodejs": Node.js
    '''

class QuotesSpider(scrapy.Spider):
    PAGE_LIMIT = 5         # Change Page limit to get more successful submission
    LANGUAGE = 'c.gcc'  # Get solutions from the given Language
    name = "cfSpider"

    def __init__(self, lang = 'python.3', **kwargs):
        LANGUAGE = lang

    def start_requests(self):
        # Make API call to codeforces server
        html = urlopen('http://codeforces.com/api/problemset.problems').read()

        # Convert given data into JSON format
        jsonData = json.loads(html.decode('utf-8'))

        for data in jsonData['result']['problems']:
            tags = data['tags']
            index = data['index']
            contestId = data['contestId']
            name = data['name']

            yield scrapy.Request(url='http://codeforces.com/problemset/status/'+str(contestId)+'/problem/'+str(index),
                            callback=self.parse,
                            meta = {'tags': tags, 'index': index, 'contestId': contestId, 'name': name})

    def get_details(self, response):
        tags = response.meta['tags']
        index = response.meta['index']
        contestId = response.meta['contestId']
        name = response.meta['name']
        tem = response.meta['tem']
        url = 'http://codeforces.com/problemset/status/'+ str(contestId) +'/problem/'+ str(index) +'/page/'+str(tem)+'?order=BY_PROGRAM_LENGTH_ASC'
        data = response.meta['data']

        for i in response.css('tr::attr(data-submission-id)').extract():
            data.add(i)

        tem += 1    # Takes care of solution pages
        if tem >= self.PAGE_LIMIT:
            yield {
                "contestId": contestId,
                "index": index,
                "name": name,
                "tags": tags,
                "language": self.LANGUAGE,
                "Submissions": data,
            }
        else:
            yield scrapy.Request(url = url, 
                            callback= self.get_details, 
                            meta = {'tags': tags, 'index': index, 'contestId': contestId, 'name': name, 'data': data, 'tem': tem})

    def parse(self, response):
        data = set() # Empty data used to append successfully submissions in one set
        tags = response.meta['tags']
        index = response.meta['index']
        contestId = response.meta['contestId']
        name = response.meta['name']
        return scrapy.FormRequest.from_response(
                response,
                formxpath='//*[@id="sidebar"]/div/div[4]/form',
                dont_filter = True,
                meta = {'tags': tags, 'index': index, 'contestId': contestId, 'name': name, 'data': data, 'tem': 2},
                callback=self.get_details,
                formdata={'programTypeForInvoker': self.LANGUAGE,
                    'verdictName': 'OK'})
