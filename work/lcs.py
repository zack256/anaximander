# LCS = Longest Common Subsequence.
# The iteration method is most likely faster than the recursion one, so its the one that is used.

def lcs_table_using_iteration(a, b):
    m = len(a); n = len(b)
    l = [[0 for i in range(m + 1)]] + [[0] + [-1 for j in range(m)] for k in range(n)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if a[j - 1] == b[i - 1]:
                l[i][j] = l[i - 1][j - 1] + 1
            else:
                l[i][j] = max(l[i - 1][j], l[i][j - 1])
    return l

def lcs_table_using_recursion (a, b):
    m = len(a); n = len(b)
    if m == 0 or n == 0:
        return 0
    l = [[0 for i in range(m + 1)]] + [[0] + [-1 for j in range(m)] for k in range(n)]
    result = lcs_recursion_helper(a, b, l)
    return l

def lcs_recursion_helper (a, b, l):
    m = len(a); n = len(b)
    if l[n][m] == -1:
        if a[m - 1] == b[n - 1]:
            l[n][m] = 1 + lcs_recursion_helper(a[:m - 1], b[:n - 1], l)
        else:
            l[n][m] = max(lcs_recursion_helper(a, b[:n - 1], l), lcs_recursion_helper(a[:m - 1], b, l))
    return l[n][m]

def get_lcs(a, b, use_iter = True):
    func = lcs_table_using_iteration if use_iter else lcs_table_using_recursion
    l = func(a, b)
    m = len(a); n = len(b)
    i = m; j = n
    len_lcs = l[n][m]
    idx = len_lcs - 1
    lcs = [""] * len_lcs
    while i > 0 and j > 0:
        if a[i - 1] == b[j - 1]:
            lcs[idx] = a[i - 1]
            i -= 1; j -= 1
            idx -= 1
        elif l[j - 1][i] >= l[j][i - 1]:
            j -= 1
        else:
            i -= 1
    return "".join(lcs)