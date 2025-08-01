# Audible File Converter

A web-based application that converts Audible files (.aax/.aa) to MP3 format and automatically splits them into 24MB chunks for easier management and storage.

## Features

- **File Format Support**: Converts .aax and .aa Audible files to MP3
- **Automatic Chunking**: Splits large audio files into 24MB chunks
- **Web Interface**: Modern, responsive web UI with drag-and-drop support
- **Activation Bytes Support**: Optional activation bytes input for .aax files
- **Batch Download**: All converted chunks are packaged in a ZIP file
- **Progress Tracking**: Real-time conversion progress updates

## Prerequisites

Before running the application, ensure you have the following installed:

1. **Python 3.7+**
2. **FFmpeg**: Required for audio conversion
   - Windows: Download from https://ffmpeg.org/download.html
   - Add FFmpeg to your system PATH
3. **pip**: Python package installer

## Installation

1. Clone or download this project to your local machine

2. Navigate to the project directory:
   ```bash
   cd "Audible Converter"
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Verify FFmpeg installation:
   ```bash
   ffmpeg -version
   ```

## Usage

1. **Start the application**:
   ```bash
   python app.py
   ```

2. **Open your web browser** and navigate to:
   ```
   http://localhost:5000
   ```

3. **Upload your Audible file**:
   - Drag and drop your .aax or .aa file onto the upload area
   - Or click "Choose File" to browse and select your file

4. **Enter activation bytes** (if required):
   - For some .aax files, you may need activation bytes
   - Leave this field empty if not required

5. **Convert the file**:
   - Click "Convert to MP3"
   - Wait for the conversion process to complete

6. **Download your files**:
   - Once conversion is complete, download the ZIP file containing all audio chunks
   - Each chunk will be approximately 24MB in size

## File Structure

```
Audible Converter/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── templates/
│   └── index.html        # Web interface template
├── static/
│   └── js/
│       └── main.js       # Frontend JavaScript
├── uploads/              # Temporary upload storage (created automatically)
└── output/               # Converted files storage (created automatically)
```

## Technical Details

### Conversion Process

1. **Upload**: User uploads .aax or .aa file
2. **Validation**: File type and size validation
3. **Conversion**: FFmpeg converts Audible format to MP3 (128kbps)
4. **Splitting**: PyDub splits the MP3 into 24MB chunks
5. **Packaging**: All chunks are packaged into a ZIP file
6. **Cleanup**: Temporary files are automatically removed

### Supported Formats

- **Input**: .aax, .aa (Audible formats)
- **Output**: .mp3 (128kbps bitrate)
- **Chunk Size**: 24MB maximum per file

### Dependencies

- **Flask**: Web framework
- **PyDub**: Audio processing
- **FFmpeg**: Audio conversion engine
- **Mutagen**: Audio metadata handling

## Troubleshooting

### Common Issues

1. **FFmpeg not found**:
   - Ensure FFmpeg is installed and added to your system PATH
   - Test with: `ffmpeg -version`

2. **Activation bytes required**:
   - Some .aax files require activation bytes
   - You can find these through various online tools or methods

3. **Large file processing**:
   - Very large files may take considerable time to process
   - Ensure sufficient disk space for temporary files

4. **Port already in use**:
   - If port 5000 is busy, modify the port in `app.py`:
   ```python
   app.run(debug=True, host='0.0.0.0', port=5001)
   ```

### Error Messages

- **"Invalid file type"**: Only .aax and .aa files are supported
- **"FFmpeg error"**: Check FFmpeg installation and activation bytes
- **"Conversion failed"**: File may be corrupted or require activation bytes

## Security Notes

- Files are temporarily stored during processing and automatically deleted
- No user data is permanently stored on the server
- Use in a trusted environment only

## License

This project is for educational and personal use only. Ensure you have the legal right to convert any Audible files you process.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Verify all prerequisites are properly installed
3. Check the browser console for JavaScript errors
4. Review the Flask application logs for server-side errors
