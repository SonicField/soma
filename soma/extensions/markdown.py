"""
Pure SOMA Markdown Extension

Provides markdown generation via state machine pattern.
All logic implemented in pure SOMA using Python FFI primitives.
"""


def drain_and_join_builtin(vm):
    """
    >md.drain.join builtin - Drain AL until Void, join with separator.

    AL before: [void, item1, item2, ..., itemN, separator, ...]
    AL after: ["item1 item2 ... itemN", ...]
    """
    from soma.vm import Void, VoidSingleton

    # Pop separator
    if len(vm.al) < 1:
        raise RuntimeError("AL underflow: md.drain.join requires separator")
    separator = vm.al.pop()

    # Pop items until Void
    items = []
    while True:
        if len(vm.al) < 1:
            raise RuntimeError("AL underflow: md.drain.join requires Void terminator")

        item = vm.al.pop()

        if isinstance(item, VoidSingleton):
            break

        items.append(str(item))

    # Items are in reverse order (LIFO), so reverse them
    items.reverse()

    # Join with separator
    result = str(separator).join(items)

    # Push Void sentinel back first, then result (LIFO order)
    vm.al.append(Void)
    vm.al.append(result)


def drain_and_format_ul_builtin(vm):
    """
    >use.md.drain.ul builtin - Drain AL, check nesting stack, format as unordered list.

    AL before: [void, item1, item2, ..., itemN, depth, stack, ...]
    AL after: ["- item1\n...\n\n", new_depth, new_stack, void, ...]
    """
    from soma.vm import Void, VoidSingleton

    # Pop stack and depth
    if len(vm.al) < 2:
        raise RuntimeError("AL underflow: md.drain.ul requires stack and depth")
    stack = vm.al.pop()
    depth = int(vm.al.pop())

    # Pop items until Void
    items = []
    while True:
        if len(vm.al) < 1:
            raise RuntimeError("AL underflow: md.drain.ul requires Void terminator")

        item = vm.al.pop()

        if isinstance(item, VoidSingleton):
            break

        items.append(str(item))

    # Items are in reverse order (LIFO), so reverse them
    items.reverse()

    # Build result
    result_parts = []

    # Check if we have a parent context on the stack
    if isinstance(stack, list) and len(stack) > 0:
        parent_ctx = stack[-1]
        parent_depth = parent_ctx['depth']

        if depth > parent_depth:
            # We're a nested formatter - render only our items, add to parent context
            indent = "  " * depth
            for item in items:
                result_parts.append(f"{indent}- {item}\n")

            nested_result = ''.join(result_parts)

            # Update parent context with nested text
            parent_ctx['nested_text'] = parent_ctx.get('nested_text', '') + nested_result

            # Don't pop stack, just update it
            new_stack = stack
            new_depth = parent_depth  # Return to parent depth

            # Return empty string - text already added to parent context
            # Don't add blank line for nested content
            result = ""
        else:
            # We're the outer formatter - pop ALL parent contexts at our depth and render everything
            new_stack = []
            contexts_to_render = []

            # Pop all contexts at parent_depth
            for ctx in stack:
                if ctx['depth'] == parent_depth:
                    contexts_to_render.append(ctx)
                else:
                    new_stack.append(ctx)

            # Render all parent contexts first
            parent_indent = "  " * parent_depth
            for ctx in contexts_to_render:
                parent_items = ctx['items']
                nested_text = ctx.get('nested_text', '')

                # Render parent items using UL format
                for item in parent_items:
                    result_parts.append(f"{parent_indent}- {item}\n")

                # Insert nested text
                if nested_text:
                    result_parts.append(nested_text)

            # Render current items at same depth
            for item in items:
                result_parts.append(f"{parent_indent}- {item}\n")

            result = ''.join(result_parts)

            # Set new depth based on remaining stack
            if new_stack:
                # Still nested - add result to parent context and return empty string
                new_stack[-1]['nested_text'] = new_stack[-1].get('nested_text', '') + result
                result = ""  # Don't add to document yet
                new_depth = new_stack[-1]['depth']
            else:
                # Top level - add to document
                new_depth = 0
                # Add final blank line only at depth 0
                if new_depth == 0:
                    result += "\n"
    else:
        # No nesting - normal list
        new_stack = []
        indent = "  " * depth
        for item in items:
            result_parts.append(f"{indent}- {item}\n")
        new_depth = depth
        result = ''.join(result_parts)

        # Add final blank line only at depth 0
        if new_depth == 0:
            result += "\n"

    # Push Void sentinel back first, then new stack, then new_depth, then result (LIFO order)
    vm.al.append(Void)
    vm.al.append(new_stack)
    vm.al.append(new_depth)
    vm.al.append(result)


