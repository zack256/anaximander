import re

def check_valid_base(name, length, regex):
    return len(name) <= length and re.search(regex, name)

def check_if_valid_news_article_name(name):
    return check_valid_base(name, 255, r"^[a-z0-9-]+$")

def check_if_valid_news_tag_name(name):
    return check_valid_base(name, 40, r"^[a-z0-9-]+$")

def check_if_valid_wiki_article_name(name):
    return check_valid_base(name, 80, r"^[a-zA-Z0-9().,!~*\-[\]{}]+$")  # carefully planned out.

def check_if_valid_wiki_name(name):
    return check_valid_base(name, 80, r"^[a-zA-Z0-9\-_]+$")