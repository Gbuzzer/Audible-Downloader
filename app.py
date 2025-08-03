import os
import tempfile
import shutil
import logging
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

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

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

def convert_audible_file(input_file, output_dir, activation_bytes=None, output_format='mp3'):
    """Convert Audible file to specified format using ffmpeg with fallback methods"""
    app.logger.info(f"Starting conversion of {input_file} to {output_format}")
    
    # First try the standard method
    try:
        app.logger.info("Attempting standard conversion method...")
        return _convert_with_standard_method(input_file, output_dir, activation_bytes, output_format)
    except Exception as e:
        app.logger.warning(f"Standard conversion failed: {str(e)}")
        app.logger.info("Trying fallback method for problematic AAC streams...")
        
        # Try fallback method
        try:
            app.logger.info("Calling _convert_with_fallback_method...")
            return _convert_with_fallback_method(input_file, output_dir, activation_bytes, output_format)
        except Exception as fallback_error:
            app.logger.error(f"All conversion methods failed. Standard error: {str(e)}, Fallback error: {str(fallback_error)}")
            raise Exception(f"All conversion methods failed. This .aax file may use an incompatible DRM scheme or be corrupted. Last error: {str(fallback_error)}")

def _convert_with_standard_method(input_file, output_dir, activation_bytes=None, output_format='mp3'):
    """Standard conversion method"""
    app.logger.info(f"*** STARTING STANDARD CONVERSION: {input_file} to {output_format} ***")
    
    # Check if FFmpeg is available
    ffmpeg_available, error_msg = check_ffmpeg_availability()
    if not ffmpeg_available:
        raise Exception(f"FFmpeg is required but not available: {error_msg}. Please install FFmpeg from https://ffmpeg.org/download.html and add it to your system PATH.")
    
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    temp_output = os.path.join(output_dir, f"{base_name}_temp.{output_format}")
    
    # Get the correct FFmpeg command
    ffmpeg_cmd, _ = get_ffmpeg_commands()
    
    # Build ffmpeg command - activation_bytes MUST come before -i
    cmd = [ffmpeg_cmd]
    if activation_bytes and input_file.lower().endswith('.aax'):
        cmd.extend(['-activation_bytes', activation_bytes])
    
    # Add error resilience flags to handle AAC decoding issues
    cmd.extend(['-err_detect', 'ignore_err', '-fflags', '+igndts+ignidx'])
    cmd.extend(['-i', input_file])
    
    # Set codec and options based on output format
    if output_format.lower() == 'mp3':
        cmd.extend(['-c:a', 'libmp3lame', '-b:a', '128k'])
    elif output_format.lower() == 'm4b':
        # M4B format with AAC codec, preserving chapters
        cmd.extend(['-c:a', 'aac', '-b:a', '128k', '-c:v', 'copy'])
    else:
        raise Exception(f"Unsupported output format: {output_format}")
    
    cmd.extend([temp_output, '-y'])
    
    app.logger.info(f"Running FFmpeg command: {' '.join(cmd)}")
    
    # Run conversion with proper stdin handling, encoding, and timeout
    result = subprocess.run(cmd, capture_output=True, text=True, check=False, 
                          stdin=subprocess.DEVNULL, timeout=900, 
                          encoding='utf-8', errors='replace')  # Handle encoding issues
    
    if result.returncode != 0:
        app.logger.error(f"FFmpeg command failed with return code {result.returncode}")
        app.logger.error(f"FFmpeg stdout: {result.stdout}")
        app.logger.error(f"FFmpeg stderr: {result.stderr}")
        
        # Provide more helpful error messages
        error_msg = "FFmpeg conversion failed"
        if result.stderr:
            if "activation_bytes" in result.stderr.lower():
                error_msg = "Invalid activation bytes - please check your activation bytes are correct for this file"
            elif "invalid data" in result.stderr.lower():
                error_msg = "Invalid or corrupted audio file - the .aax file may be damaged"
            else:
                error_msg = f"FFmpeg error: {result.stderr}"
        elif result.returncode == 4294967274:  # Common Windows error code
            error_msg = "FFmpeg process was terminated - this may be due to encoding issues or wrong activation bytes"
        
        raise Exception(error_msg)
    
    app.logger.info(f"FFmpeg conversion to {output_format.upper()} successful.")
    return temp_output

