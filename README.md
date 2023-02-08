# DocTer 

*A cure-all script for finding and reading online documentation from the terminal*

## Introduction

### The Problem

If you work primarily in the terminal, sometimes the man pages aren't enough. Looking for documentation in a GUI browser breaks your flow. On the other hand, terminal-based browsers have clunky interfaces for navigating between pages and finding what you are looking for. Moreover, terminal-based browsers don't always format pages too well.

### The Solution 

DocTer is a simple script to quickly search for online documentation from the terminal and load the page in a suitable TUI or GUI browser of your choice. The pain of navigation is gone - the all that's left is to scroll the page.

DocTer's configuration allows you filter your search to specific sites, so you're probably only a few keystrokes away from the exact page you want. Moreover, you can configure each site to open in the most suitable browser.

#### Benefits:

- Configurable (using TOML),
- flexible, and
- lightweight; one script with no dependencies.

## Configuration and key concepts

DocTer has two key concepts.

- *Sources*: Sources are websites that you find useful for documentation certain topics.
- *Keywords*: The first argument provided to docter is called a keyword. Keywords serve two roles. They map to a collection of sources. Also, they can be expanded into multiple search terms.

### Minimal Example

Let's look at a minimal configuration and an example search.
```
defaultbrowser = "w3m"

[sources]
[sources.pythondocs]
urlpattern = "docs.python.org"
browser = "elinks"

[sources.pypi]
urlpattern = "pypi.org"
browser = "elinks"

[sources.cheat]
urlpattern = "cheat.sh/"

[sources.readthedocs]
urlpattern = "readthedocs.io"


[keywords]
[keywords.python]
sources = [ "pythondocs", "readthedocs", "pypi" ]
terms = "python doc"
```

The sources listed in the `[keywords.python]` table should correspond to one of the sources in the `[sources]` table. We now run
```
$ docter python requests
```
First, as `python` is a keyword listed in the `[keywords]` table, it expands to search for the terms `python doc requests`. We then are asked
```
Go to https://requests.readthedocs.io/? (browser: w3m) Y/n:
```
This is because `readthedocs` is listed as a source for Python documentation. Results from the search that do not include `docs.python.org`, `pypi.org`, or `readthedocs.io` are not offered - so anything from `cheat.sh` will not be included either.

### Example 2

There are lots of handy cheatsheats at [learnxinyminutes.com](https://learnxinyminutes.com). The TUI browser `links2` formats the pages from that site particularly nicely. So my configuration file might include the following:
```
defaultbrowser = "w3m"

[sources]
[sources.xinymins]
urlpattern = "learnxinyminutes.com/"
browser = "links2"


[keywords]
[keywords.xy]
sources = [ "xinymins" ]
terms = "learn x in y minutes"
```

Now
```
$ docter xy tmux
```

searches for `learn x in y minutes tmux`, and offers

```
Go to https://learnxinyminutes.com/docs/tmux/? (browser: links2) Y/n:
```

In other words, the default browser is overridden because the source `xinymins` has a browser set.

### Configuration

It is recommended to copy the minimal example configuration and replace it with your own settings.

#### Global settings

The following global settings should be set at the beginning of your configuration file

```
defaultbrowser = "w3m" # required
defaultgui = "firefox" # optional but recommended
always_lucky = false # optional but recommended
```

The `defaultbrowser` and `defaultgui` values should be commands to launch that browser from the shell. If `always_lucky` is set, DocTer will automatically open the first matching result in the preferred browser without asking for confirmation.

#### Sources

A source has a name, a pattern to match in the URL, and optionally a preferred browser.

```
[sources.<NAME>]
urlpattern = "<pattern contained in URL for this source>"
browser = "<command to launch a web browser>"
```

#### Keywords

A keyword has associated to it an array of sources, and a string of search terms that the keyword will expand to. All fields are required.

```
[keywords.<KEYWORD>]
sources = ["<SOURCE1>", "<SOURCE2>"]
terms = "<search string here>"
```

## More usage notes

### If no keyword is given

If the first argument is not a keyword, it is converted a search term. DocTer will just search for the terms provided and will offer results from any website in the default browser.

### Optional arguments

- `-b` can be used to override the preferred browser, for example `docter -b lynx python date time` will open Python's `datetime` documentation in the `lynx` browser.
- `-g` will replace the default browser (which should usually be a TUI browser) with the `defaultgui` browser.
- `-l` for "lucky" mode. Open the first matching result without asking confirmation.
