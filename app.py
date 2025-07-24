import os
import uuid
import tempfile
import shutil
import subprocess
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
from docx import Document
from PyPDF2 import PdfReader
from openai import OpenAI
from dotenv import load_dotenv
# Optional AWS imports for future use
try:
    import boto3
    from botocore.exceptions import NoCredentialsError
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False
import logging

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-change-this')

# Configuration
UPLOAD_FOLDER = 'uploads'
AUDIO_FOLDER = 'audio_output'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['AUDIO_FOLDER'] = AUDIO_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Create directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(AUDIO_FOLDER, exist_ok=True)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentToSpeechApp:
    def __init__(self):
        self.openai_client = None
        self.setup_openai()
        
    def setup_openai(self):
        """Initialize OpenAI client"""
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            self.openai_client = OpenAI(api_key=api_key)
            logger.info("OpenAI client initialized")
        else:
            logger.warning("OpenAI API key not found")
            
    def allowed_file(self, filename):
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
               
    def extract_text(self, file_path):
        """Extract text from different file types"""
        try:
            if file_path.lower().endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
                    
            elif file_path.lower().endswith('.docx'):
                doc = Document(file_path)
                return '\n'.join([para.text for para in doc.paragraphs])
                
            elif file_path.lower().endswith('.pdf'):
                reader = PdfReader(file_path)
                text = []
                for page in reader.pages:
                    text.append(page.extract_text())
                return '\n'.join(text)
                
            else:
                raise ValueError("Unsupported file type")
                
        except Exception as e:
            raise Exception(f"Error extracting text: {str(e)}")
            
    def get_test_text(self, full_text, max_chars=500):
        """Get first portion of text for testing (roughly first paragraph or few sentences)"""
        if len(full_text) <= max_chars:
            return full_text
            
        # Try to break at a sentence boundary
        text_portion = full_text[:max_chars]
        last_period = text_portion.rfind('.')
        last_newline = text_portion.rfind('\n')
        
        # Use the latest sentence or paragraph break
        break_point = max(last_period, last_newline)
        if break_point > max_chars * 0.7:  # At least 70% of desired length
            return full_text[:break_point + 1].strip()
        else:
            return text_portion.strip() + "..."
            
    def text_to_speech(self, text, voice="nova", speed=1.0, is_test=False):
        """Convert text to speech using OpenAI TTS"""
        if not self.openai_client:
            raise Exception("OpenAI client not initialized. Please check your API key.")
            
        try:
            # Create unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            random_id = uuid.uuid4().hex[:8]
            test_prefix = "test_" if is_test else ""
            
            # For long text, split into chunks (OpenAI TTS limit is 4096 characters)
            chunk_size = 4000  # Stay under the 4096 character limit
            if len(text) > chunk_size:
                chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
                audio_files = []
                
                for i, chunk in enumerate(chunks):
                    chunk_filename = f"{test_prefix}tts_chunk_{i}_{timestamp}_{random_id}.mp3"
                    chunk_path = os.path.join(app.config['AUDIO_FOLDER'], chunk_filename)
                    
                    response = self.openai_client.audio.speech.create(
                        model="tts-1",
                        voice=voice,
                        input=chunk
                    )
                    
                    with open(chunk_path, 'wb') as f:
                        for audio_chunk in response.iter_bytes():
                            f.write(audio_chunk)
                    
                    audio_files.append(chunk_path)
                
                # Combine audio files
                final_filename = f"{test_prefix}tts_final_{timestamp}_{random_id}.mp3"
                final_path = os.path.join(app.config['AUDIO_FOLDER'], final_filename)
                
                self.combine_audio_files(audio_files, final_path, speed)
                
                # Clean up chunk files
                for chunk_file in audio_files:
                    try:
                        os.remove(chunk_file)
                    except:
                        pass
                        
                return final_path
                
            else:
                # Single chunk processing
                filename = f"{test_prefix}tts_{timestamp}_{random_id}.mp3"
                file_path = os.path.join(app.config['AUDIO_FOLDER'], filename)
                
                response = self.openai_client.audio.speech.create(
                    model="tts-1",
                    voice=voice,
                    input=text
                )
                
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_bytes():
                        f.write(chunk)
                
                # Apply speed adjustment if needed
                if abs(speed - 1.0) > 0.01:
                    file_path = self.adjust_audio_speed(file_path, speed)
                
                return file_path
                
        except Exception as e:
            logger.error(f"Error in text_to_speech: {str(e)}")
            raise Exception(f"Error converting text to speech: {str(e)}")
            
    def combine_audio_files(self, audio_files, output_path, speed=1.0):
        """Combine multiple audio files using ffmpeg, with fallback if ffmpeg not available"""
        try:
            # Check if ffmpeg is available
            try:
                subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                # ffmpeg not available, use simple fallback
                logger.warning("ffmpeg not available, using first audio chunk only")
                if audio_files:
                    # Just use the first chunk as a fallback
                    shutil.copy2(audio_files[0], output_path)
                    return output_path
                else:
                    raise Exception("No audio files to combine")
            
            # Create file list for ffmpeg
            file_list_path = output_path.replace('.mp3', '_filelist.txt')
            with open(file_list_path, 'w') as f:
                for audio_file in audio_files:
                    f.write(f"file '{audio_file}'\n")
            
            # Combine files
            ffmpeg_cmd = [
                'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
                '-i', file_list_path, '-c', 'copy', output_path
            ]
            
            result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                # Try alternative method
                ffmpeg_cmd_alt = [
                    'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
                    '-i', file_list_path, '-acodec', 'mp3', output_path
                ]
                result = subprocess.run(ffmpeg_cmd_alt, capture_output=True, text=True)
                if result.returncode != 0:
                    raise subprocess.CalledProcessError(result.returncode, ffmpeg_cmd_alt, result.stderr)
            
            # Apply speed adjustment
            if abs(speed - 1.0) > 0.01:
                output_path = self.adjust_audio_speed(output_path, speed)
            
            # Clean up file list
            try:
                os.remove(file_list_path)
            except:
                pass
                
            return output_path
            
        except Exception as e:
            logger.error(f"Error combining audio files: {str(e)}")
            raise Exception(f"Error combining audio files: {str(e)}")
            
    def adjust_audio_speed(self, input_path, speed):
        """Adjust audio playback speed using ffmpeg"""
        try:
            # Check if ffmpeg is available
            try:
                subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                logger.warning("ffmpeg not available, skipping speed adjustment")
                return input_path
            
            output_path = input_path.replace('.mp3', f'_speed{speed}.mp3')
            
            # Handle different speed ranges
            if speed > 2.0:
                atempo_chain = f'atempo=2.0,atempo={speed/2.0}'
            elif speed < 0.5:
                atempo_chain = f'atempo=0.5,atempo={speed/0.5}'
            else:
                atempo_chain = f'atempo={speed}'
            
            speed_cmd = [
                'ffmpeg', '-y', '-i', input_path,
                '-filter:a', atempo_chain, output_path
            ]
            
            result = subprocess.run(speed_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"Speed adjustment error: {result.stderr}")
                return input_path  # Return original if speed adjustment fails
            
            # Replace original with speed-adjusted version
            os.replace(output_path, input_path)
            return input_path
            
        except Exception as e:
            logger.error(f"Error adjusting audio speed: {str(e)}")
            return input_path  # Return original if speed adjustment fails

