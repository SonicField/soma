"""
Pure SOMA Extension Example - Math Utilities.

Demonstrates an extension that provides only SOMA code, no Python builtins.
All functionality is built using existing SOMA primitives.
"""


def register(vm):
    """
    Register extension (required function).

    For pure SOMA extensions, this can be empty - all functionality
    comes from get_soma_setup().
    """
    pass  # No Python builtins to register


def get_soma_setup():
    """
    Return pure SOMA code defining math utilities.

    This demonstrates that extensions can be 100% SOMA - the Python file
    just needs to exist to return the SOMA code via get_soma_setup().
    """
    return """
) ============================================================================
) use.math - Pure SOMA Math Extension
) ============================================================================
) Demonstrates that extensions can be entirely SOMA code with no FFI.

) Absolute value
) Input: [x, ...] Output: [|x|, ...]
{ >dup 0 >< { 0 >swap >- } { >dup >drop } >choose >^ } !use.math.abs

) Maximum of two numbers
) Input: [a, b, ...] Output: [max(a,b), ...]
{ >over >over >< { >swap >drop } { >drop } >choose >^ } !use.math.max

) Minimum of two numbers
) Input: [a, b, ...] Output: [min(a,b), ...]
{ >over >over >< { >drop } { >swap >drop } >choose >^ } !use.math.min

) Square
) Input: [x, ...] Output: [x², ...]
{ >dup >* } !use.math.square

) Cube
) Input: [x, ...] Output: [x³, ...]
{ >dup >dup >* >* } !use.math.cube

) Check if even
) Input: [n, ...] Output: [True/False, ...]
{ 2 >% 0 >== } !use.math.isEven

) Check if odd
) Input: [n, ...] Output: [True/False, ...]
{ 2 >% 0 >== >not } !use.math.isOdd
"""