def _convert_with_standard_method_DISABLED(input_file, output_dir, activation_bytes=None, output_format='mp3'):
    """Standard conversion method"""
    # Check if FFmpeg is available
    ffmpeg_available, error_msg = check_ffmpeg_availability()
    if not ffmpeg_available:
        raise Exception(f"FFmpeg is required but not available: {error_msg}. Please install FFmpeg from https://ffmpeg.org/download.html and add it to your system PATH.")
    
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    temp_output = os.path.join(output_dir, f"{base_name}_temp.{output_format}")
    
    # Get the correct FFmpeg command
    ffmpeg_cmd, _ = get_ffmpeg_commands()
    
    # Build ffmpeg command - activation_bytes MUST come before -i
    cmd = [ffmpeg_cmd]
    if activation_bytes and input_file.lower().endswith('.aax'):
        cmd.extend(['-activation_bytes', activation_bytes])
    
    cmd.extend(['-i', input_file])
    
    # Set codec and options based on output format
    if output_format.lower() == 'mp3':
        cmd.extend(['-c:a', 'libmp3lame', '-b:a', '128k'])
    elif output_format.lower() == 'm4b':
        # M4B format with AAC codec, preserving chapters
        cmd.extend(['-c:a', 'aac', '-b:a', '128k', '-c:v', 'copy'])
    else:
        raise Exception(f"Unsupported output format: {output_format}")
    
    cmd.extend([temp_output, '-y'])
    
    app.logger.info(f"Running FFmpeg command: {' '.join(cmd)}")
    
    # Run conversion with proper stdin handling, encoding, and timeout
    result = subprocess.run(cmd, capture_output=True, text=True, check=False, 
                          stdin=subprocess.DEVNULL, timeout=900, 
                          encoding='utf-8', errors='replace')  # Handle encoding issues
    
    if result.returncode != 0:
        app.logger.error(f"FFmpeg command failed with return code {result.returncode}")
        app.logger.error(f"FFmpeg stdout: {result.stdout}")
        app.logger.error(f"FFmpeg stderr: {result.stderr}")
        
        # Provide more helpful error messages
        error_msg = "FFmpeg conversion failed"
        if result.stderr:
            if "activation_bytes" in result.stderr.lower():
                error_msg = "Invalid activation bytes - please check your activation bytes are correct for this file"
            elif "invalid data" in result.stderr.lower():
                error_msg = "Invalid or corrupted audio file - the .aax file may be damaged"
            else:
                error_msg = f"FFmpeg error: {result.stderr}"
        elif result.returncode == 4294967274:  # Common Windows error code
            error_msg = "FFmpeg process was terminated - this may be due to encoding issues or wrong activation bytes"
        
        raise Exception(error_msg)
