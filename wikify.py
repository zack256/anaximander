checkers = {
    "comments": ["<!--", "-->"],
    "brackets": ["[[", "]]"],
    "bolds" : ["!!", "!!"],
    "italics" : ["**", "**"]
}

def make_local_link(wiki, linked, display):
    return '<a href = "/wikis/{}/articles/{}/">{}</a>'.format(wiki.name, linked.replace(" ", "_"), display)

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





