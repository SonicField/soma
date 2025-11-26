"""
Python FFI Extension for SOMA.

Provides >use.python.* builtins for calling Python code from SOMA.
"""


def call_builtin(vm):
    """
    >use.python.call - Call a Python function with SOMA values.

    AL before: [callable_name(string), arg1, arg2, ..., argN, Void, ...]
    AL after: [result, exception, ...]

    Where:
    - callable_name: String name of Python callable (e.g., "int", "math.sqrt")
    - args: Arguments until Void terminator
    - result: Return value (or Void if exception)
    - exception: Exception object (or Void if success)

    Consumes arguments until Void, reverses them (natural → Python order),
    calls the Python callable, and pushes [result, exception].
    """
    from soma.vm import Void, VoidSingleton

    # Pop callable name
    if len(vm.al) < 1:
        from soma.vm import RuntimeError
        raise RuntimeError("AL underflow: use.python.call requires callable name")

    callable_name = vm.al.pop()

    if not isinstance(callable_name, str):
        from soma.vm import RuntimeError
        raise RuntimeError(f"use.python.call: expected string callable name, got {type(callable_name).__name__}")

    # Pop arguments until Void
    args = []
    while True:
        if len(vm.al) < 1:
            from soma.vm import RuntimeError
            raise RuntimeError("AL underflow: use.python.call requires Void terminator")

        arg = vm.al.pop()

        if isinstance(arg, VoidSingleton):
            break  # Found terminator

        args.append(arg)

    # Reverse arguments (natural push order → Python positional order)
    args.reverse()

    # Resolve callable
    try:
        # Handle module.function notation (e.g., "math.sqrt", "str.upper")
        if '.' in callable_name:
            parts = callable_name.split('.')
            module_or_type_name = '.'.join(parts[:-1])
            func_name = parts[-1]

            # Try as module.function first
            try:
                import importlib
                module = importlib.import_module(module_or_type_name)
                callable_obj = getattr(module, func_name)
            except (ImportError, ModuleNotFoundError):
                # Try as builtin.method (e.g., "str.upper")
                import builtins
                base = getattr(builtins, module_or_type_name)
                callable_obj = getattr(base, func_name)
        else:
            # Builtin function or global name
            import builtins
            callable_obj = getattr(builtins, callable_name)

    except (ImportError, AttributeError, ModuleNotFoundError) as e:
        # Push Void result and exception
        vm.al.append(Void)
        vm.al.append(str(e))
        return

    # Call Python function
    try:
        result = callable_obj(*args)

        # Convert None → Void
        if result is None:
            result = Void

        # Push result and Void exception
        vm.al.append(result)
        vm.al.append(Void)

    except Exception as e:
        # Push Void result and exception
        vm.al.append(Void)
        vm.al.append(e)


def load_builtin(vm):
    """
    >use.python.load - Load and execute a SOMA file.

    AL before: [filepath(string), ...]
    AL after: [...]

    Reads the file at filepath and executes it in the current VM context.
    """
    from soma.vm import RuntimeError

    if len(vm.al) < 1:
        raise RuntimeError("AL underflow: use.python.load requires filepath")

    filepath = vm.al.pop()

    if not isinstance(filepath, str):
        raise RuntimeError(f"use.python.load: expected string filepath, got {type(filepath).__name__}")

    # Read and execute the file
    try:
        with open(filepath, 'r') as f:
            code = f.read()

        vm.execute_code(code)

    except FileNotFoundError as e:
        raise RuntimeError(f"use.python.load: file not found: {filepath}")
    except IOError as e:
        raise RuntimeError(f"use.python.load: error reading file: {e}")


def import_builtin(vm):
    """
    >use.python.import - Import a Python module.

    AL before: [module_name(string), ...]
    AL after: [True/False, ...]

    Attempts to import the named Python module.
    Pushes True on success, False on failure.
    """
    from soma.vm import RuntimeError, True_, False_

    if len(vm.al) < 1:
        raise RuntimeError("AL underflow: use.python.import requires module name")

    module_name = vm.al.pop()

    if not isinstance(module_name, str):
        raise RuntimeError(f"use.python.import: expected string module name, got {type(module_name).__name__}")

    # Try to import
    try:
        import importlib
        importlib.import_module(module_name)
        vm.al.append(True_)
    except ImportError:
        vm.al.append(False_)


def register(vm):
    """
    Register Python extension builtins.

    Called by VM.load_extension('python').
    Registers:
    - >use.python.call - FFI primitive for calling Python functions
    - >use.python.load - Load SOMA files from filesystem
    - >use.python.import - Import Python modules
    """
    vm.register_extension_builtin('use.python.call', call_builtin)
    vm.register_extension_builtin('use.python.load', load_builtin)
    vm.register_extension_builtin('use.python.import', import_builtin)


def get_soma_setup():
    """
    Return SOMA setup code to run after registering builtins.

    Creates helper macros in the Store under use.python.* namespace.
    This demonstrates how extensions can include SOMA code to build
    convenience wrappers around the low-level FFI primitives.
    """
    return """
) Helper: Check if call succeeded (exception on stack is Void)
) Input: exception value on top of AL
) Output: True if Void (success), False otherwise
{ >isVoid } !use.python.succeeded

) Helper: Check if call failed (exception on stack is not Void)
) Input: exception value on top of AL
) Output: True if not Void (failure), False otherwise
{ >isVoid >not } !use.python.failed

) Helper: Get just the result, discard exception
) Input: [result, exception, ...] Output: [result, ...]
{ >drop } !use.python.getResult

) Helper: Get just the exception, discard result
) Input: [result, exception, ...] Output: [exception, ...]
{ >swap >drop } !use.python.getException
"""
