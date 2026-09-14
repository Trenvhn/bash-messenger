# Windows Setup for Bash Messenger

## Quick Start (From Installation Directory)

```cmd
cd J:\bash_messenger
bashmess
```

## Make 'bashmess' Work from Anywhere

### Option 1: Add to User PATH (Recommended)

**PowerShell (run as Administrator):**
```powershell
[System.Environment]::SetEnvironmentVariable('Path', [System.Environment]::GetEnvironmentVariable('Path', 'User') + ';J:\bash_messenger', 'User')
```

Then restart your terminal and run:
```cmd
bashmess
```

### Option 2: Create PowerShell Alias

**PowerShell:**
```powershell
notepad $PROFILE
```

Add this line:
```powershell
function bashmess { python J:\bash_messenger\bash_messenger.py $args }
```

Save, restart PowerShell, then run:
```powershell
bashmess
```

### Option 3: System-wide PATH (Admin Required)

**Command Prompt (run as Administrator):**
```cmd
setx /M PATH "%PATH%;J:\bash_messenger"
```

Restart terminal and run:
```cmd
bashmess
```

### Option 4: Create Desktop Shortcut

1. Right-click `J:\bash_messenger\bashmess.bat`
2. Click "Send to" → "Desktop (create shortcut)"
3. Double-click the shortcut to run

## Troubleshooting

If none work, you can always run directly:
```cmd
cd J:\bash_messenger
python bash_messenger.py
```
