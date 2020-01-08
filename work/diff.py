import work.lcs as lcs

lcs_func = lcs.get_lcs

def get_subtractions(s, lcs):
    subtractions = []
    left = 0
    for c, i in enumerate(lcs):
        right = s.find(i, left)
        if left != right:
            subtraction = [left, s[left: right]]
            subtractions.append(subtraction)
        left = right + 1
    end = s[left : ]
    if end != "":
        ending_subtraction = [left, end]
        subtractions.append(ending_subtraction)
    return subtractions

def get_additions(s, lcs):
    additions = []
    left = 0
    for c, i in enumerate(lcs):
        right = s.find(i, left)
        if left != right:
            addition = [c, s[left : right]]
            additions.append(addition)
        left = right + 1
    end = s[left : ]
    if end != "":
        ending_addition = [len(lcs), end]
        additions.append(ending_addition)
    return additions

def get_diff(a, b):
    # Calculates the diff from a to b.
    lcs = lcs_func(a, b)
    subtractions = get_subtractions(a, lcs)
    additions = get_additions(b, lcs)
    return subtractions, additions