import os
import tempfile
import shutil
from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
from werkzeug.utils import secure_filename
import subprocess
import zipfile
try:
    from mutagen import File
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False
import math
from datetime import datetime
from dotenv import load_dotenv
from activation_extractor import ActivationBytesExtractor

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
ALLOWED_EXTENSIONS = {'aax', 'aa'}
MAX_CHUNK_SIZE_MB = 24
MAX_CHUNK_SIZE_BYTES = MAX_CHUNK_SIZE_MB * 1024 * 1024

# Create directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_size_mb(filepath):
    """Get file size in MB"""
    return os.path.getsize(filepath) / (1024 * 1024)

def check_ffmpeg_availability():
    """Check if FFmpeg and FFprobe are available"""
    try:
        # Check for local FFmpeg installation first (faster)
        local_ffmpeg = os.path.join(os.path.dirname(__file__), 'ffmpeg', 'ffmpeg.exe')
        local_ffprobe = os.path.join(os.path.dirname(__file__), 'ffmpeg', 'ffprobe.exe')
        
        if os.path.exists(local_ffmpeg) and os.path.exists(local_ffprobe):
            # Quick test to make sure they work
            result = subprocess.run([local_ffmpeg, '-version'], capture_output=True, timeout=3)
            if result.returncode == 0:
                return True, None
        
        # Fallback to system PATH (with timeout)
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True, timeout=3)
        subprocess.run(['ffprobe', '-version'], capture_output=True, check=True, timeout=3)
        return True, None
        
    except Exception as e:
        return False, f"FFmpeg is not available: {str(e)}"

def get_ffmpeg_commands():
    """Get the appropriate FFmpeg and FFprobe commands (system or local)"""
    # Check for local FFmpeg first (since we know it's there)
    local_ffmpeg = os.path.join(os.path.dirname(__file__), 'ffmpeg', 'ffmpeg.exe')
    local_ffprobe = os.path.join(os.path.dirname(__file__), 'ffmpeg', 'ffprobe.exe')
    
    if os.path.exists(local_ffmpeg) and os.path.exists(local_ffprobe):
        return local_ffmpeg, local_ffprobe
    
    # Fallback to system commands
    return 'ffmpeg', 'ffprobe'

def convert_audible_to_mp3(input_file, output_dir, activation_bytes=None):
    """Convert Audible file to MP3 using ffmpeg"""
    try:
        # Check if FFmpeg is available
        ffmpeg_available, error_msg = check_ffmpeg_availability()
        if not ffmpeg_available:
            raise Exception(f"FFmpeg is required but not available: {error_msg}. Please install FFmpeg from https://ffmpeg.org/download.html and add it to your system PATH.")
        
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        temp_mp3 = os.path.join(output_dir, f"{base_name}_temp.mp3")
        
        # Get the correct FFmpeg command
        ffmpeg_cmd, _ = get_ffmpeg_commands()
        
        # Build ffmpeg command
        cmd = [ffmpeg_cmd, '-i', input_file]
        
        # Add activation bytes if provided (for .aax files)
        if activation_bytes and input_file.lower().endswith('.aax'):
            cmd.extend(['-activation_bytes', activation_bytes])
        
        cmd.extend(['-acodec', 'libmp3lame', '-ab', '128k', temp_mp3, '-y'])
        
        # Run conversion
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"FFmpeg error: {result.stderr}")
        
        return temp_mp3
    except Exception as e:
        raise Exception(f"Conversion failed: {str(e)}")

def get_audio_duration(input_file):
    """Get audio duration in seconds using FFmpeg"""
    try:
        _, ffprobe_cmd = get_ffmpeg_commands()
        cmd = [ffprobe_cmd, '-v', 'quiet', '-show_entries', 'format=duration', '-of', 'csv=p=0', input_file]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except Exception as e:
        raise Exception(f"Failed to get audio duration: {str(e)}")

