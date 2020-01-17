'''
def wikify (text):
    html = ""
    for paragraph in text.split("\n"):
        if paragraph == "":
            html += "<br/>"
        else:
            html += "<p>" + paragraph + "</p>"
    return html
'''

def wikify(text, wiki):
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
    return html






