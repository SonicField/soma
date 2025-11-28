# SOMA Runner

A clean command-line interface for executing SOMA programs from stdin.

## Usage

```bash
cat program.soma | python3 soma.py > output.txt
```

Or directly with a shebang:
```bash
cat program.soma | ./soma.py > output.txt
```

## Description

This script provides a clean, Unix-friendly way to run SOMA programs:

- **Reads from stdin**: SOMA code in UTF-8 encoding
- **Writes to stdout**: Program output only (UTF-8)
- **Errors to stderr**: Error messages don't pollute output

## Examples

### Simple Output

```bash
echo "md.state.doc >print" | python3 soma.py
```

### Markdown Generation

Create a SOMA markdown document that outputs to stdout:

```soma
(python) >use
(markdown) >use

>md.start

(My Document) >md.h1
(Introduction text) >md.p

) Output the generated markdown to stdout
md.state.doc >print
```

Run it:
```bash
cat document.soma | python3 soma.py > output.md
```

### Pipeline Processing

```bash
# Generate markdown and pipe to another tool
cat document.soma | python3 soma.py | pandoc -f markdown -t html
```

## Key Features

- **Clean output**: Only SOMA program output goes to stdout
- **UTF-8 support**: Full Unicode support for input and output
- **Error handling**: Errors reported to stderr with non-zero exit code
- **Pipeline friendly**: Designed for Unix-style command composition

## Return Codes

- `0`: Success
- `1`: Error (details on stderr)

## Notes

To output markdown to stdout instead of a file, use `>md.print` instead of `>md.render`:

```soma
(python) >use
(markdown) >use

>md.start
(Content here...) >md.p

) Print to stdout instead of rendering to file
>md.print
```