def _convert_with_fallback_method(input_file, output_dir, activation_bytes=None, output_format='mp3'):
    """Fallback conversion method for older .aax files with problematic AAC streams"""
    app.logger.info("Starting fallback conversion method...")
    
    # Check if FFmpeg is available
    ffmpeg_available, error_msg = check_ffmpeg_availability()
    if not ffmpeg_available:
        raise Exception(f"FFmpeg is required but not available: {error_msg}")
    
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    temp_output = os.path.join(output_dir, f"{base_name}_fallback.{output_format}")
    
    # Get the correct FFmpeg command
    ffmpeg_cmd, _ = get_ffmpeg_commands()
    
    # Try multiple fallback strategies
    fallback_strategies = [
        # Strategy 1: Maximum error tolerance with different decoder
        {
            'name': 'Max error tolerance + alternative decoder',
            'extra_flags': ['-err_detect', 'ignore_err', '-fflags', '+igndts+ignidx+genpts', 
                          '-max_muxing_queue_size', '4096', '-probesize', '50M', '-analyzeduration', '100M']
        },
        # Strategy 2: Force stream copy first, then convert
        {
            'name': 'Two-pass: extract then convert',
            'extra_flags': ['-c', 'copy', '-avoid_negative_ts', 'make_zero', '-fflags', '+genpts']
        },
        # Strategy 3: Use different audio decoder with error resilience
        {
            'name': 'Alternative audio processing',
            'extra_flags': ['-err_detect', 'ignore_err', '-fflags', '+igndts+ignidx', 
                          '-ac', '2', '-ar', '44100', '-threads', '1']
        },
        # Strategy 4: Minimal processing with raw extraction
        {
            'name': 'Minimal processing extraction',
            'extra_flags': ['-vn', '-sn', '-dn', '-ignore_unknown', '-f', output_format]
        }
    ]
    
    for strategy in fallback_strategies:
        app.logger.info(f"Trying fallback strategy: {strategy['name']}")
        
        # Build ffmpeg command
        cmd = [ffmpeg_cmd]
        if activation_bytes and input_file.lower().endswith('.aax'):
            cmd.extend(['-activation_bytes', activation_bytes])
        
        cmd.extend(['-i', input_file])
        cmd.extend(strategy['extra_flags'])
        
        # Set output codec if not copying or using raw format
        if 'copy' not in strategy['extra_flags'] and '-f' not in strategy['extra_flags']:
            if output_format.lower() == 'mp3':
                cmd.extend(['-c:a', 'libmp3lame', '-b:a', '128k'])
            elif output_format.lower() == 'm4b':
                cmd.extend(['-c:a', 'aac', '-b:a', '128k'])
        
        cmd.extend([temp_output, '-y'])
        
        app.logger.info(f"Running fallback FFmpeg command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False,
                                  stdin=subprocess.DEVNULL, timeout=900,
                                  encoding='utf-8', errors='replace')
            
            if result.returncode == 0:
                app.logger.info(f"Fallback strategy '{strategy['name']}' succeeded!")
                return temp_output
            else:
                app.logger.warning(f"Fallback strategy '{strategy['name']}' failed with return code {result.returncode}")
                app.logger.warning(f"Stderr: {result.stderr[:500]}...")  # Truncate long error messages
                
        except subprocess.TimeoutExpired:
            app.logger.error(f"Fallback strategy '{strategy['name']}' timed out")
        except Exception as e:
            app.logger.error(f"Fallback strategy '{strategy['name']}' failed with exception: {str(e)}")
    
    # If all strategies failed
    raise Exception("All fallback conversion strategies failed. This .aax file may use an incompatible DRM scheme or have severe corruption.")

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

@app.route('/test')
def test():
    app.logger.info("Test route called!")
    return jsonify({'status': 'Flask app is working!', 'timestamp': datetime.now().isoformat()})