def split_audio_file(input_file, output_dir, max_size_mb=24):
    """Split audio file into chunks of specified size using FFmpeg"""
    try:
        # Get audio duration
        total_duration_seconds = get_audio_duration(input_file)
        
        # Calculate duration per chunk based on file size
        file_size_mb = get_file_size_mb(input_file)
        
        # Calculate chunk duration to achieve target file size
        chunk_duration_seconds = (max_size_mb / file_size_mb) * total_duration_seconds
        
        # Ensure minimum chunk duration (1 minute)
        min_chunk_duration_seconds = 60
        chunk_duration_seconds = max(chunk_duration_seconds, min_chunk_duration_seconds)
        
        chunks = []
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        
        # Split audio into chunks using FFmpeg
        chunk_index = 1
        start_time = 0
        
        while start_time < total_duration_seconds:
            end_time = min(start_time + chunk_duration_seconds, total_duration_seconds)
            duration = end_time - start_time
            
            chunk_filename = f"{base_name}_chunk_{chunk_index:03d}.mp3"
            chunk_path = os.path.join(output_dir, chunk_filename)
            
            # Use FFmpeg to extract chunk
            ffmpeg_cmd, _ = get_ffmpeg_commands()
            cmd = [
                ffmpeg_cmd, '-i', input_file,
                '-ss', str(start_time),
                '-t', str(duration),
                '-acodec', 'libmp3lame',
                '-ab', '128k',
                chunk_path, '-y'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"FFmpeg chunk creation error: {result.stderr}")
            
            chunks.append(chunk_path)
            start_time = end_time
            chunk_index += 1
        
        return chunks
    except Exception as e:
        raise Exception(f"Audio splitting failed: {str(e)}")

