#!/usr/bin/env python3
import toml
import subprocess
import argparse
import re
from urllib.request import Request, urlopen
from typing import Tuple, List
from pathlib import Path


def main() -> None:
    args = get_arguments()
    config_path = f"{str(Path.home())}/.config/docter.toml"
    instance_config = load_config(config_path, args)
    search_str = instance_config.search_str
    search_result_page = ddg_search(search_str)
    results = [result for result in get_result_urls(search_result_page)]
    process_results(results, instance_config)
    print(
        f"No other likely results found from {instance_config.keyword}"
        f" sources for '{' '.join(instance_config.terms)}'."
    )


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
        try:
            self.defaultbrowser = global_config["defaultbrowser"]
        except KeyError:
            self.defaultbrowser = "w3m"
        try:
            self.defaultgui = global_config["defaultgui"]
        except KeyError:
            self.defaultgui = None
        self.set_browser = args.browser
        self.gui_browser = args.gui
        try:
            always_lucky = global_config["always_lucky"]
        except KeyError:
            always_lucky = False
        self.lucky = args.lucky or always_lucky
        self.terms = args.terms
        self.added_terms = global_config["keywords"][self.keyword]["terms"]
        self.sources = self.make_sources_dict(global_config)
        self.search_str = self.get_search_string()

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
            config["keywords"][""] = {"terms": keyword, "sources": ["any"]}
            config["sources"]["any"] = {"urlpattern": ""}
            self.keyword = ""

    def get_search_string(self) -> str:
        added_terms = self.added_terms.split()
        search_str = " ".join(added_terms + self.terms)
        return search_str


def match_url_with_source(url: str, sources: dict) -> str | None:
    for source_name, source_info in sources.items():
        try:
            pattern = source_info["urlpattern"]
        except KeyError:
            print(f"Warning: source {source_name} is not configured")
        if pattern in url:
            return source_name
    return None


def process_results(results: List[str], config: InstanceConfig) -> None:
    for result in results:
        source = match_url_with_source(result, config.sources)
        if not source:
            continue
        browser = select_browser(source, config)
        if config.lucky:
            launch_page(browser, result)
            exit()
        offer_user_page_launch(result, browser)


def select_browser(source: str, config: InstanceConfig) -> str:
    if config.set_browser:
        return config.set_browser
    if config.gui_browser:
        return config.defaultgui
    default = config.defaultbrowser
    return config.sources[source].get("browser", default)


def offer_user_page_launch(url: str, browser: str) -> None:
    while True:
        response = input(f"Did you want {url}? (browser: {browser}) Y/m/n/q: ").lower()
        if response.lower() in ["no", "n"]:
            break
        if response.lower() in ["y", "yes", ""]:
            launch_page(browser, url)
            exit()
        if response.lower() in ["m"]:
            launch_page(browser,url)
            print(
                f"{browser} browser closed, offering next search result (enter q if done)"
            )
            break
        if response.lower() == "q":
            exit()


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
    req = Request(f"https://duckduckgo.com/html/?q={url_string}", headers=headers)
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
