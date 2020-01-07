def wikify (text, version):
    print([versions, version, versions[version]])
    return versions[version](text)

def wkf_0_1_0 (text):
    #if text == "":
    #    return text
    #return "<p>" + "</p>\n<p>".join(text.split("\n")) + "</p>"
    html = ""
    for paragraph in text.split("\n"):
        if paragraph == "":
            html += "<br/>"
        else:
            html += "<p>" + paragraph + "</p>"
    return html

versions = {
    "0.1.0" : wkf_0_1_0,
    }