def create_zip_archive(file_paths, zip_name):
    """Create a ZIP archive containing all converted files"""
    zip_path = os.path.join(OUTPUT_FOLDER, zip_name)
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in file_paths:
            if os.path.exists(file_path):
                arcname = os.path.basename(file_path)
                zipf.write(file_path, arcname)
    
    return zip_path

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        activation_bytes = request.form.get('activation_bytes', '')
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Only .aax and .aa files are allowed'}), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{timestamp}_{filename}"
        upload_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(upload_path)
        
        # Create output directory for this conversion
        output_dir = os.path.join(OUTPUT_FOLDER, f"conversion_{timestamp}")
        os.makedirs(output_dir, exist_ok=True)
        
        # Convert Audible file to MP3
        print(f"Converting {filename} to MP3...")
        temp_mp3 = convert_audible_to_mp3(upload_path, output_dir, activation_bytes)
        
        # Split into chunks
        print(f"Splitting audio into {MAX_CHUNK_SIZE_MB}MB chunks...")
        chunk_files = split_audio_file(temp_mp3, output_dir, MAX_CHUNK_SIZE_MB)
        
        # Create ZIP archive
        zip_name = f"{os.path.splitext(filename)[0]}_converted.zip"
        zip_path = create_zip_archive(chunk_files, zip_name)
        
        # Clean up temporary files
        os.remove(upload_path)
        os.remove(temp_mp3)
        
        # Get file info
        total_chunks = len(chunk_files)
        total_size_mb = sum(get_file_size_mb(chunk) for chunk in chunk_files)
        
        return jsonify({
            'success': True,
            'message': 'File converted successfully',
            'download_url': f'/download/{zip_name}',
            'total_chunks': total_chunks,
            'total_size_mb': round(total_size_mb, 2),
            'zip_name': zip_name
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    try:
        file_path = os.path.join(OUTPUT_FOLDER, filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/status')
def status():
    ffmpeg_available, ffmpeg_error = check_ffmpeg_availability()
    return jsonify({
        'status': 'running',
        'upload_folder': UPLOAD_FOLDER,
        'output_folder': OUTPUT_FOLDER,
        'max_chunk_size_mb': MAX_CHUNK_SIZE_MB,
        'ffmpeg_available': ffmpeg_available,
        'ffmpeg_error': ffmpeg_error if not ffmpeg_available else None
    })

@app.route('/extract-activation-bytes', methods=['POST'])
def extract_activation_bytes():
    """Extract activation bytes using various methods"""
    try:
        data = request.get_json() or {}
        email = data.get('email')
        password = data.get('password')
        method = data.get('method', 'auto')  # auto, cli, auth, file, manual
        
        extractor = ActivationBytesExtractor()
        
        if method == 'cli':
            result = extractor.method_1_audible_cli()
        elif method == 'auth' and email and password:
            result = extractor.method_2_manual_auth(email, password)
        elif method == 'selenium' and email and password:
            browser = data.get('browser', 'chrome')  # Default to chrome
            debug = data.get('debug', False)
            result = extractor.method_2b_selenium_auth(email, password, browser=browser, debug=debug)
        elif method == 'file':
            result = extractor.method_3_file_search()
        elif method == 'manual':
            # For manual input
            activation_bytes = data.get('activation_bytes')
            if activation_bytes and len(activation_bytes) == 8:
                # Test the provided activation bytes
                if extractor.test_activation_bytes(activation_bytes):
                    result = activation_bytes.upper()
                    extractor.save_activation_bytes(result)
                else:
                    result = activation_bytes.upper()  # Save anyway, might work
                    extractor.save_activation_bytes(result)
            else:
                return jsonify({'error': 'Invalid activation bytes format. Must be 8 hexadecimal characters.'}), 400
        else:
            # Auto mode - try all methods
            result = extractor.extract(email, password)
        
        if result:
            return jsonify({
                'success': True,
                'activation_bytes': result,
                'message': f'Activation bytes extracted successfully: {result}'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Could not extract activation bytes using any available method',
                'suggestions': [
                    'Try providing your Audible email and password',
                    'Use the browser method to find activation bytes manually',
                    'Check if you have .aa files instead (no activation bytes needed)',
                    'Use external tools like AAXtoMP3 or OpenAudible'
                ]
            }), 400
            
    except Exception as e:
        return jsonify({'error': f'Extraction failed: {str(e)}'}), 500

@app.route('/test-activation-bytes', methods=['POST'])
def test_activation_bytes_endpoint():
    """Test if provided activation bytes work with available .aax files"""
    try:
        data = request.get_json()
        activation_bytes = data.get('activation_bytes')
        
        if not activation_bytes:
            return jsonify({'error': 'activation_bytes required'}), 400
        
        if len(activation_bytes) != 8:
            return jsonify({'error': 'Activation bytes must be 8 characters long'}), 400
        
        extractor = ActivationBytesExtractor()
        success = extractor.test_activation_bytes(activation_bytes)
        
        return jsonify({
            'success': success,
            'activation_bytes': activation_bytes.upper(),
            'message': 'Activation bytes work!' if success else 'Could not verify activation bytes (no .aax files found for testing)'
        })
        
    except Exception as e:
        return jsonify({'error': f'Test failed: {str(e)}'}), 500

@app.route('/save-activation-bytes', methods=['POST'])
def save_activation_bytes_endpoint():
    """Save activation bytes to file for future use"""
    try:
        data = request.get_json()
        activation_bytes = data.get('activation_bytes')
        
        if not activation_bytes:
            return jsonify({'error': 'activation_bytes required'}), 400
        
        if len(activation_bytes) != 8:
            return jsonify({'error': 'Activation bytes must be 8 characters long'}), 400
        
        # Save to file
        with open('activation_bytes.txt', 'w') as f:
            f.write(activation_bytes.upper())
        
        return jsonify({
            'success': True,
            'message': f'Activation bytes saved: {activation_bytes.upper()}',
            'file': 'activation_bytes.txt'
        })
        
    except Exception as e:
        return jsonify({'error': f'Save failed: {str(e)}'}), 500

@app.route('/load-activation-bytes', methods=['GET'])
def load_activation_bytes_endpoint():
    """Load saved activation bytes from file"""
    try:
        if os.path.exists('activation_bytes.txt'):
            with open('activation_bytes.txt', 'r') as f:
                activation_bytes = f.read().strip()
            
            if len(activation_bytes) == 8:
                return jsonify({
                    'success': True,
                    'activation_bytes': activation_bytes,
                    'message': 'Activation bytes loaded from file'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Invalid activation bytes in file'
                }), 400
        else:
            return jsonify({
                'success': False,
                'error': 'No saved activation bytes found'
            }), 404
            
    except Exception as e:
        return jsonify({'error': f'Load failed: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
