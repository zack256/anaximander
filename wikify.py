'''def wikify (text):
    html = ""
    for paragraph in text.split("\n"):
        if paragraph == "":
            html += "<br/>"
        else:
            html += "<p>" + paragraph + "</p>"
    return html'''
'''def wikify(text, wiki):
    html = ""
    z = 0
    len_text = len(text)
    while z < len_text:
        paragraph = ""
        zz = z
        brackets = 0
        while zz < len_text:
            char = text[zz]
            if char == "\n":
                break
            if char == "[":
                brackets += 1
                if brackets == 2:
                    fin = zz + 1
                    close_brackets = 0
                    recorded = ""
                    pipe_idx = None
                    left_open = True
                    brackets = 0
                    while True:
                        if fin >= len_text:
                            break
                        car = text[fin]
                        if car == "]":
                            close_brackets += 1
                            if close_brackets == 2:
                                if pipe_idx:
                                    article_name = recorded[:pipe_idx]
                                    link_text = recorded[pipe_idx + 1:]
                                else:
                                    article_name = link_text = recorded
                                html_link = '<a href = "/wikis/{}/articles/{}/">{}</a>'.format(wiki.name, article_name, link_text)
                                paragraph += html_link
                                zz = fin
                                left_open = False
                                break
                        elif car == "\n":   # link left open, incomplete.
                            break
                        else:
                            close_brackets = 0
                            recorded += car
                        if car == "|":
                            if pipe_idx == None:
                                pipe_idx = len(recorded) - 1
                        fin += 1
                    if left_open:
                        paragraph += "[[" + text[zz:fin]
                        zz = fin - 1
            else:
                if brackets == 1:
                    paragraph += "["
                brackets = 0
                paragraph += char
            zz += 1
        if brackets == 1:
            paragraph += "["
            brackets = 0
        if paragraph == "":
            html += "<br/>"
        else:
            html += "<p>" + paragraph + "</p>"
        z = zz + 1
    return html'''

checkers = {
    "comments": ["<!--", "-->"],
    "brackets": ["[[", "]]"],
    "bolds" : ["!!", "!!"],
    "italics" : ["**", "**"]
}

ARTICLE_ROOT_URL = "/wikis/placeholder/articles"

def make_local_link(wiki, linked, display):
    return '<a href = "/wikis/{}/articles/{}/">{}</a>'.format(wiki.name, linked, display)

def replace_with(string, what, wiki = None):
    if what == "comments":
        return ""
    elif what == "brackets":
        no_brackets = string[2:-2]
        pipe = no_brackets.find("|")
        if pipe == -1:
            linked = display = no_brackets
        else:
            linked = no_brackets[:pipe]
            display = no_brackets[pipe+1:]
        return make_local_link(wiki, linked, display)
    elif what == "bolds":
        no_bolds = string[2:-2]
        return "<b>" + no_bolds + "</b>"
    elif what == "italics":
        no_italics = string[2:-2]
        return "<i>" + no_italics + "</i>"

def replace_function(paragraphs, what, wiki = None):
    open_str, close_str = checkers[what]
    new_paragraphs = []
    for paragraph in paragraphs:
        new_paragraph = ""
        is_open = False
        last_open_idx = last_close_end = last_close_idx = last_open_body = None
        while True:
            if not is_open:
                last_open_idx = paragraph.find(open_str, last_close_end)
                if last_open_idx == -1:
                    break
                new_paragraph += paragraph[last_close_end:last_open_idx]
                is_open = True
                last_open_body = last_open_idx + len(open_str)
            else:
                last_close_idx = paragraph.find(close_str, last_open_body)
                if last_close_idx == -1:
                    last_close_end = last_open_idx
                    break
                is_open = False
                last_close_end = last_close_idx + len(close_str)
                new_paragraph += replace_with(paragraph[last_open_idx:last_close_end], what, wiki = wiki)
        if last_close_end:
            new_paragraph += paragraph[last_close_end:]
        else:
            new_paragraph += paragraph
        new_paragraphs.append(new_paragraph)
    return new_paragraphs


def simple_wikify(text, wiki):
    paragraphs = text.split("\n")
    paragraphs = replace_function(paragraphs, "comments")
    paragraphs = replace_function(paragraphs, "brackets", wiki = wiki)
    paragraphs = replace_function(paragraphs, "bolds")
    paragraphs = replace_function(paragraphs, "italics")
    html = ""
    for paragraph in paragraphs:
        if paragraph == "":
            html += "<br/>"
        else:
            html += "<p>" + paragraph + "</p>"
    return html





