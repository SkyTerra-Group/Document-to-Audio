import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pygame
from docx import Document
from PyPDF2 import PdfReader
from openai import OpenAI
from dotenv import load_dotenv
import tempfile
import shutil
import uuid
from datetime import datetime
import threading
import time
import subprocess
import sys

class DocumentToSpeech:
    def __init__(self, root):
        self.root = root
        self.root.title("Document to Speech Converter")
        self.root.geometry("600x500")
        
        # Initialize pygame mixer
        pygame.mixer.init()
        
        # Load environment variables
        load_dotenv(override=True)
        
        # Check for API key and provide interface to set it
        self.setup_api_key()
        
        # --- FFMPEG auto-detect and .env update logic ---
        def update_env_ffmpeg_dir(ffmpeg_path):
            ffmpeg_dir = os.path.dirname(ffmpeg_path)
            env_path = os.path.join(os.getcwd(), ".env")
            lines = []
            found = False
            if os.path.exists(env_path):
                with open(env_path, "r") as f:
                    for line in f:
                        if line.startswith("FFMPEG_DIR="):
                            lines.append(f"FFMPEG_DIR={ffmpeg_dir}\n")
                            found = True
                        else:
                            lines.append(line)
            if not found:
                lines.append(f"FFMPEG_DIR={ffmpeg_dir}\n")
            with open(env_path, "w") as f:
                f.writelines(lines)
            print(f"Updated .env with FFMPEG_DIR={ffmpeg_dir}")

        def ensure_ffmpeg():
            # First check system PATH
            ffmpeg_path = shutil.which("ffmpeg")
            if ffmpeg_path:
                print(f"ffmpeg found in system PATH: {ffmpeg_path}")
                update_env_ffmpeg_dir(ffmpeg_path)
                return ffmpeg_path
            
            # Check if running as executable - look in _internal directory
            if getattr(sys, 'frozen', False):
                exe_dir = os.path.dirname(sys.executable)
                ffmpeg_internal = os.path.join(exe_dir, '_internal', 'ffmpeg', 'ffmpeg.exe')
                if os.path.exists(ffmpeg_internal):
                    print(f"ffmpeg found in executable: {ffmpeg_internal}")
                    ffmpeg_dir = os.path.dirname(ffmpeg_internal)
                    os.environ['PATH'] = ffmpeg_dir + os.pathsep + os.environ.get('PATH', '')
                    update_env_ffmpeg_dir(ffmpeg_internal)
                    return ffmpeg_internal
            
            # Check local ffmpeg directory
            local_ffmpeg = os.path.join(os.getcwd(), 'ffmpeg', 'ffmpeg.exe')
            if os.path.exists(local_ffmpeg):
                print(f"ffmpeg found locally: {local_ffmpeg}")
                ffmpeg_dir = os.path.dirname(local_ffmpeg)
                os.environ['PATH'] = ffmpeg_dir + os.pathsep + os.environ.get('PATH', '')
                update_env_ffmpeg_dir(local_ffmpeg)
                return local_ffmpeg
            
            print("ffmpeg not found, installing...")
            self.check_ffmpeg()  # Will prompt install if needed
            ffmpeg_path = shutil.which("ffmpeg")
            if ffmpeg_path:
                print(f"ffmpeg installed at: {ffmpeg_path}")
                update_env_ffmpeg_dir(ffmpeg_path)
                return ffmpeg_path
            else:
                print("ffmpeg installation failed.")
                return None

        print("PATH at runtime:", os.environ["PATH"])
        print("FFMPEG_DIR in .env:", os.getenv("FFMPEG_DIR"))
        print("shutil.which('ffmpeg'):", shutil.which("ffmpeg"))
        print("shutil.which('ffprobe'):", shutil.which("ffprobe"))

        ffmpeg_path = ensure_ffmpeg()
        if ffmpeg_path:
            ffmpeg_dir = os.path.dirname(ffmpeg_path)
            if ffmpeg_dir not in os.environ.get("PATH", ""):
                os.environ["PATH"] += os.pathsep + ffmpeg_dir
        # --- End FFMPEG auto-detect logic ---
        
        # Create main frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        # File selection
        file_frame = ttk.LabelFrame(main_frame, text="Document Selection", padding="10")
        file_frame.pack(fill='x', pady=5)
        
        self.file_path_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.file_path_var, width=50).pack(side='left', padx=5)
        ttk.Button(file_frame, text="Browse", command=self.browse_file).pack(side='left', padx=5)
        
        # Voice settings
        voice_frame = ttk.LabelFrame(main_frame, text="Voice Settings", padding="10")
        voice_frame.pack(fill='x', pady=5)
        
        # OpenAI voice selection
        ttk.Label(voice_frame, text="Voice:").grid(row=0, column=0, sticky='w', padx=5)
        self.voice_var = tk.StringVar(value="nova")
        voices = ttk.Combobox(voice_frame, textvariable=self.voice_var, width=15)
        voices['values'] = ("alloy", "echo", "fable", "onyx", "nova", "shimmer")
        voices.grid(row=0, column=1, sticky='w', padx=5)
        
        # Speed control
        ttk.Label(voice_frame, text="Speed:").grid(row=1, column=0, sticky='w', padx=5)
        self.speed_var = tk.DoubleVar(value=1.3)  # Default to 1.3x
        
        # Speed input frame
        speed_input_frame = ttk.Frame(voice_frame)
        speed_input_frame.grid(row=1, column=1, sticky='w', padx=5)
        
        # Speed text entry
        self.speed_entry = ttk.Entry(speed_input_frame, width=5, textvariable=self.speed_var)
        self.speed_entry.pack(side='left', padx=(0, 5))
        self.speed_entry.bind('<Return>', self.update_speed_from_entry)
        self.speed_entry.bind('<FocusOut>', self.update_speed_from_entry)
        
        # Speed scale
        speed_scale = ttk.Scale(
            speed_input_frame,
            from_=0.5,
            to=3.0,
            variable=self.speed_var,
            orient='horizontal',
            length=150
        )
        speed_scale.pack(side='left', padx=(0, 5))
        
        # Speed indicator
        self.speed_label = ttk.Label(speed_input_frame, text="1.3x")
        self.speed_label.pack(side='left')
        speed_scale.bind('<Motion>', self.update_speed_label)
        speed_scale.bind('<ButtonRelease-1>', self.update_speed_label)
        
        # Status and progress
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill='x', pady=5)
        
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(status_frame, textvariable=self.status_var).pack(side='left')
        
        self.progress = ttk.Progressbar(status_frame, orient='horizontal', length=300, mode='determinate')
        self.progress.pack(side='right', padx=5)
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=10)
        
        ttk.Button(button_frame, text="Convert to Speech", command=self.convert_to_speech).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Stop", command=self.stop_audio).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Save Audio", command=self.save_audio).pack(side='left', padx=5)
        ttk.Button(button_frame, text="API Key Settings", command=self.show_api_settings).pack(side='left', padx=5)
        
        # Initialize variables
        self.current_audio_file = None
        
        # Create default output directory
        self.default_output_dir = os.path.join(os.path.expanduser("~"), "Documents", "Audio Output")
        os.makedirs(self.default_output_dir, exist_ok=True)
        
        # Check for ffmpeg
        self.check_ffmpeg()
        
    def check_ffmpeg(self):
        """Check if ffmpeg/ffprobe are available. If not, offer to download on Windows."""

        import shutil

        ffmpeg_exe = shutil.which("ffmpeg")
        if ffmpeg_exe:
            print(f"ffmpeg detected at: {ffmpeg_exe}")
            return  # Everything is fine

        # At least one of the executables is missing – handle like before
        result = messagebox.askyesno(
            "Missing Dependency",
            "ffmpeg is required for audio processing but was not found.\n\n"
            "Would you like the application to download and install it now?"
        )
        if not result:
            return  # User chose not to install; later ffmpeg calls will error out

        try:
            if sys.platform == 'win32':
                # Download and install ffmpeg for Windows
                import urllib.request
                import zipfile

                temp_dir = os.path.join(os.getcwd(), 'temp_ffmpeg')
                os.makedirs(temp_dir, exist_ok=True)

                url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
                zip_path = os.path.join(temp_dir, "ffmpeg.zip")

                self.status_var.set("Downloading ffmpeg ...")
                self.root.update()
                urllib.request.urlretrieve(url, zip_path)

                self.status_var.set("Extracting ffmpeg ...")
                self.root.update()
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)

                ffmpeg_dir = os.path.join(os.getcwd(), 'ffmpeg')
                os.makedirs(ffmpeg_dir, exist_ok=True)

                for r, dirs, files in os.walk(temp_dir):
                    if 'bin' in dirs:
                        bin_dir = os.path.join(r, 'bin')
                        for file in os.listdir(bin_dir):
                            if file.endswith('.exe'):
                                shutil.copy2(os.path.join(bin_dir, file), os.path.join(ffmpeg_dir, file))

                os.environ['PATH'] += os.pathsep + ffmpeg_dir

                shutil.rmtree(temp_dir)

                messagebox.showinfo("Success", "ffmpeg installed successfully!")
            else:
                messagebox.showinfo(
                    "Installation Instructions",
                    "Please install ffmpeg using your system's package manager:\n\n"
                    "Ubuntu/Debian: sudo apt-get install ffmpeg\n"
                    "MacOS: brew install ffmpeg\n"
                    "Other: Visit https://ffmpeg.org/download.html"
                )
        except Exception as e:
            messagebox.showerror(
                "Installation Error",
                f"Failed to install ffmpeg: {str(e)}\n\n"
                "Please install manually from https://ffmpeg.org/download.html"
            )
        
    def setup_api_key(self):
        """Check for API key and setup interface to manage it"""
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            print("API key loaded:", api_key[:10] + "..." if len(api_key) > 10 else "[short key]")
        else:
            print("No API key found in environment variables")
            # Show API key setup dialog on startup if no key found
            self.root.after(100, self.show_api_settings)
    
    def show_api_settings(self):
        """Show API key settings dialog"""
        import tkinter.simpledialog as simpledialog
        
        current_key = os.getenv("OPENAI_API_KEY", "")
        
        # Create a custom dialog for API key
        dialog = tk.Toplevel(self.root)
        dialog.title("OpenAI API Key Settings")
        dialog.geometry("500x300")
        dialog.resizable(False, False)
        dialog.grab_set()  # Make dialog modal
        
        # Center the dialog
        dialog.transient(self.root)
        dialog.geometry("+%d+%d" % (self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50))
        
        # Instructions
        instructions = tk.Text(dialog, height=6, wrap=tk.WORD, bg='#f0f0f0')
        instructions.pack(fill='x', padx=10, pady=10)
        instructions.insert('1.0', 
            "To use this application, you need an OpenAI API key:\n\n"
            "1. Go to https://platform.openai.com/api-keys\n"
            "2. Create a new API key\n"
            "3. Copy and paste it below\n"
            "4. The key will be saved to a .env file in this directory"
        )
        instructions.config(state='disabled')
        
        # API key input
        tk.Label(dialog, text="OpenAI API Key:").pack(pady=(0, 5))
        
        key_frame = tk.Frame(dialog)
        key_frame.pack(fill='x', padx=10)
        
        self.api_key_var = tk.StringVar(value=current_key)
        key_entry = tk.Entry(key_frame, textvariable=self.api_key_var, show="*", width=60)
        key_entry.pack(side='left', fill='x', expand=True)
        
        # Show/Hide button
        self.show_key = tk.BooleanVar()
        def toggle_key_visibility():
            if self.show_key.get():
                key_entry.config(show="")
                show_btn.config(text="Hide")
            else:
                key_entry.config(show="*")
                show_btn.config(text="Show")
        
        show_btn = tk.Button(key_frame, text="Show", command=toggle_key_visibility)
        show_btn.pack(side='right', padx=(5, 0))
        
        # Buttons
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=20)
        
        def save_key():
            api_key = self.api_key_var.get().strip()
            if api_key:
                # Save to .env file
                env_path = os.path.join(os.getcwd(), ".env")
                
                # Read existing .env content
                env_lines = []
                if os.path.exists(env_path):
                    with open(env_path, 'r') as f:
                        env_lines = f.readlines()
                
                # Update or add API key line
                found = False
                for i, line in enumerate(env_lines):
                    if line.startswith("OPENAI_API_KEY="):
                        env_lines[i] = f"OPENAI_API_KEY={api_key}\n"
                        found = True
                        break
                
                if not found:
                    env_lines.append(f"OPENAI_API_KEY={api_key}\n")
                
                # Write back to file
                with open(env_path, 'w') as f:
                    f.writelines(env_lines)
                
                # Update environment variable for current session
                os.environ["OPENAI_API_KEY"] = api_key
                
                messagebox.showinfo("Success", "API key saved successfully!")
                dialog.destroy()
            else:
                messagebox.showwarning("Warning", "Please enter a valid API key")
        
        def cancel():
            dialog.destroy()
        
        tk.Button(button_frame, text="Save", command=save_key, bg='#4CAF50', fg='white').pack(side='left', padx=5)
        tk.Button(button_frame, text="Cancel", command=cancel).pack(side='left', padx=5)
        
        # Focus on entry
        key_entry.focus_set()
        
        # Handle Enter key
        key_entry.bind('<Return>', lambda e: save_key())
    
    def update_speed_label(self, *args):
        """Update the speed label when the slider is moved."""
        speed = self.speed_var.get()
        self.speed_label.config(text=f"{speed:.1f}x")
    
    def update_speed_from_entry(self, *args):
        """Update speed when user types in the entry field"""
        try:
            speed = float(self.speed_entry.get())
            # Clamp speed to valid range
            speed = max(0.5, min(3.0, speed))
            self.speed_var.set(speed)
            self.update_speed_label()
        except ValueError:
            # Reset to current slider value if invalid input
            self.speed_entry.delete(0, tk.END)
            self.speed_entry.insert(0, f"{self.speed_var.get():.1f}")
        
    def browse_file(self):
        """Open file dialog to select a document."""
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("Text Files", "*.txt"),
                ("Word Documents", "*.docx"),
                ("PDF Files", "*.pdf"),
                ("All Files", "*.*")
            ]
        )
        if file_path:
            self.file_path_var.set(file_path)
            
    def extract_text(self, file_path):
        """Extract text from different file types."""
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
            
    def convert_to_speech(self):
        """Convert the document text to speech using OpenAI TTS."""
        try:
            # Stop any current playback
            self.stop_audio()
            
            # Get file path
            file_path = self.file_path_var.get()
            if not file_path:
                messagebox.showwarning("Warning", "Please select a document first")
                return
                
            # Extract text
            self.status_var.set("Extracting text from document...")
            self.progress['value'] = 10
            self.root.update()
            
            text = self.extract_text(file_path)
            if not text.strip():
                messagebox.showwarning("Warning", "No text content found in document")
                return
                
            # Get OpenAI API key
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if not openai_api_key:
                messagebox.showerror("Error", "OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
                return
                
            # Initialize OpenAI client
            client = OpenAI(api_key=openai_api_key)
            
            # Create audio directory
            audio_dir = os.path.join(os.getcwd(), "audio_output")
            os.makedirs(audio_dir, exist_ok=True)
            
            # Create unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            random_id = uuid.uuid4().hex[:8]
            
            # Split text into chunks (OpenAI has a 4096 char limit)
            chunk_size = 4000  # Slightly less than limit to be safe
            chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
            total_chunks = len(chunks)
            
            # Process each chunk
            audio_files = []
            for i, chunk in enumerate(chunks):
                self.status_var.set(f"Processing chunk {i+1} of {total_chunks}...")
                self.progress['value'] = (i / total_chunks) * 80 + 10  # Scale progress from 10-90%
                self.root.update()
                
                chunk_output_path = os.path.join(audio_dir, f"tts_chunk_{i}_{timestamp}_{random_id}.mp3")
                
                # Convert chunk to speech
                response = client.audio.speech.create(
                    model="tts-1",
                    voice=self.voice_var.get(),
                    input=chunk
                )
                
                # Save chunk audio file
                with open(chunk_output_path, 'wb') as f:
                    for chunk in response.iter_bytes():
                        f.write(chunk)
                
                audio_files.append(chunk_output_path)
            
            # Combine all audio files using ffmpeg
            self.status_var.set("Combining audio files...")
            self.progress['value'] = 90
            self.root.update()
            
            try:
                # Create a file list for ffmpeg
                file_list_path = os.path.join(audio_dir, f"file_list_{timestamp}_{random_id}.txt")
                with open(file_list_path, 'w') as f:
                    for audio_file in audio_files:
                        f.write(f"file '{audio_file}'\n")
                
                # Output path for combined file
                final_output_path = os.path.join(audio_dir, f"tts_final_{timestamp}_{random_id}.mp3")
                
                # Use ffmpeg to concatenate files with better error handling
                ffmpeg_cmd = [
                    'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
                    '-i', file_list_path, '-c', 'copy', final_output_path
                ]
                
                result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"FFmpeg concat error: {result.stderr}")
                    # Try alternative method without -c copy
                    ffmpeg_cmd_alt = [
                        'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
                        '-i', file_list_path, '-acodec', 'mp3', final_output_path
                    ]
                    result = subprocess.run(ffmpeg_cmd_alt, capture_output=True, text=True)
                    if result.returncode != 0:
                        raise subprocess.CalledProcessError(result.returncode, ffmpeg_cmd_alt, result.stderr)
                
                # Apply speed adjustment if needed
                speed = self.speed_var.get()
                if abs(speed - 1.0) > 0.01:  # Only adjust if significantly different from 1.0
                    speed_adjusted_path = os.path.join(audio_dir, f"tts_speed_{timestamp}_{random_id}.mp3")
                    
                    # Handle speed changes greater than 2.0x by chaining atempo filters
                    if speed > 2.0:
                        # Chain multiple atempo filters for speeds > 2.0
                        atempo_chain = f'atempo=2.0,atempo={speed/2.0}'
                    elif speed < 0.5:
                        # Chain multiple atempo filters for speeds < 0.5
                        atempo_chain = f'atempo=0.5,atempo={speed/0.5}'
                    else:
                        atempo_chain = f'atempo={speed}'
                    
                    speed_cmd = [
                        'ffmpeg', '-y', '-i', final_output_path,
                        '-filter:a', atempo_chain, speed_adjusted_path
                    ]
                    
                    result = subprocess.run(speed_cmd, capture_output=True, text=True)
                    if result.returncode != 0:
                        print(f"Speed adjustment error: {result.stderr}")
                        raise subprocess.CalledProcessError(result.returncode, speed_cmd, result.stderr)
                    
                    # Replace final output with speed-adjusted version
                    os.replace(speed_adjusted_path, final_output_path)
                
                # Clean up temporary files
                os.remove(file_list_path)
                for audio_file in audio_files:
                    try:
                        os.remove(audio_file)
                    except:
                        pass
                
                self.current_audio_file = final_output_path
                
                # Create a descriptive filename based on the input document
                input_filename = os.path.splitext(os.path.basename(file_path))[0]
                final_filename = f"{input_filename}_audio_{timestamp}.mp3"
                final_save_path = os.path.join(self.default_output_dir, final_filename)
                
                # Copy the file to the default output directory
                shutil.copy2(final_output_path, final_save_path)
                
                # Play the combined audio
                pygame.mixer.quit()
                pygame.mixer.init()
                pygame.mixer.music.load(final_output_path)
                pygame.mixer.music.play()
                
                self.status_var.set(f"Playing complete audio at {speed}x speed...")
                
                # Show success message with file location
                messagebox.showinfo(
                    "Success",
                    f"Audio file has been saved to:\n{final_save_path}\n\n"
                    "The file will remain in the temporary directory until you close the application."
                )
                
            except subprocess.CalledProcessError as e:
                raise Exception(f"Error combining audio files: {e.stderr.decode()}")
            except Exception as e:
                raise Exception(f"Error processing audio: {str(e)}")
            
            self.progress['value'] = 100
            self.root.update()
            
        except Exception as e:
            error_msg = str(e)
            print(f"Error in conversion: {error_msg}")
            messagebox.showerror("Error", f"Error converting to speech: {error_msg}")
            self.status_var.set("Error in conversion")
            self.progress['value'] = 0
            
    def stop_audio(self):
        """Stop audio playback."""
        try:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
                self.status_var.set("Audio playback stopped")
        except Exception as e:
            self.status_var.set(f"Error stopping audio: {str(e)}")
            
    def save_audio(self):
        """Save the current audio as an MP3 file."""
        if not self.current_audio_file:
            messagebox.showwarning("Warning", "No audio has been generated yet")
            return
            
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".mp3",
                filetypes=[("MP3 Files", "*.mp3")],
                initialdir=self.default_output_dir
            )
            
            if not file_path:
                return
                
            with open(self.current_audio_file, 'rb') as src_file:
                with open(file_path, 'wb') as dst_file:
                    dst_file.write(src_file.read())
                    
            self.status_var.set(f"Audio saved as: {os.path.basename(file_path)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error saving audio: {str(e)}")
            self.status_var.set("Error saving audio")

if __name__ == "__main__":
    root = tk.Tk()
    app = DocumentToSpeech(root)
    root.mainloop() 