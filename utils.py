def next_version(current, change = 2):
    idx1 = current.find(".")
    idx2 = current.find(".", idx1 + 1)
    new = ""
    if change == 2: # patch. "1.2.3" -> "1.2.4"
        new = current[:idx2 + 1] + str(int(current[idx2 + 1:]) + 1)
    elif change == 1:   # minor. "1.2.3" -> "1.3.0"
        new = current[:idx1 + 1] + str(int(current[idx1 + 1:idx2]) + 1) + ".0"
    elif change == 0:   # major. "1.2.3" -> "2.0.0"
        new = str(int(current[:idx1]) + 1) + ".0.0"
    return new