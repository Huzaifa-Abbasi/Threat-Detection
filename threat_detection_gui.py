#!/usr/bin/env python3
"""
Enhanced AI Threat Detection GUI with Advanced Camera Selection
"""

import tkinter as tk
from tkinter import ttk, messagebox
import cv2
from PIL import Image, ImageTk
import threading
from threat_detection import load_yolo, detect_threat, setup_arduino, EMAIL_CONFIG, send_threat_email, is_email_config_valid, setup_droidcam, test_droidcam_connection as test_droidcam_connection_main
import time
import queue
import os
from datetime import datetime

class EnhancedGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Threat Detection - Enhanced")
        self.root.geometry("1200x800")
        
        # Variables
        self.is_running = False
        self.cap = None
        self.model = None
        self.arduino = None
        self.frame_queue = queue.Queue(maxsize=1)  # Reduced queue size
        self.current_image = None
        self.email_expanded = False
        self.last_email_time = 0  # Email cooldown
        self.email_cooldown = 60  # 60 seconds between emails
        self.source_var = tk.StringVar(value="webcam")
        self.detection_buffer = [False] * 10  # Increased buffer size for more smoothing
        self.hold_counter = 0  # Hold period counter
        self.hold_period = 10  # Number of frames to hold alert after last detection
        self.last_smoothed_threat = False
        self.last_threat_status = None
        self.first_email_sent = False  # Track if first email was sent for popup
        
        # Statistics
        self.frame_count = 0
        self.threat_count = 0
        self.total_threats_detected = 0
        self.start_time = time.time()
        
        # Camera configuration
        self.droidcam_url = "http://192.168.1.100:4747/video"
        self.camera_source = "webcam"  # webcam, virtual, ipcam
        
        # Create layout
        self.create_layout()
        
        # Initialize system
        self.initialize_system()
        
        # Start updates
        self.update_display()
        
        # Bind keyboard shortcuts
        self.root.bind('<Key>', self.handle_keyboard)
    
    def create_layout(self):
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Camera frame (left side - takes most space)
        self.camera_frame = ttk.LabelFrame(main_frame, text="Camera Feed")
        self.camera_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self.video_label = ttk.Label(self.camera_frame)
        self.video_label.pack(padx=10, pady=10)
        
        # Statistics frame (below camera)
        stats_frame = ttk.LabelFrame(main_frame, text="Statistics")
        stats_frame.pack(side=tk.LEFT, fill=tk.X, pady=(10, 0))
        
        self.stats_label = ttk.Label(stats_frame, text="Frame: 0 | Threats: 0 | FPS: 0.0")
        self.stats_label.pack(padx=10, pady=5)
        
        # Control panel (right side - fixed width)
        control_frame = ttk.Frame(main_frame, width=350)
        control_frame.pack(side=tk.RIGHT, fill=tk.Y)
        control_frame.pack_propagate(False)  # Prevent shrinking
        
        # Start button
        self.start_button = ttk.Button(control_frame, text="Start Detection", 
                                      command=self.toggle_detection, width=30)
        self.start_button.pack(pady=10)
        
        # Arduino status
        self.arduino_status = ttk.Label(control_frame, text="Arduino: Disconnected")
        self.arduino_status.pack(pady=5)
        
        # Camera source selection
        source_frame = ttk.LabelFrame(control_frame, text="Camera Source")
        source_frame.pack(fill=tk.X, pady=5)
        
        # Camera options
        self.webcam_radio = ttk.Radiobutton(source_frame, text="PC Webcam", variable=self.source_var, 
                                           value="webcam", command=self.on_source_change)
        self.webcam_radio.pack(anchor=tk.W, padx=10, pady=2)
        
        self.virtual_radio = ttk.Radiobutton(source_frame, text="DroidCam Virtual Camera (Recommended)", 
                                            variable=self.source_var, value="virtual", command=self.on_source_change)
        self.virtual_radio.pack(anchor=tk.W, padx=10, pady=2)
        
        self.ipcam_radio = ttk.Radiobutton(source_frame, text="DroidCam IP Camera", variable=self.source_var, 
                                          value="ipcam", command=self.on_source_change)
        self.ipcam_radio.pack(anchor=tk.W, padx=10, pady=2)
        
        # IP Camera configuration
        ipcam_frame = ttk.Frame(source_frame)
        ipcam_frame.pack(fill=tk.X, padx=10, pady=2)
        
        ttk.Label(ipcam_frame, text="IP Address:").pack(anchor=tk.W)
        self.ip_var = tk.StringVar(value="192.168.1.100")
        self.ip_entry = ttk.Entry(ipcam_frame, textvariable=self.ip_var, width=20)
        self.ip_entry.pack(anchor=tk.W, pady=2)
        self.ip_entry.configure(state="disabled")
        
        ttk.Label(ipcam_frame, text="Port:").pack(anchor=tk.W)
        self.port_var = tk.StringVar(value="4747")
        self.port_entry = ttk.Entry(ipcam_frame, textvariable=self.port_var, width=10)
        self.port_entry.pack(anchor=tk.W, pady=2)
        self.port_entry.configure(state="disabled")
        
        # Test connection button
        self.test_ipcam_btn = ttk.Button(ipcam_frame, text="Test DroidCam Connection", 
                                        command=self.test_droidcam_connection, width=25)
        self.test_ipcam_btn.pack(anchor=tk.W, pady=2)
        self.test_ipcam_btn.configure(state="disabled")
        
        # IP Camera status
        self.ipcam_status = ttk.Label(ipcam_frame, text="DroidCam: Not tested", foreground="gray")
        self.ipcam_status.pack(anchor=tk.W, pady=2)
        
        # Email toggle button
        self.email_toggle = ttk.Button(control_frame, text="📧 Show Email Config", 
                                      command=self.toggle_email, width=30)
        self.email_toggle.pack(pady=10)
        
        # Email frame (initially hidden)
        self.email_frame = ttk.LabelFrame(control_frame, text="Email Configuration")
        
        # Email fields
        ttk.Label(self.email_frame, text="Sender:").pack(anchor=tk.W, padx=10, pady=2)
        self.sender_var = tk.StringVar(value=EMAIL_CONFIG['sender_email'])
        self.sender_entry = ttk.Entry(self.email_frame, textvariable=self.sender_var, width=30)
        self.sender_entry.pack(padx=10, pady=2)
        
        ttk.Label(self.email_frame, text="Password:").pack(anchor=tk.W, padx=10, pady=2)
        self.password_var = tk.StringVar(value=EMAIL_CONFIG['sender_password'])
        self.password_entry = ttk.Entry(self.email_frame, textvariable=self.password_var, 
                                      width=30, show="*")
        self.password_entry.pack(padx=10, pady=2)
        
        # Show/Hide Password Checkbox
        self.show_password_var = tk.BooleanVar()
        self.show_password_check = ttk.Checkbutton(self.email_frame, text="Show Password", 
                                                  variable=self.show_password_var, 
                                                  command=self.toggle_password_visibility)
        self.show_password_check.pack(anchor=tk.W, padx=10, pady=2)
        
        ttk.Label(self.email_frame, text="Recipient:").pack(anchor=tk.W, padx=10, pady=2)
        self.recipient_var = tk.StringVar(value=EMAIL_CONFIG['recipient_email'])
        self.recipient_entry = ttk.Entry(self.email_frame, textvariable=self.recipient_var, width=30)
        self.recipient_entry.pack(padx=10, pady=2)
        
        # Email buttons
        btn_frame = ttk.Frame(self.email_frame)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="Save", command=self.save_email).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Test", command=self.test_email).pack(side=tk.LEFT, padx=2)
        
        # Email status
        self.email_status = ttk.Label(self.email_frame, text="Email: Not configured", 
                                     foreground="red")
        self.email_status.pack(pady=5)
        
        # Keyboard shortcuts info
        shortcuts_frame = ttk.LabelFrame(control_frame, text="Keyboard Shortcuts")
        shortcuts_frame.pack(fill=tk.X, pady=5)
        
        shortcuts_text = "Q: Quit\nS: Save Frame\nR: Reset Counters"
        shortcuts_label = ttk.Label(shortcuts_frame, text=shortcuts_text, justify=tk.LEFT)
        shortcuts_label.pack(padx=10, pady=5)
    
    def initialize_system(self):
        try:
            self.model = load_yolo()
            self.arduino = setup_arduino()
            if self.arduino:
                self.arduino_status.config(text="Arduino: Connected", foreground="green")
            else:
                self.arduino_status.config(text="Arduino: Disconnected", foreground="red")
            
            # Load email config
            self.load_email_config()
            
        except Exception as e:
            messagebox.showerror("Error", f"Initialization failed: {e}")
    
    def on_source_change(self):
        """Handle camera source change"""
        source = self.source_var.get()
        
        # Enable/disable IP camera fields
        if source == "ipcam":
            self.ip_entry.configure(state="normal")
            self.port_entry.configure(state="normal")
            self.test_ipcam_btn.configure(state="normal")
        else:
            self.ip_entry.configure(state="disabled")
            self.port_entry.configure(state="disabled")
            self.test_ipcam_btn.configure(state="disabled")
    
    def toggle_detection(self):
        if not self.is_running:
            self.start_detection()
        else:
            self.stop_detection()
    
    def start_detection(self):
        if not self.model:
            messagebox.showerror("Error", "Model not loaded!")
            return
        
        self.is_running = True
        self.start_button.config(text="Stop Detection")
        
        # Setup camera based on selection
        self.cap = self.setup_camera()
        
        if not self.cap or not self.cap.isOpened():
            messagebox.showerror("Error", "Could not open camera!")
            self.stop_detection()
            return
        
        # Reset statistics
        self.frame_count = 0
        self.threat_count = 0
        self.total_threats_detected = 0
        self.start_time = time.time()
        
        threading.Thread(target=self.capture_loop, daemon=True).start()
    
    def setup_camera(self):
        """Setup camera based on selected source"""
        source = self.source_var.get()
        
        if source == "webcam":
            print("Using PC webcam...")
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                print("❌ Failed to open webcam")
                return None
            print("✅ Webcam connection established")
            
        elif source == "virtual":
            print("Using DroidCam Virtual Camera...")
            cap = cv2.VideoCapture(1)  # Virtual camera index
            if not cap.isOpened():
                print("❌ Failed to open DroidCam Virtual Camera")
                print("Make sure DroidCam is installed and running on your PC")
                return None
            
            # Test reading a frame
            ret, frame = cap.read()
            if not ret:
                print("❌ Could not read frame from DroidCam Virtual Camera")
                cap.release()
                return None
                
            print("✅ DroidCam Virtual Camera connection successful!")
            
        elif source == "ipcam":
            print("Using DroidCam IP Camera...")
            
            # First try virtual camera
            print("Trying virtual camera first...")
            cap = cv2.VideoCapture(1)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    print("✅ Virtual camera connection successful!")
                    return cap
                cap.release()
            
            # If virtual camera fails, try IP
            ip = self.ip_var.get().strip()
            port = self.port_var.get().strip()
            if not ip:
                print("❌ IP address is required")
                return None
                
            url = f"http://{ip}:{port}/video"
            print(f"Trying IP connection: {url}")
            
            cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
            if not cap.isOpened():
                # Try RTSP
                rtsp_url = url.replace('http://', 'rtsp://')
                print(f"Trying RTSP connection: {rtsp_url}")
                cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
            
            if not cap.isOpened():
                print("❌ Failed to connect to DroidCam via IP")
                return None
                
            print("✅ DroidCam IP connection successful!")
        
        # Set camera properties
        if cap and cap.isOpened():
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_FPS, 30)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        return cap
    
    def stop_detection(self):
        self.is_running = False
        self.start_button.config(text="Start Detection")
        if self.cap:
            self.cap.release()
            self.cap = None
    
    def capture_loop(self):
        frame_count = 0
        start_time = time.time()
        last_detection = 0
        detection_interval = 0.3  # Run detection every 0.3 seconds for better responsiveness
        while self.is_running:
            ret, frame = self.cap.read()
            if not ret:
                break
            frame_count += 1
            current_time = time.time()
            if current_time - last_detection >= detection_interval:
                try:
                    result = detect_threat(frame, self.model)
                    if result is None:
                        continue
                    processed_frame, threat_detected, threat_details = result
                    last_detection = current_time
                    
                    # Update threat statistics
                    if threat_detected:
                        self.threat_count += 1
                        if self.threat_count == 1:  # First detection in sequence
                            self.total_threats_detected += 1
                    else:
                        self.threat_count = 0
                    
                    self.detection_buffer.pop(0)
                    self.detection_buffer.append(threat_detected)
                    smoothed_threat = sum(self.detection_buffer) >= 2
                    if smoothed_threat:
                        self.hold_counter = self.hold_period
                    elif self.hold_counter > 0:
                        self.hold_counter -= 1
                        smoothed_threat = True
                    self.last_smoothed_threat = smoothed_threat
                    self.last_threat_status = threat_details.get('status')
                    
                    def send_email_bg(frame, threat_details):
                        send_threat_email(frame, threat_details)
                    
                    if (smoothed_threat and hasattr(self, 'email_configured') and self.email_configured and 
                        current_time - self.last_email_time > self.email_cooldown):
                        if not is_email_config_valid():
                            print("[EMAIL] Email config incomplete. Not sending email.")
                            self.email_status.config(text="Email: Config Incomplete", foreground="red")
                            self.show_email_popup("Email configuration is incomplete. Please fill all fields and save.")
                        else:
                            print(f"[EMAIL] Attempting to send email with config: {EMAIL_CONFIG}")
                            try:
                                threading.Thread(target=send_email_bg, args=(processed_frame.copy(), threat_details), daemon=True).start()
                                print("[EMAIL] Email send triggered in background thread.")
                                self.email_status.config(text="Email: Alert Sent (background)", foreground="green")
                                self.last_email_time = current_time
                            except Exception as e:
                                print(f"[EMAIL] Exception during email send: {e}")
                                import traceback
                                traceback.print_exc()
                                self.email_status.config(text="Email: Alert Exception", foreground="red")
                                self.show_email_popup(f"Exception during email send: {e}")
                    
                    # Update frame count
                    self.frame_count = frame_count
                    
                    try:
                        self.frame_queue.put_nowait(processed_frame)
                    except queue.Full:
                        try:
                            self.frame_queue.get_nowait()
                        except:
                            pass
                        try:
                            self.frame_queue.put_nowait(processed_frame)
                        except:
                            pass
                except Exception as e:
                    print(f"Detection error: {e}")
            time.sleep(0.01)  # Reduced sleep time for better responsiveness
    
    def update_display(self):
        if self.is_running:
            try:
                frame = self.frame_queue.get_nowait()
                # Resize frame for better performance
                frame = cv2.resize(frame, (640, 480))
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                img = ImageTk.PhotoImage(image=img)
                self.current_image = img
                self.video_label.config(image=img)
            except queue.Empty:
                pass
            except Exception as e:
                print(f"Display error: {e}")
        
        # Update statistics
        if self.is_running:
            current_time = time.time()
            fps = self.frame_count / (current_time - self.start_time) if current_time > self.start_time else 0
            stats_text = f"Frame: {self.frame_count} | Threats: {self.total_threats_detected} | FPS: {fps:.1f}"
            self.stats_label.config(text=stats_text)
        
        self.root.after(33, self.update_display)  # ~30 FPS display update
    
    def handle_keyboard(self, event):
        """Handle keyboard shortcuts"""
        if event.char.lower() == 's':
            self.save_current_frame()
        elif event.char.lower() == 'r':
            self.reset_counters()
    
    def save_current_frame(self):
        """Save the current frame with threat information"""
        if not self.is_running or self.current_image is None:
            messagebox.showwarning("Warning", "No frame to save. Start detection first.")
            return
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"threat_detection_{timestamp}.jpg"
            
            # Get the current frame from the queue
            try:
                frame = self.frame_queue.get_nowait()
                # Add save confirmation text
                cv2.putText(frame, f"SAVED: {timestamp}", (10, frame.shape[0] - 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.imwrite(filename, frame)
                
                print(f"✅ Frame saved as: {filename}")
                if self.last_threat_status:
                    print(f"   Status: {self.last_threat_status}")
                
                messagebox.showinfo("Success", f"Frame saved as: {filename}")
                
            except queue.Empty:
                messagebox.showwarning("Warning", "No frame available to save.")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save frame: {e}")
    
    def reset_counters(self):
        """Reset all counters and statistics"""
        self.frame_count = 0
        self.threat_count = 0
        self.total_threats_detected = 0
        self.start_time = time.time()
        self.last_email_time = 0
        print("🔄 All counters reset!")
        messagebox.showinfo("Reset", "All counters have been reset!")
    
    def toggle_email(self):
        if self.email_expanded:
            self.email_frame.pack_forget()
            self.email_toggle.config(text="📧 Show Email Config")
            self.email_expanded = False
        else:
            self.email_frame.pack(fill=tk.X, pady=5)
            self.email_toggle.config(text="📧 Hide Email Config")
            self.email_expanded = True
    
    def toggle_password_visibility(self):
        """Toggle password visibility in the password entry"""
        if self.show_password_var.get():
            self.password_entry.config(show="")
        else:
            self.password_entry.config(show="*")
    
    def save_email_config(self):
        try:
            sender = self.sender_var.get().strip()
            password = self.password_var.get().strip()
            recipient = self.recipient_var.get().strip()
            
            if not all([sender, password, recipient]):
                messagebox.showerror("Error", "Please fill all fields!")
                return
            
            # Update config
            EMAIL_CONFIG['sender_email'] = sender
            EMAIL_CONFIG['sender_password'] = password
            EMAIL_CONFIG['recipient_email'] = recipient
            
            # Save to file
            with open("email_config.txt", "w") as f:
                f.write(f"{sender}\n{password}\n{recipient}\n")
            
            self.email_status.config(text="Email: Saved", foreground="green")
            self.email_configured = True
            messagebox.showinfo("Success", "Email configuration saved!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Save failed: {e}")
    
    def load_email_config(self):
        try:
            if os.path.exists("email_config.txt"):
                with open("email_config.txt", "r") as f:
                    lines = f.readlines()
                    if len(lines) >= 3:
                        self.sender_var.set(lines[0].strip())
                        self.password_var.set(lines[1].strip())
                        self.recipient_var.set(lines[2].strip())
                        
                        EMAIL_CONFIG['sender_email'] = lines[0].strip()
                        EMAIL_CONFIG['sender_password'] = lines[1].strip()
                        EMAIL_CONFIG['recipient_email'] = lines[2].strip()
                        
                        self.email_status.config(text="Email: Loaded", foreground="blue")
                        self.email_configured = True
            else:
                self.email_configured = False
        except:
            self.email_status.config(text="Email: Not configured", foreground="red")
            self.email_configured = False
    
    def save_email(self):
        self.save_email_config()
    
    def test_email(self):
        try:
            import smtplib
            sender = self.sender_var.get().strip()
            password = self.password_var.get().strip()
            
            if not sender or not password:
                messagebox.showerror("Error", "Please fill email and password!")
                return
            
            # Test connection with better error handling
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            
            try:
                server.login(sender, password)
                server.quit()
                
                self.email_status.config(text="Email: Test OK", foreground="green")
                messagebox.showinfo("Success", "Email connection test successful!")
                
            except smtplib.SMTPAuthenticationError as e:
                error_code = e.smtp_code
                error_message = e.smtp_error.decode() if isinstance(e.smtp_error, bytes) else str(e.smtp_error)
                
                if "534" in str(error_code) or "5.7.9" in error_message:
                    messagebox.showerror("Authentication Error", 
                                       "Gmail App Password Error!\n\n"
                                       "This usually means:\n"
                                       "1. You're using your regular Gmail password\n"
                                       "2. 2-Step Verification isn't enabled\n"
                                       "3. App password was generated incorrectly\n\n"
                                       "To fix:\n"
                                       "1. Go to Google Account settings\n"
                                       "2. Enable 2-Step Verification\n"
                                       "3. Go to Security > App passwords\n"
                                       "4. Generate new app password for 'Mail'\n"
                                       "5. Use the 16-character password (with spaces)")
                elif "535" in str(error_code):
                    messagebox.showerror("Authentication Error", 
                                       "Invalid email or password!\n\n"
                                       "Make sure you're using an App Password, not your regular Gmail password.")
                else:
                    messagebox.showerror("Authentication Error", f"Login failed: {error_message}")
                
                self.email_status.config(text="Email: Auth Failed", foreground="red")
                
        except Exception as e:
            self.email_status.config(text="Email: Test Failed", foreground="red")
            messagebox.showerror("Error", f"Connection failed: {e}")

    def test_droidcam_connection(self):
        """Test DroidCam connection without starting full detection"""
        self.ipcam_status.config(text="DroidCam: Testing...", foreground="blue")
        self.test_ipcam_btn.config(state="disabled")
        
        # Run test in background thread
        def test_connection():
            try:
                # First try virtual camera
                print("Testing virtual camera...")
                cap = cv2.VideoCapture(1)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret:
                        cap.release()
                        self.ipcam_status.config(text="DroidCam: Virtual Camera ✓", foreground="green")
                        messagebox.showinfo("Success", "DroidCam Virtual Camera is working!")
                        return
                    cap.release()
                
                # Try IP connection
                ip = self.ip_var.get().strip()
                port = self.port_var.get().strip()
                if not ip:
                    self.ipcam_status.config(text="DroidCam: IP required", foreground="red")
                    messagebox.showerror("Error", "Please enter IP address")
                    return
                
                url = f"http://{ip}:{port}/video"
                print(f"Testing IP connection: {url}")
                
                # Use the main test function
                success, message = test_droidcam_connection_main(url)
                
                if success:
                    self.ipcam_status.config(text="DroidCam: IP Connected ✓", foreground="green")
                    messagebox.showinfo("Success", f"DroidCam IP connection successful!\n{message}")
                else:
                    self.ipcam_status.config(text="DroidCam: IP Failed", foreground="red")
                    messagebox.showerror("Error", f"DroidCam IP connection failed:\n{message}")
                    
            except Exception as e:
                self.ipcam_status.config(text="DroidCam: Test error", foreground="red")
                messagebox.showerror("Error", f"Connection test failed: {e}")
            finally:
                self.test_ipcam_btn.config(state="normal")
        
        threading.Thread(target=test_connection, daemon=True).start()

    def show_email_popup(self, message, success=False):
        """Show a messagebox for email status. Only show for errors."""
        if not success:
            messagebox.showerror("Email Alert", message)

def main():
    root = tk.Tk()
    app = EnhancedGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 