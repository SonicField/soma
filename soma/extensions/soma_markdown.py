"""Python FFI helpers for SOMA markdown library."""


def drain_and_join(separator, *items):
    """
    Join items with separator.

    Called via >use.python.call which already drains AL until Void
    and reverses items to natural order.
    """
    # Filter out None (Void representation)
    items = [str(item) for item in items if item is not None]
    return str(separator).join(items)


def string_concat(s1, s2):
    """Concatenate two strings."""
    return str(s1) + str(s2)


def string_concat_all(*items):
    """Concatenate all arguments into a single string."""
    return ''.join(str(item) for item in items if item is not None)


def string_join(separator, *items):
    """Join items with separator."""
    # Filter out None (Void representation)
    items = [str(item) for item in items if item is not None]
    return str(separator).join(items)


def string_join_list(separator, items):
    """Join a list of items with separator."""
    if not isinstance(items, list):
        return ""
    return str(separator).join(str(item) for item in items)


def string_repeat(s, count):
    """Repeat string N times."""
    return str(s) * int(count)


def list_new():
    """Create empty list."""
    return []


def list_append(lst, item):
    """Append item to list, return new list."""
    if not isinstance(lst, list):
        lst = []
    return lst + [item]


def list_length(lst):
    """Get list length."""
    if not isinstance(lst, list):
        return 0
    return len(lst)


def list_get(lst, index):
    """Get item at index."""
    if not isinstance(lst, list):
        raise TypeError("Not a list")
    return lst[int(index)]


def list_is_empty(lst):
    """Check if list is empty."""
    if not isinstance(lst, list):
        return True
    return len(lst) == 0


def stack_push(stack, item):
    """Push item onto stack (returns new stack)."""
    if not isinstance(stack, list):
        stack = []
    return stack + [item]


def stack_pop(stack):
    """Pop item from stack. Returns (item, new_stack) or (None, stack) if empty."""
    if not isinstance(stack, list) or len(stack) == 0:
        return None, stack
    return stack[-1], stack[:-1]


def stack_is_empty(stack):
    """Check if stack is empty."""
    if not isinstance(stack, list):
        return True
    return len(stack) == 0


def to_string(value):
    """Convert value to string."""
    return str(value)


def is_list(value):
    """Check if value is a list."""
    return isinstance(value, list)


def link_format(left_bracket, text, middle, url):
    """Format a markdown link: [text](url)"""
    return f"{left_bracket}{text}{middle}{url})"


def write_file(filename, content):
    """Write content to file."""
    with open(str(filename), 'w') as f:
        f.write(str(content))
    return None
