"""
Pure SOMA Markdown Extension

Provides markdown generation via state machine pattern.
All logic implemented in pure SOMA using Python FFI primitives.
"""

from soma.extensions.markdown_emitter import MarkdownEmitter


class OliPlaceholder:
    """Opaque placeholder for ordered list items accumulated via >md.oli"""
    def __init__(self, index):
        self.index = index

    def __repr__(self):
        return f"OliPlaceholder({self.index})"


class UliPlaceholder:
    """Opaque placeholder for unordered list items accumulated via >md.uli"""
    def __init__(self, index):
        self.index = index

    def __repr__(self):
        return f"UliPlaceholder({self.index})"


class DliPlaceholder:
    """Opaque placeholder for definition list items accumulated via >md.dli"""
    def __init__(self, index):
        self.index = index

    def __repr__(self):
        return f"DliPlaceholder({self.index})"


def is_placeholder(obj):
    """Check if object is any kind of list item placeholder."""
    return isinstance(obj, (OliPlaceholder, UliPlaceholder, DliPlaceholder))


def replace_placeholder(item, accumulator):
    """
    Replace placeholder with accumulated value if it's a placeholder.
    Otherwise return the item as-is (converted to string).
    """
    if isinstance(item, (OliPlaceholder, UliPlaceholder, DliPlaceholder)):
        if 0 <= item.index < len(accumulator):
            return accumulator[item.index]
        else:
            raise RuntimeError(f"Placeholder index {item.index} out of range (accumulator has {len(accumulator)} items)")
    return str(item)


def validate_no_placeholders(items, operation_name):
    """
    Validate that no placeholders exist in items.
    Raises RuntimeError if any placeholder is found.
    """
    for i, item in enumerate(items):
        if is_placeholder(item):
            placeholder_type = "ordered" if isinstance(item, OliPlaceholder) else "unordered"
            list_op = ">md.ol" if isinstance(item, OliPlaceholder) else ">md.ul"

            # Provide context-specific hints
            hint = ""
            if operation_name in [">md.dl", ">md.dt"]:
                hint = (
                    f"\n\nNote: {operation_name} processes items in pairs. "
                    f"Placeholders cannot be part of pairs. "
                    f"Consume all placeholders with {list_op} BEFORE calling {operation_name}, "
                    f"or ensure placeholders are below the Void sentinel (not in the items being paired)."
                )

            raise RuntimeError(
                f"{operation_name} encountered {type(item).__name__} at position {i}. "
                f"Placeholders from >md.oli/uli must be consumed by >md.ol/ul before {operation_name}. "
                f"Did you forget to call {list_op}?{hint}"
            )


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

    # Pop items until Void or placeholder
    items = []
    hit_placeholder = False
    while True:
        if len(vm.al) < 1:
            raise RuntimeError("AL underflow: md.drain.join requires Void terminator")

        item = vm.al.pop()

        if isinstance(item, VoidSingleton):
            break

        # Stop if we hit a placeholder from oli/uli calls
        if is_placeholder(item):
            # Put it back and stop draining
            vm.al.append(item)
            hit_placeholder = True
            break

        # Validate that item is a string (text concatenation only accepts strings)
        if not isinstance(item, str):
            raise TypeError(
                f"Text concatenation (>md.t) requires string items, got {type(item).__name__}: {item!r}\n"
                f"Hint: If you want to use a literal operator like '-', wrap it in parentheses: (-)\n"
                f"      Example: (text ) (-) ( more text) >md.t"
            )

        items.append(item)

    # Items are in reverse order (LIFO), so reverse them
    items.reverse()

    # Get emitter from state and use its join/concat methods
    emitter = vm.store.read_value(['md', 'state', 'emitter'])

    # Use emitter's concat or join method to handle escaping and tagging
    if str(separator) == "":
        # Empty separator means concatenation (implements >md.t)
        result = emitter.concat(items)
    else:
        # Non-empty separator means joining
        result = emitter.join(items, str(separator))

    # Push Void back if we hit it, otherwise we stopped at placeholder (which is already back)
    if not hit_placeholder:
        vm.al.append(Void)

    # Push result
    vm.al.append(result)


