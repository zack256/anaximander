def wikify (text):
    html = ""
    for paragraph in text.split("\n"):
        if paragraph == "":
            html += "<br/>"
        else:
            html += "<p>" + paragraph + "</p>"
    return html