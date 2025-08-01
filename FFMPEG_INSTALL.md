# FFmpeg Installation Guide for Windows

## Quick Installation Options

### Option 1: Download Pre-built Binaries (Recommended)

1. **Download FFmpeg**:
   - Go to https://ffmpeg.org/download.html
   - Click "Windows" and then "Windows builds by BtbN"
   - Download the latest release (e.g., `ffmpeg-master-latest-win64-gpl.zip`)

2. **Extract and Install**:
   - Extract the ZIP file to `C:\ffmpeg\`
   - You should have: `C:\ffmpeg\bin\ffmpeg.exe` and `C:\ffmpeg\bin\ffprobe.exe`

3. **Add to System PATH**:
   - Press `Win + R`, type `sysdm.cpl`, press Enter
   - Click "Environment Variables"
   - Under "System Variables", find and select "Path", click "Edit"
   - Click "New" and add: `C:\ffmpeg\bin`
   - Click "OK" on all dialogs
   - **Restart your command prompt/terminal**

4. **Verify Installation**:
   ```cmd
   ffmpeg -version
   ffprobe -version
   ```

### Option 2: Using Chocolatey (if you have it)

```cmd
choco install ffmpeg
```

### Option 3: Using Winget (Windows 10/11)

```cmd
winget install Gyan.FFmpeg
```

## Troubleshooting

- **"Command not found"**: Make sure FFmpeg is in your PATH and restart your terminal
- **Permission errors**: Run as administrator when adding to PATH
- **Still not working**: Try logging out and back in to refresh environment variables

## Alternative: Portable Installation

If you don't want to modify system PATH:

1. Create folder: `C:\Users\georg\CascadeProjects\Audible Converter\ffmpeg\`
2. Place `ffmpeg.exe` and `ffprobe.exe` in that folder
3. The app will be updated to check this location automatically

After installation, restart the Audible Converter app and try converting again!
