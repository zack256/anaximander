def forward_transform(s, subtractions, additions):
    middle = ""; current = 0
    for subtraction in subtractions:
        middle += s[current:subtraction[0]]
        current = len(subtraction[1]) + subtraction[0]
    middle += s[current:]
    end = ""; current = 0
    for addition in additions:
        end += middle[current:addition[0]] + addition[1]
        current = addition[0]
    end += middle[current:]
    return end

def backwards_transform(s, subtractions, additions):
    middle = ""; kept = taken = current = 0
    for subtraction in additions:
        middle += s[current:subtraction[0] + current - kept]
        kept = subtraction[0]; taken += len(subtraction[1])
        current = kept + taken
    middle += s[current:]
    end = ""; current = 0
    for addition in subtractions:
        add = addition[0] - len(end)
        end += middle[current:current + add] + addition[1]
        current += add
    end += middle[current:]
    return end