def drain_and_format_ol_builtin(vm):
    """
    >use.md.drain.ol builtin - Drain AL, check nesting stack, format as ordered list.

    AL before: [void, item1, item2, ..., itemN, depth, stack, ...]
    AL after: ["1. item1\n...\n\n", new_depth, new_stack, void, ...]
    """
    from soma.vm import Void, VoidSingleton

    # Pop stack and depth
    if len(vm.al) < 2:
        raise RuntimeError("AL underflow: md.drain.ol requires stack and depth")
    stack = vm.al.pop()
    depth = int(vm.al.pop())

    # Pop items until Void
    items = []
    while True:
        if len(vm.al) < 1:
            raise RuntimeError("AL underflow: md.drain.ol requires Void terminator")

        item = vm.al.pop()

        if isinstance(item, VoidSingleton):
            break

        items.append(str(item))

    # Items are in reverse order (LIFO), so reverse them
    items.reverse()

    # Build result
    result_parts = []

    # Check if we have a parent context on the stack
    if isinstance(stack, list) and len(stack) > 0:
        parent_ctx = stack[-1]
        parent_depth = parent_ctx['depth']

        if depth > parent_depth:
            # We're a nested formatter - render only our items, add to parent context
            indent = "  " * depth
            counter = 1
            for item in items:
                result_parts.append(f"{indent}{counter}. {item}\n")
                counter += 1

            nested_result = ''.join(result_parts)

            # Update parent context with nested text
            parent_ctx['nested_text'] = parent_ctx.get('nested_text', '') + nested_result

            # Don't pop stack, just update it
            new_stack = stack
            new_depth = parent_depth  # Return to parent depth

            # Return empty string - text already added to parent context
            # Don't add blank line for nested content
            result = ""
        else:
            # We're the outer formatter - pop ALL parent contexts at our depth and render everything
            new_stack = []
            contexts_to_render = []

            # Pop all contexts at parent_depth
            for ctx in stack:
                if ctx['depth'] == parent_depth:
                    contexts_to_render.append(ctx)
                else:
                    new_stack.append(ctx)

            # Render all parent contexts first
            parent_indent = "  " * parent_depth
            counter = 1
            for ctx in contexts_to_render:
                parent_items = ctx['items']
                nested_text = ctx.get('nested_text', '')

                # Render parent items using OL format
                for item in parent_items:
                    result_parts.append(f"{parent_indent}{counter}. {item}\n")
                    counter += 1

                # Insert nested text
                if nested_text:
                    result_parts.append(nested_text)

            # Render current items at same depth (continue counter)
            for item in items:
                result_parts.append(f"{parent_indent}{counter}. {item}\n")
                counter += 1

            result = ''.join(result_parts)

            # Set new depth based on remaining stack
            if new_stack:
                # Still nested - add result to parent context and return empty string
                new_stack[-1]['nested_text'] = new_stack[-1].get('nested_text', '') + result
                result = ""  # Don't add to document yet
                new_depth = new_stack[-1]['depth']
            else:
                # Top level - add to document
                new_depth = 0
                # Add final blank line only at depth 0
                if new_depth == 0:
                    result += "\n"
    else:
        # No nesting - normal list
        new_stack = []
        indent = "  " * depth
        counter = 1
        for item in items:
            result_parts.append(f"{indent}{counter}. {item}\n")
            counter += 1
        new_depth = depth
        result = ''.join(result_parts)

        # Add final blank line only at depth 0
        if new_depth == 0:
            result += "\n"

    # Push Void sentinel back first, then new stack, then new_depth, then result (LIFO order)
    vm.al.append(Void)
    vm.al.append(new_stack)
    vm.al.append(new_depth)
    vm.al.append(result)


