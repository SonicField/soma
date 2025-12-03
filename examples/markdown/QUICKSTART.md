# SOMA Markdown Quick Start

## Learn

Read the comprehensive user guide:
```bash
cat examples/markdown/markdown-user-guide.soma
```

Or view the generated markdown version for easier reading.

## Generate Markdown

```bash
# 1. Create your SOMA document (my-doc.soma)
(python) >use
(markdown) >use
>md.start

(My Document) >md.h1
(This is content.) >md.p

(my-doc.md) >md.render

# 2. Run it
soma my-doc.soma
```

## Generate Styled HTML

```bash
# 1. Create your SOMA document (my-doc.soma)
(python) >use
(markdown) >use
>md.start
md.htmlEmitter >md.emitter    # ← Key difference: switch to HTML!

(My Document) >md.h1
(This is content.) >md.p

(my-doc.html) >md.render

# 2. Run it and wrap with styling
cd examples/markdown
soma ../../my-doc.soma
./wrap-html.sh --inline ../../my-doc.html    # ← Standalone HTML with inlined CSS!

# 3. Open my-doc-styled.html in browser
#    (No external CSS file needed - completely standalone!)
```

**Note:** Use `--inline` for standalone documents, or omit for linked CSS.

That's it! See `html_example.soma` for a complete working example.
