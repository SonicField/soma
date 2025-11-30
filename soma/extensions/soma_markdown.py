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


def render_table(header, rows, alignment):
    """
    Render a markdown table with column-width-aware formatting.

    Args:
        header: List of header cell strings
        rows: List of row lists (each row is list of cell strings)
        alignment: List of alignment strings ("left", "centre", "right", None)
                   or None if no alignment specified

    Returns:
        String containing formatted markdown table
    """
    if not isinstance(header, list) or len(header) == 0:
        return ""

    num_cols = len(header)

    # Calculate column widths
    col_widths = [len(str(cell)) for cell in header]

    if isinstance(rows, list):
        for row in rows:
            if isinstance(row, list):
                for i, cell in enumerate(row):
                    if i < num_cols:
                        col_widths[i] = max(col_widths[i], len(str(cell)))

    result_parts = []

    # Build header row with padding
    result_parts.append("| ")
    header_cells = []
    for i, cell in enumerate(header):
        header_cells.append(str(cell).ljust(col_widths[i]))
    result_parts.append(" | ".join(header_cells))
    result_parts.append(" |\n")

    # Build separator row with alignment
    result_parts.append("|")
    has_alignment = isinstance(alignment, list) and len(alignment) > 0

    for i in range(num_cols):
        align = None
        if isinstance(alignment, list) and i < len(alignment):
            align = alignment[i]

        width = col_widths[i]

        if align == "left":
            # :------ (colon + width+1 dashes)
            result_parts.append(":" + "-" * (width + 1) + "|")
        elif align == "centre":
            # :---: (colon + width dashes + colon)
            result_parts.append(":" + "-" * width + ":|")
        elif align == "right":
            # -------: (width+1 dashes + colon)
            result_parts.append("-" * (width + 1) + ":|")
        else:
            # ------- (width+2 dashes for padding spaces)
            result_parts.append("-" * (width + 2) + "|")

    result_parts.append("\n")

    # Build data rows with padding
    if isinstance(rows, list):
        for row in rows:
            if isinstance(row, list):
                result_parts.append("| ")
                # Pad cells to column width
                cells = []
                for i in range(num_cols):
                    if i < len(row):
                        cells.append(str(row[i]).ljust(col_widths[i]))
                    else:
                        cells.append(" " * col_widths[i])
                result_parts.append(" | ".join(cells))
                result_parts.append(" |\n")

    result_parts.append("\n")
    return ''.join(result_parts)


def data_title_format(*items):
    """
    Format items with alternating bold (for data title pattern).

    Takes even number of items and bolds every other one (0, 2, 4...).
    Example: ('Name', 'Alice', 'Age', '30') -> '**Name** Alice **Age** 30'
    """
    # Filter out None (Void representation)
    items = [str(item) for item in items if item is not None]

    if len(items) % 2 != 0:
        raise ValueError(f"md.dt requires even number of items, got {len(items)}")

    formatted = []
    for i, item in enumerate(items):
        if i % 2 == 0:  # Even indices: 0, 2, 4... get bolded
            formatted.append(f"**{item}**")
        else:
            formatted.append(item)

    return " ".join(formatted)


def definition_list_format(*items):
    """
    Format items as definition list items (label: value pairs).

    Takes even number of items and formats as "**label**: value" pairs.
    Example: ('Name', 'Alice', 'Age', '30') -> ['**Name**: Alice', '**Age**: 30']
    """
    # Filter out None (Void representation)
    items = [str(item) for item in items if item is not None]

    if len(items) % 2 != 0:
        raise ValueError(f"md.dl requires even number of items, got {len(items)}")

    formatted = []
    for i in range(0, len(items), 2):
        label = items[i]
        value = items[i + 1]
        formatted.append(f"**{label}**: {value}")

    return formatted


def write_file(filename, content):
    """Write content to file."""
    with open(str(filename), 'w') as f:
        f.write(str(content))
    return None