def drain_and_format_paragraphs_builtin(vm):
    """
    >use.md.drain.p builtin - Drain AL until Void, format each string as a separate paragraph.

    AL before: [void, item1, item2, ..., itemN, ...]
    AL after: ["item1\n\nitem2\n\n...\n\n", void, ...]

    Each string becomes its own paragraph with double newline suffix.
    """
    from soma.vm import Void, VoidSingleton

    # Pop items until Void
    items = []
    while True:
        if len(vm.al) < 1:
            raise RuntimeError("AL underflow: md.drain.p requires Void terminator")

        item = vm.al.pop()

        if isinstance(item, VoidSingleton):
            break

        items.append(str(item))

    # Items are in reverse order (LIFO), so reverse them
    items.reverse()

    # Format each item as a separate paragraph
    result_parts = []
    for item in items:
        result_parts.append(f"{item}\n\n")

    result = ''.join(result_parts)

    # Push Void sentinel back first, then result (LIFO order)
    vm.al.append(Void)
    vm.al.append(result)


def drain_and_format_blockquote_builtin(vm):
    """
    >use.md.drain.q builtin - Drain AL until Void, format as blockquote.

    AL before: [void, item1, item2, ..., itemN, ...]
    AL after: ["> item1\n> item2\n...\n\n", void, ...]

    Each string becomes a blockquote line prefixed with "> ".
    """
    from soma.vm import Void, VoidSingleton

    # Pop items until Void
    items = []
    while True:
        if len(vm.al) < 1:
            raise RuntimeError("AL underflow: md.drain.q requires Void terminator")

        item = vm.al.pop()

        if isinstance(item, VoidSingleton):
            break

        items.append(str(item))

    # Items are in reverse order (LIFO), so reverse them
    items.reverse()

    # Format each item as a blockquote line
    result_parts = []
    for item in items:
        result_parts.append(f"> {item}\n")

    result = ''.join(result_parts)

    # Add final blank line
    result += "\n"

    # Push Void sentinel back first, then result (LIFO order)
    vm.al.append(Void)
    vm.al.append(result)


def drain_and_format_code_block_builtin(vm):
    """
    >use.md.drain.code builtin - Drain AL until Void, format as code block.

    AL before: [void, line1, line2, ..., lineN, language, ...]
    AL after: ["```lang\nline1\nline2\n...\n```\n\n", void, ...]

    Language can be Nil or empty string for no language specification.
    """
    from soma.vm import Void, VoidSingleton, NilSingleton

    # Pop language parameter
    if len(vm.al) < 1:
        raise RuntimeError("AL underflow: md.code requires language parameter")
    language = vm.al.pop()

    # Check if language is Nil or empty
    is_nil = isinstance(language, NilSingleton)
    is_empty = (not is_nil) and (str(language) == "")
    has_language = not (is_nil or is_empty)

    # Pop lines until Void
    lines = []
    while True:
        if len(vm.al) < 1:
            raise RuntimeError("AL underflow: md.code requires Void terminator")

        item = vm.al.pop()

        if isinstance(item, VoidSingleton):
            break

        lines.append(str(item))

    # Lines are in reverse order (LIFO), so reverse them
    lines.reverse()

    # Build code block
    result_parts = []

    # Opening triple backticks with optional language
    if has_language:
        result_parts.append(f"```{language}\n")
    else:
        result_parts.append("```\n")

    # Add each line
    for line in lines:
        result_parts.append(f"{line}\n")

    # Closing triple backticks
    result_parts.append("```\n\n")

    result = ''.join(result_parts)

    # Push Void sentinel back first, then result (LIFO order)
    vm.al.append(Void)
    vm.al.append(result)


def nest_builtin(vm):
    """
    >use.md.nest builtin - Push current items onto nesting stack and increase depth.

    AL before: [void, item1, item2, ..., itemN, ...]
    AL after: [void, ...]

    Side effects: Pushes context onto md.state.stack, increases md.state.depth
    """
    from soma.vm import Void, VoidSingleton

    # Pop items until Void
    items = []
    while True:
        if len(vm.al) < 1:
            raise RuntimeError("AL underflow: md.nest requires Void terminator")

        item = vm.al.pop()

        if isinstance(item, VoidSingleton):
            break

        items.append(str(item))

    # Items are in reverse order (LIFO), so reverse them
    items.reverse()

    # Get current depth and stack
    current_depth = vm.store.read_value(['md', 'state', 'depth'])
    current_stack = vm.store.read_value(['md', 'state', 'stack'])

    # Create context for this level
    context = {'items': items, 'depth': current_depth}

    # Push context onto stack
    if not isinstance(current_stack, list):
        current_stack = []
    new_stack = current_stack + [context]
    vm.store.write_value(['md', 'state', 'stack'], new_stack)

    # Increase depth for nested content
    vm.store.write_value(['md', 'state', 'depth'], current_depth + 1)

    # Push Void back
    vm.al.append(Void)


