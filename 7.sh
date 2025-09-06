# Check if we're already in a mnemosyne* directory
if [ -d "mnemosyne" ] || [ -d "mnemosyneos" ] || [ -d "MnemosyneOS" ]; then
    echo "Found a mnemosyne directory here: $(pwd)"
    ls -la | grep -i mnemosyne
else
    echo "No mnemosyne directory found here. Searching for it..."
    
    # Search for likely directory names
    MNEMOSYNE_DIR=$(find ~ -type d -name "*mnemosyne*" -o -name "*Mnemosyne*" 2>/dev/null | head -1)
    
    if [ -n "$MNEMOSYNE_DIR" ]; then
        echo "Found Mnemosyne directory at: $MNEMOSYNE_DIR"
        cd "$MNEMOSYNE_DIR"
        echo "Changed to: $(pwd)"
    else
        echo "Could not find Mnemosyne directory automatically."
        echo "Please navigate to it manually with: cd /path/to/your/mnemosyne/directory"
    fi
fi