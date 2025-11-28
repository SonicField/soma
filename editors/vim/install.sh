#!/bin/bash
# Installation script for SOMA Vim syntax highlighting
# This creates symlinks in ~/.vim/ pointing to the files in this directory

set -e

# Colours for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Colour

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "SOMA Vim Syntax Highlighting Installer"
echo "======================================="
echo

# Create ~/.vim directories if they don't exist
echo "Creating Vim directories..."
mkdir -p ~/.vim/ftdetect
mkdir -p ~/.vim/syntax

# Function to create symlink with backup
create_symlink() {
    local source="$1"
    local target="$2"
    local name="$3"

    if [ -L "$target" ]; then
        # It's already a symlink
        existing_target=$(readlink "$target")
        if [ "$existing_target" = "$source" ]; then
            echo -e "${GREEN}✓${NC} $name already installed"
            return 0
        else
            echo -e "${YELLOW}!${NC} $name exists (symlink to $existing_target)"
            read -p "  Replace with new symlink? [y/N] " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                rm "$target"
            else
                echo -e "${YELLOW}↷${NC} Skipping $name"
                return 1
            fi
        fi
    elif [ -f "$target" ]; then
        # It's a regular file
        echo -e "${YELLOW}!${NC} $name exists (regular file)"
        read -p "  Back up and replace? [y/N] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            mv "$target" "$target.backup"
            echo -e "${GREEN}→${NC} Backed up to $target.backup"
        else
            echo -e "${YELLOW}↷${NC} Skipping $name"
            return 1
        fi
    fi

    # Create the symlink
    ln -s "$source" "$target"
    echo -e "${GREEN}✓${NC} Installed $name"
    return 0
}

# Install files
echo
echo "Installing syntax files..."
create_symlink "$SCRIPT_DIR/ftdetect/soma.vim" ~/.vim/ftdetect/soma.vim "ftdetect/soma.vim"
create_symlink "$SCRIPT_DIR/syntax/soma.vim" ~/.vim/syntax/soma.vim "syntax/soma.vim"

echo
echo "======================================="
echo -e "${GREEN}Installation complete!${NC}"
echo
echo "Syntax highlighting will now work for .soma files."
echo
echo "Try it:"
echo "  vim examples/soma_runner/example.soma"
echo
echo "To customize colours, see:"
echo "  $SCRIPT_DIR/README.md"
echo
