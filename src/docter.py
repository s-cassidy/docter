import yaml
import subprocess
import re
from urllib.request import Request, urlopen


def main():
    results = ddg_search("python calendar")
    urls = [url for url in result_urls(results)]
    config = load_config("test/test.yaml")
    keyword = "python"
    for url in urls:
        if match := match_url_with_source_config(url, keyword, config):
            break
    launch_page("w3m", url)


def match_url_with_source_config(url: str, keyword: str, config: dict) -> str:
    keyword_sources = config["keywords"][keyword]["sources"]
    for source in keyword_sources:
        try:
            pattern = config['sources'][source]['url']
        except KeyError:
            print(f"Warning: source {source} is not configured")
        if pattern in url:
            return source

def launch_page(browser: str, url: str, gui: bool=False) -> None:
    subprocess.run([browser, url])



def load_config(path: str) -> dict:
    with open(path, 'r', encoding='utf8') as f:
        config = yaml.load(f, Loader=yaml.Loader)
    return config


def result_urls(results_html: str) -> str:
    for line in results_html.splitlines():
        exp = '(?:result__url.+)(http.+)"'
        match = re.search(exp, line) 
        if match:
            yield match.group(1)


def ddg_search(search_string: str) -> str:
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    search = '+'.join(search_string.split())
    req = Request(f"https://duckduckgo.com/html/?q={search}", headers=headers)
    return urlopen(req).read().decode()

def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf8") as f:
        try:
            config = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            print(exc)
    return config



if __name__ == "__main__":
    main()