@app.route('/upload', methods=['POST'])
def upload_file():
    temp_dir = None
    try:
        app.logger.info("--- New upload request received ---")
        if 'file' not in request.files:
            app.logger.error("No file part in request")
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        activation_bytes = request.form.get('activation_bytes', '')
        app.logger.info(f"File: {file.filename}, Activation Bytes: {'Yes' if activation_bytes else 'No'}")

        if file.filename == '':
            app.logger.error("No file selected")
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            app.logger.error(f"Invalid file type: {file.filename}")
            return jsonify({'error': 'Invalid file type. Only .aax and .aa files are allowed'}), 400
        
        filename = secure_filename(file.filename)
        
        # Create a unique temporary directory for this conversion
        temp_dir = tempfile.mkdtemp(prefix="conversion_")
        app.logger.info(f"Created temporary directory: {temp_dir}")

        # Save uploaded file to the temporary directory
        upload_path = os.path.join(temp_dir, filename)
        file.save(upload_path)
        app.logger.info(f"Saved uploaded file to: {upload_path}")
        
        # Get output format from form
        output_format = request.form.get('output_format', 'mp3').lower()
        if output_format not in ['mp3', 'm4b']:
            output_format = 'mp3'  # Default fallback
        
        # Convert Audible file to specified format (no chunking at this stage)
        app.logger.info(f"Converting {filename} to {output_format.upper()}...")
        temp_output = convert_audible_file(upload_path, temp_dir, activation_bytes, output_format)
        
        # Always create a single output file first
        final_filename = f"{os.path.splitext(filename)[0]}.{output_format}"
        final_path = os.path.join(OUTPUT_FOLDER, final_filename)
        
        # Move the converted file to the final output directory
        shutil.move(temp_output, final_path)
        app.logger.info(f"Moved final MP3 to: {final_path}")
        
        total_size_mb = get_file_size_mb(final_path)

        response_data = {
            'success': True,
            'message': 'File converted successfully',
            'download_url': f'/download/{final_filename}',
            'filename': final_filename,
            'output_format': output_format.upper(),
            'total_size_mb': round(total_size_mb, 2),
            'can_chunk': total_size_mb > MAX_CHUNK_SIZE_MB  # Show chunk option if file is large
        }

        app.logger.info("Conversion process successful.")
        return jsonify(response_data)
        
    except Exception as e:
        app.logger.error(f"An error occurred during upload/conversion: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500
    finally:
        # Cleanup: remove the temporary directory and its contents
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                app.logger.info(f"Successfully cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                app.logger.error(f"Failed to clean up temporary directory {temp_dir}: {e}")

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

@app.route('/chunk-file', methods=['POST'])
def chunk_file():
    """Chunk an existing MP3 file into smaller pieces"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        
        if not filename:
            return jsonify({'error': 'filename required'}), 400
        
        file_path = os.path.join(OUTPUT_FOLDER, filename)
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        app.logger.info(f"Chunking file: {filename}")
        
        # Create temporary directory for chunking
        temp_dir = tempfile.mkdtemp(prefix="chunking_")
        
        try:
            # Split the MP3 file into chunks
            chunk_files = split_audio_file(file_path, temp_dir, MAX_CHUNK_SIZE_MB)
            app.logger.info(f"Created {len(chunk_files)} chunks.")
            
            # Create ZIP archive
            base_name = os.path.splitext(filename)[0]
            zip_name = f"{base_name}_chunked.zip"
            zip_path = create_zip_archive(chunk_files, zip_name)
            app.logger.info(f"Created ZIP archive: {zip_path}")
            
            total_chunks = len(chunk_files)
            total_size_mb = sum(get_file_size_mb(chunk) for chunk in chunk_files)
            
            return jsonify({
                'success': True,
                'message': f'File chunked into {total_chunks} pieces successfully',
                'download_url': f'/download/{zip_name}',
                'zip_name': zip_name,
                'total_chunks': total_chunks,
                'total_size_mb': round(total_size_mb, 2)
            })
            
        finally:
            # Clean up temporary directory
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                app.logger.info(f"Cleaned up chunking temp directory: {temp_dir}")
        
    except Exception as e:
        app.logger.error(f"Chunking failed: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

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

@app.route('/extract-activation-bytes', methods=['POST'])
def extract_activation_bytes_endpoint():
    """Extract activation bytes using audible-cli"""
    try:
        data = request.get_json()
        method = data.get('method', 'cli')
        
        if method != 'cli':
            return jsonify({
                'success': False,
                'error': 'Only audible-cli method is supported'
            }), 400
        
        app.logger.info("Attempting to extract activation bytes using audible-cli...")
        
        # Try to use audible-cli to get activation bytes
        try:
            # Check if audible-cli is available
            result = subprocess.run(['py', '-m', 'audible_cli', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                return jsonify({
                    'success': False,
                    'error': 'audible-cli not found. Please install it with: pip install audible-cli'
                }), 400
            
            # Try to get activation bytes
            result = subprocess.run(['py', '-m', 'audible_cli', 'activation-bytes'], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                output = result.stdout.strip()
                # Extract 8-character hex string from output
                import re
                hex_match = re.search(r'\b([0-9A-Fa-f]{8})\b', output)
                if hex_match:
                    activation_bytes = hex_match.group(1).upper()
                    
                    # Save to file for future use
                    with open('activation_bytes.txt', 'w') as f:
                        f.write(activation_bytes)
                    
                    app.logger.info(f"Successfully extracted activation bytes: {activation_bytes}")
                    return jsonify({
                        'success': True,
                        'activation_bytes': activation_bytes,
                        'message': 'Activation bytes extracted successfully'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Could not find activation bytes in audible-cli output'
                    }), 400
            else:
                error_msg = result.stderr.strip() if result.stderr else 'Unknown error'
                return jsonify({
                    'success': False,
                    'error': f'audible-cli failed: {error_msg}'
                }), 400
                
        except subprocess.TimeoutExpired:
            return jsonify({
                'success': False,
                'error': 'audible-cli command timed out'
            }), 400
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Error running audible-cli: {str(e)}'
            }), 500
            
    except Exception as e:
        app.logger.error(f"Activation bytes extraction failed: {str(e)}", exc_info=True)
        return jsonify({'error': f'Extraction failed: {str(e)}'}), 500

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