# Initialize the document to speech app
doc_to_speech = DocumentToSpeechApp()

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and text extraction"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not doc_to_speech.allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed. Please use .txt, .pdf, or .docx files.'}), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{timestamp}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        # Extract text
        full_text = doc_to_speech.extract_text(file_path)
        if not full_text.strip():
            os.remove(file_path)
            return jsonify({'error': 'No text content found in document'}), 400
        
        # Get test text (first portion)
        test_text = doc_to_speech.get_test_text(full_text)
        
        return jsonify({
            'success': True,
            'filename': unique_filename,
            'full_text_length': len(full_text),
            'test_text': test_text,
            'test_text_length': len(test_text)
        })
        
    except Exception as e:
        logger.error(f"Error in upload_file: {str(e)}")
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@app.route('/test_speech', methods=['POST'])
def test_speech():
    """Generate test audio from first portion of text"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        voice = data.get('voice', 'nova')
        speed = float(data.get('speed', 1.0))
        
        if not filename:
            return jsonify({'error': 'No filename provided'}), 400
        
        # Get file path
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        # Extract text and get test portion
        full_text = doc_to_speech.extract_text(file_path)
        test_text = doc_to_speech.get_test_text(full_text)
        
        # Generate test audio
        audio_path = doc_to_speech.text_to_speech(test_text, voice, speed, is_test=True)
        
        # Return audio file name for download
        return jsonify({
            'success': True,
            'audio_filename': os.path.basename(audio_path),
            'test_text_length': len(test_text)
        })
        
    except Exception as e:
        logger.error(f"Error in test_speech: {str(e)}")
        return jsonify({'error': f'Error generating test audio: {str(e)}'}), 500

@app.route('/convert_full', methods=['POST'])
def convert_full():
    """Convert full document to speech"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        voice = data.get('voice', 'nova')
        speed = float(data.get('speed', 1.0))
        
        if not filename:
            return jsonify({'error': 'No filename provided'}), 400
        
        # Get file path
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        # Extract full text
        full_text = doc_to_speech.extract_text(file_path)
        
        # Generate full audio
        audio_path = doc_to_speech.text_to_speech(full_text, voice, speed, is_test=False)
        
        return jsonify({
            'success': True,
            'audio_filename': os.path.basename(audio_path),
            'full_text_length': len(full_text)
        })
        
    except Exception as e:
        logger.error(f"Error in convert_full: {str(e)}")
        return jsonify({'error': f'Error converting full document: {str(e)}'}), 500

@app.route('/download/<filename>')
def download_file(filename):
    """Download generated audio file"""
    try:
        file_path = os.path.join(app.config['AUDIO_FOLDER'], filename)
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(file_path, as_attachment=True)
        
    except Exception as e:
        logger.error(f"Error in download_file: {str(e)}")
        return jsonify({'error': f'Error downloading file: {str(e)}'}), 500

@app.route('/health')
def health_check():
    """Health check endpoint for AWS"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    # Development server - use environment PORT or default to 5000
    port = int(os.getenv('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)