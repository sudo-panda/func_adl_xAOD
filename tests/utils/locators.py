def find_line_with(text, lines, throw_if_not_found=True):
    'Find the first line with the text. Return its index, zero based'
    for index, l in enumerate(lines):
        if text in l:
            return index
    if throw_if_not_found:
        raise Exception("Unable to find text '{0}' in any lines in text output".format(text))
    return -1


def find_line_numbers_with(text, lines):
    return [index for index, l in enumerate(lines) if text in l]


def find_next_closing_bracket(lines):
    'Find the next closing bracket. If there is an opening one, then track through to the matching closing one.'
    depth = 0
    for index, l in enumerate(lines):
        if l.strip() == "{":
            depth += 1
        if l.strip() == "}":
            depth -= 1
            if depth < 0:
                return index
    return -1


def find_open_blocks(lines):
    'Search through and record the lines before a {. If a { is closed, then remove that lines'
    stack = []
    last_line_seen = 'xxx-xxx-xxx'
    for ln in lines:
        if ln.strip() == '{':
            stack += [last_line_seen]
        elif ln.strip() == '}':
            stack = stack[:-1]
        last_line_seen = ln
    return stack
