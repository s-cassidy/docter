#!/usr/bin/env python3
import toml
import subprocess
import argparse
import re
from urllib.request import Request, urlopen
from pathlib import Path


def main():
    args = get_arguments()
    config_path = f"{str(Path.home())}/.config/docter.toml"
    instance_config = load_config(config_path, args)
    search_str = instance_config.get_search_string()
    search_result_page = ddg_search(search_str)
    results = [result for result in get_result_urls(search_result_page)]
    result_url, browser = select_result_and_browser(results, instance_config)
    if result_url is not None:
        launch_page(browser, result_url)


def get_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-g", "--gui", action="store_true", help="use the default gui browser"
    )
    parser.add_argument(
        "-l",
        "--lucky",
        action="store_true",
        help="open first result without asking confirmation",
    )
    parser.add_argument(
        "-b", "--browser", help="optionally pass a browser to open the link"
    )
    parser.add_argument(
        "keyword", help="configurable keyword to filter results from specific sources"
    )
    parser.add_argument(
        "terms",
        help="terms to search for from keyword sources",
        nargs=argparse.REMAINDER,
    )
    return parser.parse_args()


class InstanceConfig:
    def __init__(self, global_config, args) -> None:
        self.keyword = args.keyword
        self.handle_no_keyword(global_config)
        self.defaultbrowser = global_config["defaultbrowser"]
        self.defaultgui = global_config["defaultgui"]
        self.set_browser = args.browser
        self.gui_browser = args.gui
        self.lucky = args.lucky or global_config["always_lucky"]
        self.terms = args.terms
        self.added_terms = global_config["keywords"][self.keyword]["terms"]
        self.sources = self.make_sources_dict(global_config)

    def make_sources_dict(self, global_config: dict) -> dict:
        keyword_sources = global_config["keywords"][self.keyword]["sources"]
        all_sources = global_config["sources"]
        keyword_sources_dict = dict()
        for source in keyword_sources:
            if source not in all_sources:
                print(f"{self.keyword} source {source} not configured")
                continue
            keyword_sources_dict[source] = all_sources[source]
        return keyword_sources_dict

    def handle_no_keyword(self, config: dict) -> None:
        keyword = self.keyword
        if keyword not in config["keywords"]:
            print(
                f"{keyword} is not a keyword;"
                " performing a standard search with default settings"
            )
            config["keywords"][""] = {"terms": [keyword], "sources": ["any"]}
            config["sources"]["any"] = {"urlpattern": ""}
            self.keyword = ""

    def get_search_string(self) -> str:
        search_str = " ".join(self.added_terms + self.terms)
        return search_str

    def match_url_with_source(self, url: str) -> str | None:
        for source_name, source_info in self.sources.items():
            try:
                pattern = source_info["urlpattern"]
            except KeyError:
                print(f"Warning: source {source_name} is not configured")
            if pattern in url:
                return source_name
        return None


def select_result_and_browser(results: list, config) -> tuple:
    for result in results:
        if source := config.match_url_with_source(result):
            browser = select_browser(source, config)
            if config.lucky or offer_user_page_launch(result, browser):
                return result, browser
    print(
        f"No other likely results found from {config.keyword}"
        f" sources for {config.terms}."
    )
    return None, None


def select_browser(source: str, config) -> str:
    if config.set_browser:
        return config.set_browser
    if config.gui_browser:
        return config.defaultgui
    default = config.defaultbrowser
    return config.sources[source].get("browser", default)


def offer_user_page_launch(url: str, browser: str) -> bool:
    while True:
        response = input(f"Go to {url}? (browser: {browser}) Y/n: ").lower()
        if response.lower() in ["no", "n"]:
            return False
        if response.lower() in ["y", "yes", ""]:
            return True


def load_config(path: str, keyword: str) -> InstanceConfig:
    with open(path, "r", encoding="utf8") as f:
        global_config = toml.load(f)
    instance_config = InstanceConfig(global_config, keyword)
    return instance_config


def ddg_search(search_string: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X"
        " 10_10_1) AppleWebKit/537.36 (KHTML, "
        "like Gecko) Chrome/39.0.2171.95 Safari/537.36"
    }

    print(f"Searching DuckDuckGo for '{search_string}'")
    url_string = search_string.replace(" ", r"+")
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