def drain_and_format_ul_builtin(vm):
    """
    >use.md.drain.ul builtin - Drain AL, check nesting stack, format as unordered list.

    AL before: [void, item1, item2, ..., itemN, depth, stack, accumulator, emitter, ...]
    AL after: ["- item1\n...\n\n", new_depth, new_stack, void, ...]

    Items may include placeholders like "__MD_ITEM_PLACEHOLDER_N__" which are
    replaced with accumulated items from the accumulator list.
    Uses emitter.unordered_list() to format.
    """
    from soma.vm import Void, VoidSingleton

    # Pop emitter
    if len(vm.al) < 1:
        raise RuntimeError("AL underflow: md.drain.ul requires emitter")
    emitter = vm.al.pop()

    # Pop accumulator, stack and depth
    if len(vm.al) < 3:
        raise RuntimeError("AL underflow: md.drain.ul requires accumulator, stack and depth")
    accumulator = vm.al.pop()
    stack = vm.al.pop()
    depth = int(vm.al.pop())

    # Ensure accumulator is a list
    if not isinstance(accumulator, list):
        accumulator = []

    # Pop items until Void
    items = []
    while True:
        if len(vm.al) < 1:
            raise RuntimeError("AL underflow: md.drain.ul requires Void terminator")

        item = vm.al.pop()

        if isinstance(item, VoidSingleton):
            break

        items.append(item)  # Keep as object for now

    # Items are in reverse order (LIFO), so reverse them
    items.reverse()

    # Replace placeholders with accumulated items and validate types
    for i in range(len(items)):
        item = items[i]
        if isinstance(item, UliPlaceholder):
            # Correct placeholder type - replace with accumulated item
            if 0 <= item.index < len(accumulator):
                items[i] = accumulator[item.index]
            else:
                raise RuntimeError(f"UliPlaceholder index {item.index} out of range (accumulator has {len(accumulator)} items)")
        elif isinstance(item, OliPlaceholder):
            # Wrong placeholder type!
            raise RuntimeError(
                f">md.ul encountered OliPlaceholder (from >md.oli). "
                f"Use >md.ol for ordered list items, not >md.ul. "
                f"Did you mean to use >md.ol instead of >md.ul?"
            )
        elif isinstance(item, DliPlaceholder):
            # Wrong placeholder type!
            raise RuntimeError(
                f">md.ul encountered DliPlaceholder (from >md.dli). "
                f"Use >md.dul for definition list items, not >md.ul. "
                f"Did you mean to use >md.dul instead of >md.ul?"
            )
        else:
            # Regular item - convert to string
            items[i] = str(item)

    # Build result - use emitter for simple non-nested lists
    result_parts = []

    # Check if we have a parent context on the stack
    if isinstance(stack, list) and len(stack) > 0:
        parent_ctx = stack[-1]
        parent_depth = parent_ctx['depth']

        if depth > parent_depth:
            # We're a nested formatter - render only our items, add to parent context
            if emitter.can_concat_lists():
                # HTML: Use proper nested <ul> structure
                nested_result = emitter.unordered_list(items, depth)
            else:
                # Markdown: Use manual formatting to preserve exact spacing
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

            if emitter.can_concat_lists():
                # HTML: Build proper nested structure with nested lists inside <li> tags
                all_items = []

                # Process parent contexts
                for ctx in contexts_to_render:
                    parent_items = ctx['items']
                    nested_text = ctx.get('nested_text', '')
                    parent_accumulator = ctx.get('uli_accumulator', [])

                    for item in parent_items:
                        item_text = replace_placeholder(item, parent_accumulator)
                        # Append nested content to the item
                        if nested_text:
                            all_items.append(item_text + nested_text)
                            nested_text = ''  # Use it once
                        else:
                            all_items.append(item_text)

                # Add current items
                all_items.extend(items)

                # Use emitter to format
                result = emitter.unordered_list(all_items, parent_depth)
            else:
                # Markdown: Use manual formatting to preserve exact spacing
                parent_indent = "  " * parent_depth
                for ctx in contexts_to_render:
                    parent_items = ctx['items']
                    nested_text = ctx.get('nested_text', '')
                    parent_accumulator = ctx.get('uli_accumulator', [])

                    # Render parent items using UL format (replace placeholders if needed)
                    for item in parent_items:
                        item_text = replace_placeholder(item, parent_accumulator)
                        result_parts.append(f"{parent_indent}- {item_text}\n")

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
                if new_depth == 0 and not emitter.can_concat_lists():
                    result += "\n"
    else:
        # No nesting - use emitter for simple case
        new_stack = []
        new_depth = depth
        result = emitter.unordered_list(items, depth)

    # Push Void sentinel back first, then new stack, then new_depth, then result (LIFO order)
    vm.al.append(Void)
    vm.al.append(new_stack)
    vm.al.append(new_depth)
    vm.al.append(result)


