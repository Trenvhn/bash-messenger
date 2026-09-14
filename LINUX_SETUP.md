# Quick Fix for Running bashmess Command

If `bashmess` command doesn't work after installation, run:

```bash
# Add to PATH (run once)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Or open a new terminal and run:
bashmess
```

## Alternative: Create an alias

```bash
echo "alias bashmess='$PWD/bashmess'" >> ~/.bashrc
source ~/.bashrc
bashmess
```

## Or run directly from the directory

```bash
cd /path/to/bash-messenger
./bashmess
```
