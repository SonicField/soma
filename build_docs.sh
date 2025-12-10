#!/bin/bash
# build_docs.sh - Render all SOMA documentation from .soma source to .md
#
# Usage: ./build_docs.sh [--clean] [--verbose]
#
# This script finds all .soma files in docs/ and renders them to .md
# using the soma runner (python3 -m soma).

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VERBOSE=false
CLEAN=false

for arg in "$@"; do
    case $arg in
        --verbose|-v) VERBOSE=true ;;
        --clean) CLEAN=true ;;
    esac
done

log() {
    if $VERBOSE; then
        echo "$@"
    fi
}

# Find all .soma files in docs/ and render to .md
render_soma_files() {
    local count=0
    local failed=0

    while IFS= read -r soma_file; do
        # Derive .md filename (same name, different extension)
        md_file="${soma_file%.soma}.md"

        log "Rendering: $soma_file -> $md_file"

        if python3 -m soma < "$soma_file" > "$md_file.tmp" 2>&1; then
            mv "$md_file.tmp" "$md_file"
            count=$((count + 1))
        else
            echo "ERROR: Failed to render $soma_file" >&2
            rm -f "$md_file.tmp"
            failed=$((failed + 1))
        fi
    done < <(find docs -name "*.soma" -type f)

    echo "Rendered $count files successfully"
    if [[ $failed -gt 0 ]]; then
        echo "Failed to render $failed files"
        exit 1
    fi
}

# Clean generated .md files (only where .soma source exists)
clean_generated() {
    local count=0

    while IFS= read -r soma_file; do
        md_file="${soma_file%.soma}.md"
        if [[ -f "$md_file" ]]; then
            log "Removing: $md_file"
            rm "$md_file"
            count=$((count + 1))
        fi
    done < <(find docs -name "*.soma" -type f)

    echo "Cleaned $count generated files"
}

if $CLEAN; then
    clean_generated
else
    render_soma_files
fi