def drain_and_format_ol_builtin(vm):
    """
    >use.md.drain.ol builtin - Drain AL, check nesting stack, format as ordered list.

    AL before: [void, item1, item2, ..., itemN, depth, stack, accumulator, emitter, ...]
    AL after: ["1. item1\n...\n\n", new_depth, new_stack, void, ...]

    Items may include placeholders like "__MD_ITEM_PLACEHOLDER_N__" which are
    replaced with accumulated items from the accumulator list.
    Uses emitter.ordered_list() to format.
    """
    from soma.vm import Void, VoidSingleton

    # Pop emitter
    if len(vm.al) < 1:
        raise RuntimeError("AL underflow: md.drain.ol requires emitter")
    emitter = vm.al.pop()

    # Pop accumulator, stack and depth
    if len(vm.al) < 3:
        raise RuntimeError("AL underflow: md.drain.ol requires accumulator, stack and depth")
    accumulator = vm.al.pop()
    stack = vm.al.pop()
    depth = int(vm.al.pop())

    # Ensure accumulator is a list
    if not isinstance(accumulator, list):
        accumulator = []

    # Pop items until Void
    items = []
    while True:
        if len(vm.al) < 1:
            raise RuntimeError("AL underflow: md.drain.ol requires Void terminator")

        item = vm.al.pop()

        if isinstance(item, VoidSingleton):
            break

        items.append(item)  # Keep as object for now

    # Items are in reverse order (LIFO), so reverse them
    items.reverse()

    # Replace placeholders with accumulated items and validate types
    for i in range(len(items)):
        item = items[i]
        if isinstance(item, OliPlaceholder):
            # Correct placeholder type - replace with accumulated item
            if 0 <= item.index < len(accumulator):
                items[i] = accumulator[item.index]
            else:
                raise RuntimeError(f"OliPlaceholder index {item.index} out of range (accumulator has {len(accumulator)} items)")
        elif isinstance(item, UliPlaceholder):
            # Wrong placeholder type!
            raise RuntimeError(
                f">md.ol encountered UliPlaceholder (from >md.uli). "
                f"Use >md.ul for unordered list items, not >md.ol. "
                f"Did you mean to use >md.ul instead of >md.ol?"
            )
        elif isinstance(item, DliPlaceholder):
            # Wrong placeholder type!
            raise RuntimeError(
                f">md.ol encountered DliPlaceholder (from >md.dli). "
                f"Use >md.dol for definition list items, not >md.ol. "
                f"Did you mean to use >md.dol instead of >md.ol?"
            )
        else:
            # Regular item - convert to string
            items[i] = str(item)

    # Build result - use emitter for simple non-nested lists
    result_parts = []

    # Check if we have a parent context on the stack
    if isinstance(stack, list) and len(stack) > 0:
        parent_ctx = stack[-1]
        parent_depth = parent_ctx['depth']

        if depth > parent_depth:
            # We're a nested formatter - render only our items, add to parent context
            if emitter.can_concat_lists():
                # HTML: Use proper nested <ol> structure
                nested_result = emitter.ordered_list(items, depth)
            else:
                # Markdown: Use manual formatting to preserve exact spacing
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

            if emitter.can_concat_lists():
                # HTML: Build proper nested structure with nested lists inside <li> tags
                all_items = []

                # Process parent contexts
                for ctx in contexts_to_render:
                    parent_items = ctx['items']
                    nested_text = ctx.get('nested_text', '')
                    parent_accumulator = ctx.get('oli_accumulator', [])

                    for item in parent_items:
                        item_text = replace_placeholder(item, parent_accumulator)
                        # Append nested content to the item
                        if nested_text:
                            all_items.append(item_text + nested_text)
                            nested_text = ''  # Use it once
                        else:
                            all_items.append(item_text)

                # Add current items
                all_items.extend(items)

                # Use emitter to format
                result = emitter.ordered_list(all_items, parent_depth)
            else:
                # Markdown: Use manual formatting to preserve exact spacing
                parent_indent = "  " * parent_depth
                counter = 1
                for ctx in contexts_to_render:
                    parent_items = ctx['items']
                    nested_text = ctx.get('nested_text', '')
                    parent_accumulator = ctx.get('oli_accumulator', [])

                    # Render parent items using OL format (replace placeholders if needed)
                    for item in parent_items:
                        item_text = replace_placeholder(item, parent_accumulator)
                        result_parts.append(f"{parent_indent}{counter}. {item_text}\n")
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
                if new_depth == 0 and not emitter.can_concat_lists():
                    result += "\n"
    else:
        # No nesting - use emitter for simple case
        new_stack = []
        new_depth = depth
        result = emitter.ordered_list(items, depth)

    # Push Void sentinel back first, then new stack, then new_depth, then result (LIFO order)
    vm.al.append(Void)
    vm.al.append(new_stack)
    vm.al.append(new_depth)
    vm.al.append(result)


def drain_and_format_paragraphs_builtin(vm):
    """
    >use.md.drain.p builtin - Drain AL until Void, format each string as a separate paragraph.

    AL before: [void, item1, item2, ..., itemN, emitter, ...]
    AL after: ["item1\n\nitem2\n\n...\n\n", void, ...]

    Each string becomes its own paragraph with double newline suffix.
    Uses emitter.paragraph() to format.
    """
    from soma.vm import Void, VoidSingleton

    # Pop emitter
    if len(vm.al) < 1:
        raise RuntimeError("AL underflow: md.drain.p requires emitter")
    emitter = vm.al.pop()

    # Pop items until Void
    items = []
    while True:
        if len(vm.al) < 1:
            raise RuntimeError("AL underflow: md.drain.p requires Void terminator")

        item = vm.al.pop()

        if isinstance(item, VoidSingleton):
            break

        items.append(item)

    # Items are in reverse order (LIFO), so reverse them
    items.reverse()

    # Validate no placeholders
    validate_no_placeholders(items, ">md.p")

    # Convert to strings
    items = [str(item) for item in items]

    # Use emitter to format paragraphs
    result = emitter.paragraph(items)

    # Push Void sentinel back first, then result (LIFO order)
    vm.al.append(Void)
    vm.al.append(result)


def drain_and_format_blockquote_builtin(vm):
    """
    >use.md.drain.q builtin - Drain AL until Void, format as blockquote.

    AL before: [void, item1, item2, ..., itemN, emitter, ...]
    AL after: ["> item1\n> item2\n...\n\n", void, ...]

    Each string becomes a blockquote line prefixed with "> ".
    Uses emitter.blockquote() to format.
    """
    from soma.vm import Void, VoidSingleton

    # Pop emitter
    if len(vm.al) < 1:
        raise RuntimeError("AL underflow: md.drain.q requires emitter")
    emitter = vm.al.pop()

    # Pop items until Void
    items = []
    while True:
        if len(vm.al) < 1:
            raise RuntimeError("AL underflow: md.drain.q requires Void terminator")

        item = vm.al.pop()

        if isinstance(item, VoidSingleton):
            break

        items.append(item)

    # Items are in reverse order (LIFO), so reverse them
    items.reverse()

    # Validate no placeholders
    validate_no_placeholders(items, ">md.q")

    # Convert to strings
    items = [str(item) for item in items]

    # Use emitter to format blockquote
    result = emitter.blockquote(items)

    # Push Void sentinel back first, then result (LIFO order)
    vm.al.append(Void)
    vm.al.append(result)


