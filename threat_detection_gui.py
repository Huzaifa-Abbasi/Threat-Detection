import tkinter as tk
from tkinter import ttk, messagebox
import cv2
from PIL import Image, ImageTk
import threading
from threat_detection import load_yolo, detect_threat, setup_arduino
import time

class ThreatDetectionGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Threat Detection System")
        self.root.geometry("1200x800")
        
        # Initialize variables
        self.is_running = False
        self.cap = None
        self.model = None
        self.arduino = None
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Create video frame
        self.video_frame = ttk.LabelFrame(self.main_frame, text="Camera Feed", padding="5")
        self.video_frame.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
        
        self.video_label = ttk.Label(self.video_frame)
        self.video_label.grid(row=0, column=0, padx=5, pady=5)
        
        # Create control panel
        self.control_frame = ttk.LabelFrame(self.main_frame, text="Controls", padding="5")
        self.control_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        
        # Start/Stop button
        self.start_button = ttk.Button(self.control_frame, text="Start Detection", command=self.toggle_detection)
        self.start_button.grid(row=0, column=0, padx=5, pady=5)
        
        # Status indicators
        self.status_frame = ttk.LabelFrame(self.main_frame, text="Status", padding="5")
        self.status_frame.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")
        
        self.threat_status = ttk.Label(self.status_frame, text="Threat Status: Normal", font=("Arial", 12))
        self.threat_status.grid(row=0, column=0, padx=5, pady=5)
        
        self.fps_label = ttk.Label(self.status_frame, text="FPS: 0", font=("Arial", 12))
        self.fps_label.grid(row=1, column=0, padx=5, pady=5)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(0, weight=3)
        self.main_frame.rowconfigure(1, weight=1)
        
        # Initialize system
        self.initialize_system()
    
    def initialize_system(self):
        """Initialize the YOLO model and Arduino connection"""
        try:
            self.model = load_yolo()
            self.arduino = setup_arduino()
            messagebox.showinfo("Success", "System initialized successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to initialize system: {str(e)}")
    
    def toggle_detection(self):
        """Toggle the threat detection system on/off"""
        if not self.is_running:
            self.start_detection()
        else:
            self.stop_detection()
    
    def start_detection(self):
        """Start the threat detection system"""
        self.is_running = True
        self.start_button.config(text="Stop Detection")
        self.cap = cv2.VideoCapture(0)
        threading.Thread(target=self.update_frame, daemon=True).start()
    
    def stop_detection(self):
        """Stop the threat detection system"""
        self.is_running = False
        self.start_button.config(text="Start Detection")
        if self.cap:
            self.cap.release()
    
    def update_frame(self):
        """Update the video frame with detection results"""
        frame_count = 0
        start_time = cv2.getTickCount()
        skip_frames = 30  # Process every 30th frame
        last_detection_time = 0
        detection_interval = 1.0  # Run detection every 1 second
        
        while self.is_running:
            if self.cap is None:
                break
                
            ret, frame = self.cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # Skip frames to improve performance
            if frame_count % skip_frames != 0:
                continue
            
            # Resize frame for faster processing
            frame = cv2.resize(frame, (320, 240))  # Reduced resolution
            
            current_time = time.time()
            # Only run detection periodically
            if current_time - last_detection_time >= detection_interval:
                # Process frame with threat detection
                processed_frame, threat_detected = detect_threat(frame, self.model)
                last_detection_time = current_time
                
                # Update threat status
                if threat_detected:
                    self.threat_status.config(text="Threat Status: THREAT DETECTED!", foreground="red")
                else:
                    self.threat_status.config(text="Threat Status: Normal", foreground="green")
            else:
                # Just resize and display frame without detection
                processed_frame = cv2.resize(frame, (640, 480))
            
            # Calculate and update FPS
            if frame_count % 30 == 0:
                end_time = cv2.getTickCount()
                fps = 30 / ((end_time - start_time) / cv2.getTickFrequency())
                self.fps_label.config(text=f"FPS: {fps:.1f}")
                start_time = cv2.getTickCount()
            
            # Convert frame to PhotoImage
            processed_frame = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(processed_frame)
            img = ImageTk.PhotoImage(image=img)
            
            # Update video label
            self.video_label.config(image=img)
            
            # Small delay to prevent high CPU usage
            cv2.waitKey(1)
    
    def __del__(self):
        """Cleanup when the application is closed"""
        self.stop_detection()
        if self.arduino:
            self.arduino.close()

def main():
    root = tk.Tk()
    app = ThreatDetectionGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 