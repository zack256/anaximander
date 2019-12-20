import re
import string

def check_valid_base(name, max_length, regex, min_length = 1):
    return len(name) <= max_length and len(name) >= min_length and re.search(regex, name)

def check_if_valid_news_article_name(name):
    return check_valid_base(name, 255, r"^[a-z0-9-]+$")

def check_if_valid_news_tag_name(name):
    return check_valid_base(name, 40, r"^[a-z0-9-]+$")

def check_if_valid_wiki_article_name(name):
    return name[0] != string.ascii_lowercase + "_" and check_valid_base(name, 80, r"^([_]?[a-zA-Z0-9().,!~*\-[\]{}])+$")    # Article name cannot start with a lowercase letter or a space (underscore).

def check_if_valid_wiki_name(name):
    return check_valid_base(name, 80, r"^[a-z0-9\-_]+$")