def drain_and_format_code_block_builtin(vm):
    """
    >use.md.drain.code builtin - Drain AL until Void, format as code block.

    AL before: [void, line1, line2, ..., lineN, language, emitter, ...]
    AL after: ["```lang\nline1\nline2\n...\n```\n\n", void, ...]

    Language can be Nil or empty string for no language specification.
    Uses emitter.code_block() to format.
    """
    from soma.vm import Void, VoidSingleton, NilSingleton

    # Pop emitter
    if len(vm.al) < 1:
        raise RuntimeError("AL underflow: md.code requires emitter")
    emitter = vm.al.pop()

    # Pop language parameter
    if len(vm.al) < 1:
        raise RuntimeError("AL underflow: md.code requires language parameter")
    language = vm.al.pop()

    # Check if language is Nil or empty
    is_nil = isinstance(language, NilSingleton)
    is_empty = (not is_nil) and (str(language) == "")
    has_language = not (is_nil or is_empty)

    # Convert language to string or None
    language_str = str(language) if has_language else None

    # Pop lines until Void
    lines = []
    while True:
        if len(vm.al) < 1:
            raise RuntimeError("AL underflow: md.code requires Void terminator")

        item = vm.al.pop()

        if isinstance(item, VoidSingleton):
            break

        lines.append(item)

    # Lines are in reverse order (LIFO), so reverse them
    lines.reverse()

    # Validate no placeholders
    validate_no_placeholders(lines, ">md.code")

    # Convert to strings
    lines = [str(line) for line in lines]

    # Use emitter to format code block
    result = emitter.code_block(lines, language_str)

    # Push Void sentinel back first, then result (LIFO order)
    vm.al.append(Void)
    vm.al.append(result)


