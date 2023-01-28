import yaml
import requests
import re
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup


def main():
    pass

def load_config(path):
    with open(path, 'r', encoding='utf8') as f:
        config = yaml.load(f, Loader=yaml.Loader)
    return config


def result_urls(response):
    for line in response.splitlines():
        exp = '(?:result__url.+)(http.+)"'
        match = re.search(exp, line) 
        if match:
            yield match.group(1)


headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
req = Request("https://duckduckgo.com/html/?q=hello", headers=headers)
response = urlopen(req).read().decode()
urls = [url for url in result_urls(response)]
print(urls)

