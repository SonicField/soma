# Vim Syntax Highlighting for SOMA

This directory contains Vim syntax highlighting support for SOMA (State-Oriented Machine Algebra).

## Features

- **Syntax highlighting** for all SOMA language constructs
- **Comment recognition** (lines starting with `)`)
- **String literals** (enclosed in parentheses)
- **Number literals** (integers, including negative)
- **Special values** (Nil, Void, True, False)
- **Block folding** (fold on `{...}` blocks)
- **Operator highlighting** (`>`, `!`, `^`)
- **Built-in operations** (FFI primitives like `>choose`, `>chain`, `>print`)
- **Standard library** operations (`>dup`, `>swap`, `>if`, etc.)
- **Extension operations** (like `>md.h1`, `>use.python`)
- **Register paths** (paths starting with `_.`)
- **CellRef paths** (paths ending with `.`)
- **TODO/FIXME/NOTE** highlighting in comments

## Installation

### Automatic Installation

Run the installer script from the SOMA repository root:

```bash
./editors/vim/install.sh
```

This will create symlinks in your `~/.vim/` directory.

### Manual Installation

Copy or symlink the files to your Vim configuration directory:

```bash
# Create directories if they don't exist
mkdir -p ~/.vim/ftdetect
mkdir -p ~/.vim/syntax

# Copy files
cp editors/vim/ftdetect/soma.vim ~/.vim/ftdetect/
cp editors/vim/syntax/soma.vim ~/.vim/syntax/

# OR create symlinks (recommended - stays up to date)
ln -s $(pwd)/editors/vim/ftdetect/soma.vim ~/.vim/ftdetect/soma.vim
ln -s $(pwd)/editors/vim/syntax/soma.vim ~/.vim/syntax/soma.vim
```

### For Vim-Plug Users

Add this to your `.vimrc`:

```vim
Plug 'path/to/soma/editors/vim'
```

## Usage

Once installed, open any `.soma` file and syntax highlighting will be applied automatically:

```bash
vim examples/soma_runner/example.soma
```

## Colour Scheme

The syntax file uses custom colours designed for maximum visual distinction:

### Literals
- **String content** → White (`#ffffff`) - e.g., `Hello World` (neutral, since very common)
- **String delimiters** → Green, **bold** (`#5fd75f`) - e.g., `(` and `)` around strings
- **Numbers** → Magenta (`#af87ff`) - e.g., `42`, `-17`
- **Special values** → Magenta, bold - e.g., `Nil`, `Void`, `True`, `False`

### Structure
- **Block braces** → Green, **bold** (`#5fd75f`) - e.g., `{` and `}`

### Operations
- **Setters** → Yellow/Orange, **bold** (`#ffaf00`) - e.g., `!x`, `!_.counter`
- **Execution (built-in)** → Bright Cyan, **bold** (`#00d7ff`) - e.g., `>print`, `>choose`, `>+`
- **Execution (stdlib)** → Cyan, **bold** (`#5fafff`) - e.g., `>dup`, `>if`, `>while`
- **Execution (extensions)** → Blue, **bold** (`#5f87ff`) - e.g., `>md.h1`, `>use`
- **Execution (generic)** → Blue, **bold** (`#87afff`) - e.g., `>myfunction`

### Paths (Getters)
- **Register paths** → Bright Red (`#ff5f5f`) - e.g., `_.x`, `_.counter`
- **Store paths** → Pink-Red (`#d75f87`) - e.g., `x`, `counter` (distinct from register!)
- **CellRefs** → Orange (`#d7af5f`) - e.g., `path.`, `list.head.`

### Other
- **Comments** → Grey - e.g., `) This is a comment`
- **Special operators** → Yellow, bold - e.g., `^`

The colour scheme is designed so that:
- **String content** is white/neutral (very common in SOMA markdown documents)
- **String parentheses** `()` are bold green - matches block braces, easy to see
- **Block braces** `{}` are bold green - easy to spot block boundaries
- **Register paths** are bright red vs **store paths** which are pink-red - both visible, subtly distinct
- **Setters** (mutations) are bold yellow - immediately visible
- **Execution** operations are bold cyan/blue - they really pop!
- **Numbers** are purple - distinct from everything else

## Known Limitations

### String Detection

SOMA uses parentheses `()` for string literals, which makes perfect detection challenging with regex alone. The current implementation uses a simple region match that works well in most cases but might occasionally:

- Highlight non-string parentheses as strings
- Miss strings in complex nested contexts

For 100% accurate string detection, a TreeSitter grammar would be needed.

### Suggestions for Improvement

If you encounter highlighting issues:

1. Try breaking complex expressions across multiple lines
2. Use the `docs/SKILL.md` coding style recommendations
3. Consider contributing a TreeSitter grammar for SOMA!

## Customization

You can customize colours in your `.vimrc`. The syntax file uses these custom highlight groups:

```vim
" Example: Change setter colour to red
hi somaSetter ctermfg=Red guifg=#ff0000 cterm=bold gui=bold

" Example: Make execution operations less bold
hi somaBuiltinExec ctermfg=Cyan guifg=#00d7ff cterm=NONE gui=NONE

" Example: Different colour for register paths
hi somaRegisterPath ctermfg=Yellow guifg=#ffff00

" Example: Make store paths brighter
hi somaStorePath ctermfg=White guifg=#ffffff cterm=bold gui=bold
```

Available highlight groups:
- `somaComment`, `somaTodo`
- `somaString`, `somaStringDelimiter`, `somaEscape`, `somaNumber`, `somaSpecial`
- `somaBlockBrace` (for `{` and `}`)
- `somaSetter` (for `!x` and `!_.x`)
- `somaBuiltinExec`, `somaStdlibExec`, `somaExtensionExec`, `somaExecution`
- `somaRegisterPath` (for `_.x`), `somaStorePath` (for `x`), `somaCellRef` (for `x.`)
- `somaSpecialOp`

## Testing

Test the syntax highlighting with the example files:

```bash
vim examples/soma_runner/example.soma
vim examples/soma_runner/complete_example.soma
vim soma/stdlib.soma
vim tests/soma/01_ffi_builtins.soma
```

## Contributing

Improvements to the syntax highlighting are welcome! Common areas:

- Better string literal detection
- More sophisticated pattern matching
- Additional edge cases
- Performance optimizations

## See Also

- **SOMA Documentation**: `docs/index.md`
- **Language Reference**: `docs/SKILL.md`
- **Examples**: `examples/`

## Licence

This syntax file is part of the SOMA project and follows the same licence.
