" Vim syntax file
" Language: SOMA (State-Oriented Machine Algebra)
" Maintainer: Alex Turner
" Latest Revision: 2024-11-28

if exists("b:current_syntax")
  finish
endif

" Comments - start with ) and go to end of line
syn match somaComment ").*$" contains=somaTodo

" TODO/FIXME/NOTE in comments
syn keyword somaTodo contained TODO FIXME NOTE XXX HACK

" Numbers (integers, including negative)
syn match somaNumber "\<-\?\d\+\>"

" Special values
syn keyword somaSpecial Nil Void True False

" String literals - enclosed in parentheses
" Use matchgroup to highlight the delimiters separately
syn region somaString matchgroup=somaStringDelimiter start="(" end=")" skip="\\)" contains=somaEscape

" String escapes like \HEX\
syn match somaEscape "\\[0-9a-fA-F]\+\\" contained

" Block braces - make them stand out
syn match somaBlockBrace "[{}]"

" Blocks - enclosed in braces (transparent for containing other syntax)
syn region somaBlock start="{" end="}" transparent fold

" SETTERS - Match entire !path constructs with high priority
" These must come before individual paths to take precedence
syn match somaSetter "!_\.[a-zA-Z0-9_.]*" " Register setter !_.x
syn match somaSetter "![a-zA-Z_][a-zA-Z0-9_.]*" " Store setter !x

" EXECUTION - Match entire >operation constructs to make them pop
" Built-in operations (FFI primitives) - highest priority, most distinctive
syn match somaBuiltinExec ">choose\>"
syn match somaBuiltinExec ">chain\>"
syn match somaBuiltinExec ">block\>"
syn match somaBuiltinExec "><\>"
syn match somaBuiltinExec ">+\>"
syn match somaBuiltinExec ">-\>"
syn match somaBuiltinExec ">\*\>"
syn match somaBuiltinExec ">/\>"
syn match somaBuiltinExec ">%\>"
syn match somaBuiltinExec ">concat\>"
syn match somaBuiltinExec ">toString\>"
syn match somaBuiltinExec ">toInt\>"
syn match somaBuiltinExec ">isVoid\>"
syn match somaBuiltinExec ">isNil\>"
syn match somaBuiltinExec ">print\>"

" Stdlib operations - still prominent but slightly different
syn match somaStdlibExec ">not\>"
syn match somaStdlibExec ">and\>"
syn match somaStdlibExec ">or\>"
syn match somaStdlibExec ">>\>"
syn match somaStdlibExec ">==\>"
syn match somaStdlibExec ">!=\>"
syn match somaStdlibExec ">=<\>"
syn match somaStdlibExec ">=>\>"
syn match somaStdlibExec ">dup\>"
syn match somaStdlibExec ">drop\>"
syn match somaStdlibExec ">swap\>"
syn match somaStdlibExec ">over\>"
syn match somaStdlibExec ">rot\>"
syn match somaStdlibExec ">inc\>"
syn match somaStdlibExec ">dec\>"
syn match somaStdlibExec ">abs\>"
syn match somaStdlibExec ">min\>"
syn match somaStdlibExec ">max\>"
syn match somaStdlibExec ">\^\>"
syn match somaStdlibExec ">times\>"
syn match somaStdlibExec ">if\>"
syn match somaStdlibExec ">ifelse\>"
syn match somaStdlibExec ">while\>"
syn match somaStdlibExec ">do\>"

" Extension operations (like >md.h1, >use.python)
syn match somaExtensionExec ">[a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z0-9_.]*"

" Extension names (like >use)
syn match somaExtensionExec ">use\>"

" Generic execution (anything else starting with >)
syn match somaExecution ">[a-zA-Z_][a-zA-Z0-9_.]*"

" Special operator (^)
syn match somaSpecialOp "\^"

" GETTERS - Regular value references
" Register paths (prefixed with _.) - very distinct from store paths
syn match somaRegisterPath "\<_\.[a-zA-Z_][a-zA-Z0-9_]*\>"
syn match somaRegisterPath "\<_\.\>"

" CellRef paths (trailing dot)
syn match somaCellRef "\<[a-zA-Z_][a-zA-Z0-9_.]*\.\>"

" Store paths (regular identifiers)
syn match somaStorePath "\<[a-zA-Z_][a-zA-Z0-9_]*\>"

" ============================================================================
" COLOUR DEFINITIONS
" ============================================================================
" Define custom colours that are visually distinct
" Users can override these in their .vimrc

" Comments - subtle grey
hi def link somaComment Comment
hi def link somaTodo Todo

" Literals
hi def somaString ctermfg=White guifg=#ffffff  " White for strings (common in SOMA docs)
hi def somaStringDelimiter ctermfg=Green guifg=#5fd75f cterm=bold gui=bold  " Green parens, bold (like braces)
hi def somaEscape ctermfg=Magenta guifg=#af5fff cterm=bold gui=bold
hi def somaNumber ctermfg=Magenta guifg=#af87ff  " Purple/magenta for numbers
hi def somaSpecial ctermfg=Magenta guifg=#d787ff cterm=bold gui=bold

" Blocks - green braces
hi def somaBlockBrace ctermfg=Green guifg=#5fd75f cterm=bold gui=bold

" SETTERS - Bold and distinctive (orange/yellow)
hi def somaSetter ctermfg=Yellow guifg=#ffaf00 cterm=bold gui=bold

" EXECUTION - Make these really pop! Bright cyan/blue, bold
hi def somaBuiltinExec ctermfg=Cyan guifg=#00d7ff cterm=bold gui=bold  " Bright cyan, bold
hi def somaStdlibExec ctermfg=Cyan guifg=#5fafff cterm=bold gui=bold   " Slightly darker cyan
hi def somaExtensionExec ctermfg=Blue guifg=#5f87ff cterm=bold gui=bold
hi def somaExecution ctermfg=Blue guifg=#87afff cterm=bold gui=bold

" Special operators
hi def somaSpecialOp ctermfg=Yellow guifg=#ffff00 cterm=bold gui=bold

" GETTERS - Regular paths
hi def somaRegisterPath ctermfg=Red guifg=#ff5f5f  " Bright red for register paths
hi def somaCellRef ctermfg=Yellow guifg=#d7af5f      " Orange-ish for cellrefs
hi def somaStorePath ctermfg=Red guifg=#d75f87     " Pink-red for store paths (distinct from register)

let b:current_syntax = "soma"
