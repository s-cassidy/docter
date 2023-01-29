import yaml
import subprocess
import argparse
import re
from urllib.request import Request, urlopen


def main():
    args = get_arguments()
    config = load_config("test/test.yaml")
    check_keyword(args, config)
    search_str = build_search_string(args, config)
    search_result_page = ddg_search(search_str)
    results = [result for result in get_result_urls(search_result_page)]
    result_url, browser = select_result_and_browser(results, args, config)
    if result_url:
        launch_page(browser, result_url)


def check_keyword(args: argparse.Namespace, config: dict) -> None:
    keyword = args.keyword
    if keyword not in config['keywords']:
        print(f"{keyword} is not a keyword; performing a standard search with default settings")
        config['keywords'][keyword] = {'terms': [keyword],
                                       'sources': ['any']}
        config["sources"]["any"] = {'urlpattern': ''}


def select_result_and_browser(results: list,
                              args: argparse.Namespace,
                              config: dict) -> tuple:
    for result in results:
        if source := match_url_with_source(result, args.keyword, config):
            browser = select_browser(source, config)
            if accept_page_launch(result, browser):
                return result, browser
    else:
        print(f"No other likely results found from {args.keyword}"
              f" sources for {args.terms}."
              )
        return None, browser


def accept_page_launch(url: str, browser: str) -> tuple:
    while True:
        response = input(f"Go to {url}? (browser: {browser}) Y/n: ").lower()
        if response.lower() in ["no", "n"]:
            return False
        if response.lower() in ["y", "yes", ""]:
            return True


def select_browser(source: str, config: dict) -> str:
    default = config['defaultbrowser']
    return config['sources'][source].get('browser', default)


def build_search_string(cli_args: argparse.Namespace, config: dict) -> str:
    keyword = cli_args.keyword
    terms = cli_args.terms
    additional_terms = config['keywords'][keyword]['terms']
    search_str = '+'.join(additional_terms+terms.split())
    return search_str


def get_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("keyword",
                        help="configurable keyword to select sources")
    parser.add_argument("terms",
                        help="terms to search for in the selected sources")
    return parser.parse_args()


def match_url_with_source(url: str, keyword: str, config: dict) -> str:
    keyword_sources = config["keywords"][keyword]["sources"]
    for source in keyword_sources:
        try:
            pattern = config['sources'][source]['urlpattern']
        except KeyError:
            print(f"Warning: source {source} is not configured")
        if pattern in url:
            return source


def launch_page(browser: str, url: str, gui: bool = False) -> None:
    subprocess.run([browser, url])


def get_result_urls(results_html: str) -> str:
    for line in results_html.splitlines():
        exp = '(?:result__url.+)(http.+)"'
        match = re.search(exp, line)
        if match:
            yield match.group(1)


def ddg_search(url_string: str) -> str:
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X"
                             " 10_10_1) AppleWebKit/537.36 (KHTML, "
                             "like Gecko) Chrome/39.0.2171.95 Safari/537.36"
               }
    print(f"Searching for {url_string}")
    req = Request(
            f"https://duckduckgo.com/html/?q={url_string}",
            headers=headers
            )
    return urlopen(req).read().decode()


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf8") as f:
        try:
            config = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            print(exc)
    tidy_config(config)
    return config


def tidy_config(config: dict) -> None:
    for word, word_opts in config['keywords'].items():
        word_opts['terms'] = word_opts.get('terms', [word])
        for source in word_opts['sources']:
            if source not in config['sources']:
                print(f"{word} source {source} not properly configured")

if __name__ == "__main__":
    main()
