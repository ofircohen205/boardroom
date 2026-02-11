#!/bin/bash
# Install git hooks for the Boardroom project
# This script copies pre-push hook to .git/hooks/ and makes it executable

set -e  # Exit on error

# ANSI color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GIT_HOOKS_DIR="${SCRIPT_DIR}/../../.git/hooks"

# Check if .git directory exists
if [ ! -d "${SCRIPT_DIR}/../../.git" ]; then
    echo -e "${RED}Error: Not a git repository${NC}"
    echo "Please run this script from the project root."
    exit 1
fi

# Create hooks directory if it doesn't exist
mkdir -p "$GIT_HOOKS_DIR"

# Copy pre-push hook
echo "Installing pre-push hook..."
cp "${SCRIPT_DIR}/pre-push" "${GIT_HOOKS_DIR}/pre-push"
chmod +x "${GIT_HOOKS_DIR}/pre-push"

echo -e "${GREEN}✓ Pre-push hook installed successfully${NC}"
echo ""
echo "The following hook is now active:"
echo "  - pre-push: Blocks direct pushes to main branch"
echo ""
echo "To bypass in emergencies (not recommended):"
echo "  git push --no-verify origin main"
echo ""
