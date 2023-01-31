#!/usr/bin/env python3
import yaml
import subprocess
import argparse
import re
from urllib.request import Request, urlopen
from pathlib import Path


def main():
    args = get_arguments()
    config_path = f"{str(Path.home())}/.config/docter.yaml"
    instance_config = load_config(config_path, args)
    search_str = instance_config.get_search_string()
    search_result_page = ddg_search(search_str)
    results = [result for result in get_result_urls(search_result_page)]
    result_url, browser = select_result_and_browser(results, instance_config)
    if result_url:
        launch_page(browser, result_url)


def get_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("keyword",
                        help="configurable keyword to select sources")
    parser.add_argument("terms", 
                        help="terms to search for in the selected sources",
                        nargs=argparse.REMAINDER)
    return parser.parse_args()


class InstanceConfig:
    def __init__(self, global_config, args) -> None:
        self.keyword = args.keyword
        self.handle_no_keyword(global_config)
        self.defaultbrowser = global_config['defaultbrowser']
        self.defaultgui = global_config['defaultgui']
        self.gui_browser = False
        self.terms = args.terms
        self.added_terms = global_config['keywords'][self.keyword]['terms']
        self.sources = self.make_sources_dict(global_config)
        print(self.sources)
        self.additional_terms = global_config['keywords'][self.keyword]['terms']

    def make_sources_dict(self, global_config: dict) -> dict:
        keyword_sources = global_config['keywords'][self.keyword]['sources']
        all_sources = global_config['sources']
        sources_dict = dict()
        for source in keyword_sources:
            if source not in all_sources:
                print(f"{word} source {source} not properly configured")
            else:
                sources_dict[source] = all_sources[source]
        return sources_dict

    def handle_no_keyword(self, config: dict) -> None: 
        keyword = self.keyword
        if keyword not in config['keywords']:
            print(f"{keyword} is not a keyword;"
                  " performing a standard search with default settings")
            config['keywords'][''] = {'terms': [keyword],
                                      'sources': ['any']}
            config['sources']['any'] = {'urlpattern': ''}
            self.keyword = ''

    def get_search_string(self) -> str:
        search_str = ' '.join(self.added_terms+self.terms)
        print(f"Searching for {search_str}")
        return search_str

    def match_url_with_source(self, url: str) -> str:
        for source_name, source_info in self.sources.items():
            try:
                pattern = source_info['urlpattern']
            except KeyError:
                print(f"Warning: source {source_name} is not configured")
            if pattern in url:
                return source_name


def select_result_and_browser(results: list, config) -> tuple:
    for result in results:
        if source := config.match_url_with_source(result):
            browser = select_browser(source, config)
            if accept_page_launch(result, browser):
                return result, browser
    else:
        print(f"No other likely results found from {config.keyword}"
              f" sources for {config.terms}."
              )
        return None, browser


def select_browser(source: str, config) -> str:
    default = config.defaultbrowser
    return config.sources[source].get('browser', default)


def accept_page_launch(url: str, browser: str) -> tuple:
    while True:
        response = input(f"Go to {url}? (browser: {browser}) Y/n: ").lower()
        if response.lower() in ["no", "n"]:
            return False
        if response.lower() in ["y", "yes", ""]:
            return True


def load_config(path: str, keyword: str) -> dict:
    with open(path, "r", encoding="utf8") as f:
        try:
            global_config = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            print(exc)
    instance_config = InstanceConfig(global_config, keyword)
    return instance_config



def ddg_search(url_string: str) -> str:
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X"
                             " 10_10_1) AppleWebKit/537.36 (KHTML, "
                             "like Gecko) Chrome/39.0.2171.95 Safari/537.36"
               }
    url_string = url_string.replace(' ', r'+')
    req = Request(
            f"https://duckduckgo.com/html/?q={url_string}",
            headers=headers
            )
    return urlopen(req).read().decode()


def get_result_urls(results_html: str) -> str:
    for line in results_html.splitlines():
        exp = '(?:result__url.+)(http.+)"'
        match = re.search(exp, line)
        if match:
            yield match.group(1)

def launch_page(browser: str, url: str, gui: bool = False) -> None:
    subprocess.run([browser, url])


if __name__ == "__main__":
    main()
