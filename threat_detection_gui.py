#!/usr/bin/env python3
"""
Simple AI Threat Detection GUI with Collapsible Email
"""

import tkinter as tk
from tkinter import ttk, messagebox
import cv2
from PIL import Image, ImageTk
import threading
from threat_detection import load_yolo, detect_threat, setup_arduino, EMAIL_CONFIG, send_threat_email
import time
import queue
import os

class SimpleGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Threat Detection - Simple")
        self.root.geometry("1000x700")
        
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
        
        # Create layout
        self.create_layout()
        
        # Initialize system
        self.initialize_system()
        
        # Start updates
        self.update_display()
    
    def create_layout(self):
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Camera frame (left side - takes most space)
        self.camera_frame = ttk.LabelFrame(main_frame, text="Camera Feed")
        self.camera_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self.video_label = ttk.Label(self.camera_frame)
        self.video_label.pack(padx=10, pady=10)
        
        # Control panel (right side - fixed width)
        control_frame = ttk.Frame(main_frame, width=300)
        control_frame.pack(side=tk.RIGHT, fill=tk.Y)
        control_frame.pack_propagate(False)  # Prevent shrinking
        
        # Start button
        self.start_button = ttk.Button(control_frame, text="Start Detection", 
                                      command=self.toggle_detection, width=25)
        self.start_button.pack(pady=10)
        
        # Arduino status
        self.arduino_status = ttk.Label(control_frame, text="Arduino: Disconnected")
        self.arduino_status.pack(pady=5)
        
        # Email toggle button
        self.email_toggle = ttk.Button(control_frame, text="📧 Show Email Config", 
                                      command=self.toggle_email, width=25)
        self.email_toggle.pack(pady=10)
        
        # Email frame (initially hidden)
        self.email_frame = ttk.LabelFrame(control_frame, text="Email Configuration")
        
        # Email fields
        ttk.Label(self.email_frame, text="Sender:").pack(anchor=tk.W, padx=10, pady=2)
        self.sender_var = tk.StringVar(value=EMAIL_CONFIG['sender_email'])
        self.sender_entry = ttk.Entry(self.email_frame, textvariable=self.sender_var, width=25)
        self.sender_entry.pack(padx=10, pady=2)
        
        ttk.Label(self.email_frame, text="Password:").pack(anchor=tk.W, padx=10, pady=2)
        self.password_var = tk.StringVar(value=EMAIL_CONFIG['sender_password'])
        self.password_entry = ttk.Entry(self.email_frame, textvariable=self.password_var, 
                                      width=25, show="*")
        self.password_entry.pack(padx=10, pady=2)
        
        # Show/Hide Password Checkbox
        self.show_password_var = tk.BooleanVar()
        self.show_password_check = ttk.Checkbutton(self.email_frame, text="Show Password", 
                                                  variable=self.show_password_var, 
                                                  command=self.toggle_password_visibility)
        self.show_password_check.pack(anchor=tk.W, padx=10, pady=2)
        
        ttk.Label(self.email_frame, text="Recipient:").pack(anchor=tk.W, padx=10, pady=2)
        self.recipient_var = tk.StringVar(value=EMAIL_CONFIG['recipient_email'])
        self.recipient_entry = ttk.Entry(self.email_frame, textvariable=self.recipient_var, width=25)
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
        
        # Status section
        status_frame = ttk.LabelFrame(control_frame, text="Status")
        status_frame.pack(fill=tk.X, pady=10)
        
        self.threat_status = ttk.Label(status_frame, text="Threat: Normal", 
                                     font=("Arial", 12, "bold"))
        self.threat_status.pack(pady=5)
        
        self.fps_label = ttk.Label(status_frame, text="FPS: 0")
        self.fps_label.pack(pady=2)
    
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
        self.cap = cv2.VideoCapture(0)
        
        # Set camera properties for better performance
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        if not self.cap.isOpened():
            messagebox.showerror("Error", "Could not open camera!")
            self.stop_detection()
            return
        
        threading.Thread(target=self.capture_loop, daemon=True).start()
    
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
            
            # Run detection more frequently for better responsiveness
            if current_time - last_detection >= detection_interval:
                try:
                    result = detect_threat(frame, self.model)
                    if result is None:
                        continue
                    
                    processed_frame, threat_detected, threat_details = result
                    last_detection = current_time
                    
                    # Update status
                    if threat_detected:
                        self.threat_status.config(text="Threat: DETECTED!", foreground="red")
                        # Send email with cooldown
                        if (hasattr(self, 'email_configured') and self.email_configured and 
                            current_time - self.last_email_time > self.email_cooldown):
                            try:
                                send_threat_email(processed_frame, threat_details)
                                self.last_email_time = current_time
                            except:
                                pass
                    else:
                        self.threat_status.config(text="Threat: Normal", foreground="green")
                    
                    # Update FPS
                    fps = frame_count / (current_time - start_time)
                    self.fps_label.config(text=f"FPS: {fps:.1f}")
                    
                    # Put frame in queue for display (non-blocking)
                    try:
                        self.frame_queue.put_nowait(processed_frame)
                    except queue.Full:
                        # Clear queue and put new frame
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
            else:
                # For frames without detection, just update FPS and display
                fps = frame_count / (current_time - start_time)
                if frame_count % 15 == 0:  # Update FPS every 15 frames
                    self.fps_label.config(text=f"FPS: {fps:.1f}")
                
                # Put original frame in queue for display
                try:
                    self.frame_queue.put_nowait(frame)
                except queue.Full:
                    try:
                        self.frame_queue.get_nowait()
                        self.frame_queue.put_nowait(frame)
                    except:
                        pass
            
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
        
        self.root.after(33, self.update_display)  # ~30 FPS display update
    
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
        except:
            self.email_status.config(text="Email: Not configured", foreground="red")
    
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

def main():
    root = tk.Tk()
    app = SimpleGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 