def nest_builtin(vm):
    """
    >use.md.nest builtin - Push current items onto nesting stack and increase depth.

    AL before: [void, item1, item2, ..., itemN, ...]
    AL after: [void, ...]

    Side effects: Pushes context onto md.state.stack, increases md.state.depth,
                  saves current accumulator state and clears it for nested level
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

        # Keep placeholders as objects, convert others to strings
        if is_placeholder(item):
            items.append(item)
        else:
            items.append(str(item))

    # Items are in reverse order (LIFO), so reverse them
    items.reverse()

    # Get current depth and stack
    current_depth = vm.store.read_value(['md', 'state', 'depth'])
    current_stack = vm.store.read_value(['md', 'state', 'stack'])

    # Save current accumulator state (oli, uli, and dli)
    oli_accumulator = vm.store.read_value(['md', 'state', 'oli', 'items'])
    uli_accumulator = vm.store.read_value(['md', 'state', 'uli', 'items'])
    dli_accumulator = vm.store.read_value(['md', 'state', 'dli', 'items'])

    # Ensure they're lists
    if not isinstance(oli_accumulator, list):
        oli_accumulator = []
    if not isinstance(uli_accumulator, list):
        uli_accumulator = []
    if not isinstance(dli_accumulator, list):
        dli_accumulator = []

    # Create context for this level (save items AND accumulator state)
    context = {
        'items': items,
        'depth': current_depth,
        'oli_accumulator': oli_accumulator[:],  # Copy
        'uli_accumulator': uli_accumulator[:],  # Copy
        'dli_accumulator': dli_accumulator[:]   # Copy
    }

    # Push context onto stack
    if not isinstance(current_stack, list):
        current_stack = []
    new_stack = current_stack + [context]
    vm.store.write_value(['md', 'state', 'stack'], new_stack)

    # Clear accumulators for nested level
    vm.store.write_value(['md', 'state', 'oli', 'items'], [])
    vm.store.write_value(['md', 'state', 'uli', 'items'], [])
    vm.store.write_value(['md', 'state', 'dli', 'items'], [])

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

        items.append(item)

    # Items are in reverse order (LIFO), so reverse them
    items.reverse()

    # Validate no placeholders
    validate_no_placeholders(items, ">md.table.header/row/align")

    # Convert to strings
    items = [str(item) for item in items]

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

    # Validate no placeholders
    validate_no_placeholders(items, ">md.dt")

    # Get emitter from state
    emitter = vm.store.read_value(['md', 'state', 'emitter'])

    # Format with alternating bold
    result = data_title_format(emitter, *items)

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

    # Validate no placeholders
    validate_no_placeholders(items, ">md.dl")

    # Get emitter from state
    emitter = vm.store.read_value(['md', 'state', 'emitter'])

    # Format as definition list items (returns list of formatted strings)
    formatted_items = definition_list_format(emitter, *items)

    # Push Void sentinel back first, then all formatted items (LIFO order)
    vm.al.append(Void)
    for formatted_item in formatted_items:
        vm.al.append(formatted_item)


def accumulate_list_item_builtin(vm):
    """
    >use.md.accumulate.item builtin - Drain AL, concatenate, append to accumulator.

    AL before: [void, item1, item2, ..., itemN, path_component1, path_component2, ...]
    AL after: [void]

    Expects path components on AL (e.g., "md", "state", "oli", "items")
    Side effect: Appends concatenated string to accumulator list in Store
    """
    from soma.vm import Void, VoidSingleton

    # Pop path components until we hit a special marker or count
    # For simplicity, we'll use a fixed path structure: md.state.oli.items or md.state.uli.items
    # Pop 4 components: items, oli/uli, state, md (in reverse order)
    if len(vm.al) < 4:
        raise RuntimeError("AL underflow: accumulate_list_item requires path components")

    # Pop in reverse order (LIFO)
    component4 = str(vm.al.pop())  # "items"
    component3 = str(vm.al.pop())  # "oli" or "uli"
    component2 = str(vm.al.pop())  # "state"
    component1 = str(vm.al.pop())  # "md"

    path_components = [component1, component2, component3, component4]

    # Drain items until Void or placeholder
    items = []
    hit_placeholder = False
    while True:
        if len(vm.al) < 1:
            raise RuntimeError("AL underflow: accumulate_list_item requires Void terminator")

        item = vm.al.pop()

        if isinstance(item, VoidSingleton):
            break

        # Stop if we hit a placeholder from a previous oli/uli call
        if is_placeholder(item):
            # Put it back and stop draining
            vm.al.append(item)
            hit_placeholder = True
            break

        items.append(str(item))

    # Items are in reverse order (LIFO), so reverse them
    items.reverse()

    # Get emitter and use its concat method to properly handle tagged strings
    # This processes each item (untagging/escaping as needed) and returns a tagged result
    # We KEEP the tag so the list formatter knows this is already-processed HTML
    emitter = vm.store.read_value(['md', 'state', 'emitter'])
    result = emitter.concat(items)

    # Read current accumulator
    try:
        accumulator = vm.store.read_value(path_components)
    except:
        accumulator = []

    if not isinstance(accumulator, list):
        accumulator = []

    # Append new item
    new_accumulator = accumulator + [result]

    # Write back to store
    vm.store.write_value(path_components, new_accumulator)

    # Push Void back if we hit it, otherwise we stopped at placeholder (which is already back)
    if not hit_placeholder:
        vm.al.append(Void)

    # Push placeholder to mark position in final list
    # Determine which placeholder type based on oli vs uli
    if component3 == "oli":
        placeholder = OliPlaceholder(len(accumulator))
    elif component3 == "uli":
        placeholder = UliPlaceholder(len(accumulator))
    else:
        raise RuntimeError(f"Unknown list type '{component3}' - expected 'oli' or 'uli'")

    vm.al.append(placeholder)


def accumulate_definition_list_item_builtin(vm):
    """
    >use.md.accumulate.dli builtin - Drain AL, format as definition item, append to accumulator.

    AL before: [void, label, value_part1, value_part2, ..., ...]
    AL after: [DliPlaceholder, void, ...]

    First item popped is the label, remaining items are concatenated as the value.
    Formats as "**label**: value" and appends to md.state.dli.items accumulator.
    Pushes DliPlaceholder to mark position in final list.
    """
    from soma.vm import Void, VoidSingleton

    # Drain items until Void or placeholder
    items = []
    hit_placeholder = False
    while True:
        if len(vm.al) < 1:
            raise RuntimeError("AL underflow: md.dli requires Void terminator")

        item = vm.al.pop()

        if isinstance(item, VoidSingleton):
            break

        # Stop if we hit a placeholder from a previous call
        if is_placeholder(item):
            # Put it back and stop draining
            vm.al.append(item)
            hit_placeholder = True
            break

        items.append(item)

    # Items are in reverse order (LIFO), so reverse them
    items.reverse()

    # Need at least 2 items: label and value
    if len(items) < 2:
        raise RuntimeError(
            f">md.dli requires at least label and value (got {len(items)} item(s)). "
            f"Usage: (Label) (value part 1) (value part 2) >md.b >md.dli"
        )

    # First item is label, rest are value parts
    label = str(items[0])
    value_parts = items[1:]

    # Get emitter and use its methods
    emitter = vm.store.read_value(['md', 'state', 'emitter'])

    # Concatenate value parts using emitter (handles tags properly)
    value = emitter.concat([str(v) for v in value_parts])

    # Format as definition list item: **label**: value
    formatted = emitter.list_item_formatted(label, value)

    # Read current accumulator
    try:
        accumulator = vm.store.read_value(['md', 'state', 'dli', 'items'])
    except:
        accumulator = []

    if not isinstance(accumulator, list):
        accumulator = []

    # Append new item
    new_accumulator = accumulator + [formatted]

    # Write back to store
    vm.store.write_value(['md', 'state', 'dli', 'items'], new_accumulator)

    # Push Void back if we hit it
    if not hit_placeholder:
        vm.al.append(Void)

    # Push placeholder to mark position in final list
    placeholder = DliPlaceholder(len(accumulator))
    vm.al.append(placeholder)


def list_length_builtin(vm):
    """
    >use.python.list_length builtin - Get length of Python list.

    AL before: [list, ...]
    AL after: [void, length, ...]

    Returns Void (exception placeholder) and length.
    """
    from soma.vm import Void

    if len(vm.al) < 1:
        raise RuntimeError("AL underflow: list_length requires list")

    lst = vm.al.pop()

    if not isinstance(lst, list):
        length = 0
    else:
        length = len(lst)

    # Push Void (exception placeholder), then length
    vm.al.append(Void)
    vm.al.append(length)


def list_to_al_builtin(vm):
    """
    >use.python.list_to_al builtin - Push list items to AL.

    AL before: [list, ...]
    AL after: [item1, item2, ..., itemN, ...]

    Pushes each item from the list onto AL in order.
    """
    if len(vm.al) < 1:
        raise RuntimeError("AL underflow: list_to_al requires list")

    lst = vm.al.pop()

    if isinstance(lst, list):
        for item in lst:
            vm.al.append(item)


def validate_document_builtin(vm):
    """
    >use.md.validate.document builtin - Validate document has no placeholders and strip tags.

    AL before: [document_string, ...]
    AL after: [cleaned_document_string, ...]

    Checks that the document string doesn't contain placeholder objects.
    If it does, raises an error indicating unconsumed oli/uli items.
    Also strips all U+100000 tags from the document before returning.
    """
    from soma.extensions.markdown_emitter import strip_all_tags

    if len(vm.al) < 1:
        raise RuntimeError("AL underflow: validate_document requires document string")

    doc = vm.al.pop()

    # Check if document is actually a placeholder object (shouldn't happen but be safe)
    if is_placeholder(doc):
        raise RuntimeError(
            f">md.render/print encountered {type(doc).__name__} in final document. "
            f"All placeholders from >md.oli/uli must be consumed by >md.ol/ul before rendering. "
            f"Did you forget to call >md.ol or >md.ul?"
        )

    # Strip all tags from document before output
    cleaned_doc = strip_all_tags(str(doc))

    # Push cleaned document back
    vm.al.append(cleaned_doc)


def throw_error_builtin(vm):
    """
    >use.python.throw builtin - Throw a RuntimeError with the given message.

    AL before: [message, ...]
    AL after: (never returns - raises exception)

    Pops error message from AL and raises RuntimeError.
    """
    if len(vm.al) < 1:
        raise RuntimeError("AL underflow: throw requires error message")

    message = vm.al.pop()
    raise RuntimeError(str(message))


def create_markdown_emitter_builtin(vm):
    """
    >use.md.create_emitter builtin - Create a new MarkdownEmitter instance.

    AL before: [...]
    AL after: [emitter, ...]

    Pushes a new MarkdownEmitter instance onto the AL.
    """
    emitter = MarkdownEmitter()
    vm.al.append(emitter)


def create_html_emitter_builtin(vm):
    """
    >use.md.create_html_emitter builtin - Create a new HtmlEmitter instance.

    AL before: [...]
    AL after: [emitter, ...]

    Pushes a new HtmlEmitter instance onto the AL.
    """
    from soma.extensions.markdown_emitter import HtmlEmitter
    emitter = HtmlEmitter()
    vm.al.append(emitter)


def set_emitter_builtin(vm):
    """
    >use.md.set_emitter builtin - Set the active emitter in md.state.emitter.

    AL before: [emitter, ...]
    AL after: [...]

    Pops an emitter from the AL and sets it as the active emitter in the store.
    """
    if len(vm.al) < 1:
        raise RuntimeError("AL underflow: set_emitter requires emitter")

    emitter = vm.al.pop()
    vm.store.write_value(['md', 'state', 'emitter'], emitter)


def drain_and_format_dul_builtin(vm):
    """
    >use.md.drain.dul builtin - Drain AL, format as definition unordered list.

    AL before: [void, items..., depth, stack, accumulator, emitter]
    AL after: [result, new_depth, new_stack, void]

    Supports two patterns:
    1. With >md.dli: [void, DliPlaceholder(0), DliPlaceholder(1), ..., depth, stack, accumulator, emitter]
    2. Without >md.dli (pairs): [void, label1, value1, label2, value2, ..., depth, stack, accumulator, emitter]

    For pattern 2, pairs are formatted as "**label**: value" automatically.
    Supports nesting via depth/stack like md.ul/md.ol.
    """
    from soma.vm import Void, VoidSingleton

    # Pop emitter
    if len(vm.al) < 1:
        raise RuntimeError("AL underflow: md.dul requires emitter")
    emitter = vm.al.pop()

    # Pop accumulator, stack and depth
    if len(vm.al) < 3:
        raise RuntimeError("AL underflow: md.dul requires accumulator, stack and depth")
    accumulator = vm.al.pop()
    stack = vm.al.pop()
    depth = int(vm.al.pop())

    # Ensure accumulator is a list
    if not isinstance(accumulator, list):
        accumulator = []

    # Pop items until Void
    items = []
    while True:
        if len(vm.al) < 1:
            raise RuntimeError("AL underflow: md.dul requires Void terminator")

        item = vm.al.pop()

        if isinstance(item, VoidSingleton):
            break

        items.append(item)

    # Items are in reverse order (LIFO), so reverse them
    items.reverse()

    # Check if we have DliPlaceholders (new pattern) or raw items (old pair pattern)
    has_dli_placeholders = any(isinstance(item, DliPlaceholder) for item in items)

    if has_dli_placeholders:
        # New pattern: replace DliPlaceholders with accumulated items
        resolved_items = []
        for item in items:
            if isinstance(item, DliPlaceholder):
                if 0 <= item.index < len(accumulator):
                    resolved_items.append(accumulator[item.index])
                else:
                    raise RuntimeError(f"DliPlaceholder index {item.index} out of range (accumulator has {len(accumulator)} items)")
            elif isinstance(item, (OliPlaceholder, UliPlaceholder)):
                raise RuntimeError(
                    f">md.dul encountered {type(item).__name__}. "
                    f"Use >md.ul for >md.uli items or >md.ol for >md.oli items."
                )
            else:
                resolved_items.append(str(item))
    else:
        # Old pattern: treat as pairs and format them
        if len(items) % 2 != 0:
            raise ValueError(
                f">md.dul requires even number of items for label-value pairs, got {len(items)}. "
                f"Hint: Each label needs a value. Did you forget an item or have an extra one?"
            )
        resolved_items = []
        for i in range(0, len(items), 2):
            label = str(items[i])
            value = str(items[i + 1])
            resolved_items.append(emitter.list_item_formatted(label, value))

    # Check if we have a parent context on the stack (nesting support)
    if isinstance(stack, list) and len(stack) > 0:
        parent_ctx = stack[-1]
        parent_depth = parent_ctx['depth']

        if depth > parent_depth:
            # We're a nested formatter - render only our items, add to parent context
            if emitter.can_concat_lists():
                # HTML: Use proper nested <ul> structure
                nested_result = emitter.unordered_list(resolved_items, depth)
            else:
                # Markdown: Use manual formatting to preserve exact spacing
                indent = "  " * depth
                result_parts = []
                for item in resolved_items:
                    result_parts.append(f"{indent}- {item}\n")
                nested_result = ''.join(result_parts)

            # Update parent context with nested text
            parent_ctx['nested_text'] = parent_ctx.get('nested_text', '') + nested_result

            # Don't pop stack, just update it
            new_stack = stack
            new_depth = parent_depth  # Return to parent depth

            # Return empty string - text already added to parent context
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

            result_parts = []
            if emitter.can_concat_lists():
                # HTML: Build proper nested structure with nested lists inside <li> tags
                all_items = []

                # Process parent contexts
                for ctx in contexts_to_render:
                    parent_items = ctx['items']
                    nested_text = ctx.get('nested_text', '')
                    parent_accumulator = ctx.get('dli_accumulator', [])

                    for item in parent_items:
                        item_text = replace_placeholder(item, parent_accumulator)
                        # Append nested content to the item
                        if nested_text:
                            all_items.append(item_text + nested_text)
                            nested_text = ''  # Use it once
                        else:
                            all_items.append(item_text)

                # Add current items
                all_items.extend(resolved_items)

                # Use emitter to format
                result = emitter.unordered_list(all_items, parent_depth)
            else:
                # Markdown: Use manual formatting to preserve exact spacing
                parent_indent = "  " * parent_depth
                for ctx in contexts_to_render:
                    parent_items = ctx['items']
                    nested_text = ctx.get('nested_text', '')
                    parent_accumulator = ctx.get('dli_accumulator', [])

                    # Render parent items using UL format (replace placeholders if needed)
                    for item in parent_items:
                        item_text = replace_placeholder(item, parent_accumulator)
                        result_parts.append(f"{parent_indent}- {item_text}\n")

                    # Insert nested text
                    if nested_text:
                        result_parts.append(nested_text)

                # Render current items at same depth
                for item in resolved_items:
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
                if new_depth == 0 and not emitter.can_concat_lists():
                    result += "\n"
    else:
        # No nesting - use emitter for simple case
        new_stack = []
        new_depth = depth
        result = emitter.unordered_list(resolved_items, 0)

    # Push Void sentinel back first, then new stack, then new_depth, then result (LIFO order)
    vm.al.append(Void)
    vm.al.append(new_stack)
    vm.al.append(new_depth)
    vm.al.append(result)


def drain_and_format_dol_builtin(vm):
    """
    >use.md.drain.dol builtin - Drain AL, format as definition ordered list.

    AL before: [void, items..., depth, stack, accumulator, emitter]
    AL after: [result, new_depth, new_stack, void]

    Supports two patterns:
    1. With >md.dli: [void, DliPlaceholder(0), DliPlaceholder(1), ..., depth, stack, accumulator, emitter]
    2. Without >md.dli (pairs): [void, label1, value1, label2, value2, ..., depth, stack, accumulator, emitter]

    For pattern 2, pairs are formatted as "**label**: value" automatically.
    Supports nesting via depth/stack like md.ul/md.ol.
    """
    from soma.vm import Void, VoidSingleton

    # Pop emitter
    if len(vm.al) < 1:
        raise RuntimeError("AL underflow: md.dol requires emitter")
    emitter = vm.al.pop()

    # Pop accumulator, stack and depth
    if len(vm.al) < 3:
        raise RuntimeError("AL underflow: md.dol requires accumulator, stack and depth")
    accumulator = vm.al.pop()
    stack = vm.al.pop()
    depth = int(vm.al.pop())

    # Ensure accumulator is a list
    if not isinstance(accumulator, list):
        accumulator = []

    # Pop items until Void
    items = []
    while True:
        if len(vm.al) < 1:
            raise RuntimeError("AL underflow: md.dol requires Void terminator")

        item = vm.al.pop()

        if isinstance(item, VoidSingleton):
            break

        items.append(item)

    # Items are in reverse order (LIFO), so reverse them
    items.reverse()

    # Check if we have DliPlaceholders (new pattern) or raw items (old pair pattern)
    has_dli_placeholders = any(isinstance(item, DliPlaceholder) for item in items)

    if has_dli_placeholders:
        # New pattern: replace DliPlaceholders with accumulated items
        resolved_items = []
        for item in items:
            if isinstance(item, DliPlaceholder):
                if 0 <= item.index < len(accumulator):
                    resolved_items.append(accumulator[item.index])
                else:
                    raise RuntimeError(f"DliPlaceholder index {item.index} out of range (accumulator has {len(accumulator)} items)")
            elif isinstance(item, (OliPlaceholder, UliPlaceholder)):
                raise RuntimeError(
                    f">md.dol encountered {type(item).__name__}. "
                    f"Use >md.ul for >md.uli items or >md.ol for >md.oli items."
                )
            else:
                resolved_items.append(str(item))
    else:
        # Old pattern: treat as pairs and format them
        if len(items) % 2 != 0:
            raise ValueError(
                f">md.dol requires even number of items for label-value pairs, got {len(items)}. "
                f"Hint: Each label needs a value. Did you forget an item or have an extra one?"
            )
        resolved_items = []
        for i in range(0, len(items), 2):
            label = str(items[i])
            value = str(items[i + 1])
            resolved_items.append(emitter.list_item_formatted(label, value))

    # Check if we have a parent context on the stack (nesting support)
    if isinstance(stack, list) and len(stack) > 0:
        parent_ctx = stack[-1]
        parent_depth = parent_ctx['depth']

        if depth > parent_depth:
            # We're a nested formatter - render only our items, add to parent context
            if emitter.can_concat_lists():
                # HTML: Use proper nested <ol> structure
                nested_result = emitter.ordered_list(resolved_items, depth)
            else:
                # Markdown: Use manual formatting to preserve exact spacing
                indent = "  " * depth
                result_parts = []
                counter = 1
                for item in resolved_items:
                    result_parts.append(f"{indent}{counter}. {item}\n")
                    counter += 1
                nested_result = ''.join(result_parts)

            # Update parent context with nested text
            parent_ctx['nested_text'] = parent_ctx.get('nested_text', '') + nested_result

            # Don't pop stack, just update it
            new_stack = stack
            new_depth = parent_depth  # Return to parent depth

            # Return empty string - text already added to parent context
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

            result_parts = []
            if emitter.can_concat_lists():
                # HTML: Build proper nested structure with nested lists inside <li> tags
                all_items = []

                # Process parent contexts
                for ctx in contexts_to_render:
                    parent_items = ctx['items']
                    nested_text = ctx.get('nested_text', '')
                    parent_accumulator = ctx.get('dli_accumulator', [])

                    for item in parent_items:
                        item_text = replace_placeholder(item, parent_accumulator)
                        # Append nested content to the item
                        if nested_text:
                            all_items.append(item_text + nested_text)
                            nested_text = ''  # Use it once
                        else:
                            all_items.append(item_text)

                # Add current items
                all_items.extend(resolved_items)

                # Use emitter to format
                result = emitter.ordered_list(all_items, parent_depth)
            else:
                # Markdown: Use manual formatting to preserve exact spacing
                parent_indent = "  " * parent_depth
                counter = 1
                for ctx in contexts_to_render:
                    parent_items = ctx['items']
                    nested_text = ctx.get('nested_text', '')
                    parent_accumulator = ctx.get('dli_accumulator', [])

                    # Render parent items using OL format (replace placeholders if needed)
                    for item in parent_items:
                        item_text = replace_placeholder(item, parent_accumulator)
                        result_parts.append(f"{parent_indent}{counter}. {item_text}\n")
                        counter += 1

                    # Insert nested text
                    if nested_text:
                        result_parts.append(nested_text)

                # Render current items at same depth (continue counter)
                for item in resolved_items:
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
                if new_depth == 0 and not emitter.can_concat_lists():
                    result += "\n"
    else:
        # No nesting - use emitter for simple case
        new_stack = []
        new_depth = depth
        result = emitter.ordered_list(resolved_items, 0)

    # Push Void sentinel back first, then new stack, then new_depth, then result (LIFO order)
    vm.al.append(Void)
    vm.al.append(new_stack)
    vm.al.append(new_depth)
    vm.al.append(result)


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
    vm.register_extension_builtin('use.md.drain.dul', drain_and_format_dul_builtin)
    vm.register_extension_builtin('use.md.drain.dol', drain_and_format_dol_builtin)
    # Register list item accumulator builtins
    vm.register_extension_builtin('use.md.accumulate.item', accumulate_list_item_builtin)
    vm.register_extension_builtin('use.md.accumulate.dli', accumulate_definition_list_item_builtin)
    vm.register_extension_builtin('use.python.list_length', list_length_builtin)
    vm.register_extension_builtin('use.python.list_to_al', list_to_al_builtin)
    vm.register_extension_builtin('use.md.validate.document', validate_document_builtin)
    vm.register_extension_builtin('use.python.throw', throw_error_builtin)
    # Register emitter creation and switching builtins
    vm.register_extension_builtin('use.md.create_emitter', create_markdown_emitter_builtin)
    vm.register_extension_builtin('use.md.create_html_emitter', create_html_emitter_builtin)
    vm.register_extension_builtin('use.md.set_emitter', set_emitter_builtin)


def get_soma_setup():
    """Return SOMA code implementing markdown."""
    import os
    soma_file = os.path.join(os.path.dirname(__file__), 'markdown.soma')
    with open(soma_file, 'r') as f:
        return f.read()
