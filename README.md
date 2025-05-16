
# NASDAQ LUDP Halt Monitor Widget

A floating Windows widget that displays real-time NASDAQ trading halts with LUDP reason codes, including countdown timers to estimated unhalt times.


## Features
- Real-time updates every 15 seconds
- Always-on-top floating window
- Draggable interface
- Countdown timers with color-coded status
- Semi-transparent dark theme

## Installation (For Windows Users with No Python Experience)

### 1. Install Python
1. Download Python 3.12 from [python.org](https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe)
2. Run the installer and check both:
   - ☑️ "Install launcher for all users"
   - ☑️ "Add Python to PATH" (IMPORTANT!)
3. Click "Install Now"

### 2. Open PowerShell
Right-click the Start menu → Select "Windows PowerShell (Admin)"

### 3. Install Required Packages
Copy and paste this command into PowerShell:

```
python -m pip install pyqt6 requests beautifulsoup4 pytz lxml
```

### 4. Download the Widget
Create a new file called `halts_widget.pyw` on your Desktop and paste in the code from [widget_code.py]
*(Replace with actual URL to your code)*

**Or** use this PowerShell command (replace URL):

```
Invoke-WebRequest -Uri "[https://github.com/Mike-Ippolito/Halts_widget/blob/main/halts_widget.pyw]" -OutFile "$HOME\Desktop\halts_widget.pyw"
```

### 5. Create a Desktop Shortcut
1. Right-click on your Desktop → New → Text Document
2. Name it `Run Halt Monitor.bat`
3. Right-click → Edit, and paste:

```
@echo off
pythonw "%USERPROFILE%\Desktop\halts_widget.pyw"
```

4. Save the file and double-click to run

## Usage
- **Move the widget**: Click and drag anywhere
- **Automatic updates**: Data refreshes every 15 seconds
- **Close the widget**: Right-click taskbar icon → Close window

## Verification
After installation:
1. Double-click `Run Halt Monitor.bat`
2. A small dark rectangle should appear in the top-right corner
3. Within 15 seconds, it should display either:
   - Active halts with countdown timers
   - "No active LUDP halts"

## Troubleshooting

### Common Issues
**Q: Nothing happens when I double-click the .bat file**
- Ensure Python is installed and added to PATH
- Try running from PowerShell:
  ```
  pythonw "$HOME\Desktop\halts_widget.pyw"
  ```

**Q: Missing module errors**
- Reinstall requirements:
  ```
  python -m pip install --upgrade pyqt6 requests beautifulsoup4 pytz
  ```

**Q: Widget shows "UNHALTED?" but stock is still halted**
- NASDAQ may delay updates. Wait 2-3 minutes for feed synchronization.

**Q: Security warnings when running scripts**
- In PowerShell, run:
  ```
  Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```
  Click `[A] Yes to All` when prompted

## Uninstallation
1. Delete these files:
   - `halts_widget.pyw` from Desktop
   - `Run Halt Monitor.bat` from Desktop
2. (Optional) Uninstall Python via Control Panel → Programs → Uninstall

