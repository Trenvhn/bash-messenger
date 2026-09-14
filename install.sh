#!/bin/bash
# Bash Messenger Installer for Unix/Linux/macOS

set -e

echo "================================"
echo "  Bash Messenger Installer"
echo "================================"
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "Error: Python $REQUIRED_VERSION or higher is required"
    echo "Current version: $PYTHON_VERSION"
    exit 1
fi

echo "✓ Python $PYTHON_VERSION detected"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 is not installed"
    exit 1
fi

echo "✓ pip3 detected"
echo ""

# Install dependencies
echo "Installing dependencies..."

# Try pip install, if it fails due to externally-managed, use venv
if ! pip3 install -r requirements.txt 2>/dev/null; then
    echo ""
    echo "System is externally managed, creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt

    # Update bashmess script to use venv
    cat > bashmess << 'LAUNCHER'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/venv/bin/activate"
python3 "$SCRIPT_DIR/bash_messenger.py" "$@"
LAUNCHER
    chmod +x bashmess
fi

echo ""
echo "================================"
echo "✓ Installation complete!"
echo "================================"
echo ""

# Create symlink or add to PATH
INSTALL_DIR="$(pwd)"

# Ensure ~/.local/bin exists
mkdir -p "$HOME/.local/bin"

# Create absolute path symlink
ln -sf "$INSTALL_DIR/bashmess" "$HOME/.local/bin/bashmess"
chmod +x "$HOME/.local/bin/bashmess"

echo "✓ Added 'bashmess' command to ~/.local/bin"
echo ""

# Check if ~/.local/bin is in PATH
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo "Adding ~/.local/bin to PATH..."
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    echo ""
    echo "Run this command to activate:"
    echo "  source ~/.bashrc"
    echo ""
    echo "Or open a new terminal, then run:"
    echo "  bashmess"
else
    echo "To run Bash Messenger, simply type:"
    echo "  bashmess"
fi
echo ""