def drain_and_collect_cells_builtin(vm):
    """
    >use.md.table.drain.cells builtin - Drain AL until Void, return items as list.

    AL before: [void, item1, item2, ..., itemN, ...]
    AL after: [[item1, item2, ..., itemN], void, ...]
    """
    from soma.vm import Void, VoidSingleton

    # Pop items until Void
    items = []
    while True:
        if len(vm.al) < 1:
            raise RuntimeError("AL underflow: table.drain.cells requires Void terminator")

        item = vm.al.pop()

        if isinstance(item, VoidSingleton):
            break

        items.append(str(item))

    # Items are in reverse order (LIFO), so reverse them
    items.reverse()

    # Push Void back first, then the list
    vm.al.append(Void)
    vm.al.append(items)


def drain_and_format_data_title_builtin(vm):
    """
    >use.md.drain.dt builtin - Drain AL until Void, format with alternating bold.

    AL before: [void, item1, item2, ..., itemN, ...]
    AL after: ["**item1** item2 **item3** item4 ...", void, ...]

    Requires even number of items.
    """
    from soma.vm import Void, VoidSingleton
    from soma.extensions.soma_markdown import data_title_format

    # Pop items until Void
    items = []
    while True:
        if len(vm.al) < 1:
            raise RuntimeError("AL underflow: md.dt requires Void terminator")

        item = vm.al.pop()

        if isinstance(item, VoidSingleton):
            break

        items.append(item)

    # Items are in reverse order (LIFO), so reverse them
    items.reverse()

    # Format with alternating bold
    result = data_title_format(*items)

    # Push Void sentinel back first, then result (LIFO order)
    vm.al.append(Void)
    vm.al.append(result)


def drain_and_format_definition_list_builtin(vm):
    """
    >use.md.drain.dl builtin - Drain AL until Void, format as definition list items.

    AL before: [void, label1, value1, label2, value2, ..., ...]
    AL after: ["**label1**: value1", "**label2**: value2", ..., void, ...]

    Transforms pairs into separate items ready for list formatters.
    Requires even number of items.
    """
    from soma.vm import Void, VoidSingleton
    from soma.extensions.soma_markdown import definition_list_format

    # Pop items until Void
    items = []
    while True:
        if len(vm.al) < 1:
            raise RuntimeError("AL underflow: md.dl requires Void terminator")

        item = vm.al.pop()

        if isinstance(item, VoidSingleton):
            break

        items.append(item)

    # Items are in reverse order (LIFO), so reverse them
    items.reverse()

    # Format as definition list items (returns list of formatted strings)
    formatted_items = definition_list_format(*items)

    # Push Void sentinel back first, then all formatted items (LIFO order)
    vm.al.append(Void)
    for formatted_item in formatted_items:
        vm.al.append(formatted_item)


def register(vm):
    """Register markdown builtins."""
    # Register drain_and_join as a builtin under use.* namespace
    vm.register_extension_builtin('use.md.drain.join', drain_and_join_builtin)
    vm.register_extension_builtin('use.md.drain.ul', drain_and_format_ul_builtin)
    vm.register_extension_builtin('use.md.drain.ol', drain_and_format_ol_builtin)
    vm.register_extension_builtin('use.md.drain.p', drain_and_format_paragraphs_builtin)
    vm.register_extension_builtin('use.md.drain.q', drain_and_format_blockquote_builtin)
    vm.register_extension_builtin('use.md.drain.code', drain_and_format_code_block_builtin)
    vm.register_extension_builtin('use.md.nest', nest_builtin)
    vm.register_extension_builtin('use.md.table.drain.cells', drain_and_collect_cells_builtin)
    vm.register_extension_builtin('use.md.drain.dt', drain_and_format_data_title_builtin)
    vm.register_extension_builtin('use.md.drain.dl', drain_and_format_definition_list_builtin)


def get_soma_setup():
    """Return SOMA code implementing markdown."""
    import os
    soma_file = os.path.join(os.path.dirname(__file__), 'markdown.soma')
    with open(soma_file, 'r') as f:
        return f.read()
