import tkinter as tk
from tkinter import ttk, messagebox
import cv2
from PIL import Image, ImageTk
import threading
from threat_detection import load_yolo, detect_threat, setup_arduino
import time
import queue
import numpy as np

def detect_threat_with_confidence(frame, model, confidence_threshold=0.5):
    """Wrapper function to call detect_threat with custom confidence threshold"""
    # Resize frame to match main file behavior
    frame = cv2.resize(frame, (640, 480))
    
    # Run YOLOv8 inference with custom confidence
    results = model(frame, conf=confidence_threshold)[0]
    
    # Get the original detect_threat function and call it with the processed frame
    # We'll need to modify the approach since we can't easily override the confidence
    # Let's create a custom detection function for the GUI
    
    height, width, channels = frame.shape
    frame_center_x = width / 2
    frame_center_y = height / 2
    
    # Check if frame is too dark
    frame_brightness = np.mean(frame)
    if frame_brightness < 30:
        cv2.putText(frame, "Warning: Poor lighting or camera blocked", (10, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        return frame, False
    
    # Define threat classes (same as main file)
    weapon_classes = ['knife', 'scissors', 'baseball bat', 'bottle', 'cell phone']
    person_detected = False
    weapon_detected = False
    threat_score = 0
    detected_objects = []
    
    # Store detection coordinates for proximity analysis
    person_boxes = []
    weapon_boxes = []
    
    # Process detections
    for result in results.boxes.data.tolist():
        x1, y1, x2, y2, confidence, class_id = result
        class_name = results.names[int(class_id)]
        
        # Track detected objects
        detected_objects.append(class_name)
        
        # Calculate position and size metrics
        w = x2 - x1
        h = y2 - y1
        area_ratio = (w * h) / (width * height)
        center_x = x1 + w/2
        center_y = y1 + h/2
        distance_from_center = np.sqrt(
            ((center_x - frame_center_x) / width) ** 2 +
            ((center_y - frame_center_y) / height) ** 2
        )
        
        # Assess threat based on object type
        if class_name == 'person':
            person_detected = True
            person_boxes.append((x1, y1, x2, y2, center_x, center_y))
            color = (0, 255, 0)  # Green for person
            
        elif class_name in weapon_classes:
            weapon_detected = True
            weapon_boxes.append((x1, y1, x2, y2, center_x, center_y))
            color = (0, 0, 255)  # Red for weapons
        
        # Draw bounding boxes and labels
        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
        cv2.putText(frame, f"{class_name}: {confidence:.2f}", (int(x1), int(y1 - 10)),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    
    # Check for person-weapon proximity (person holding weapon)
    person_with_weapon = False
    if person_detected and weapon_detected:
        for person_box in person_boxes:
            px1, py1, px2, py2, p_center_x, p_center_y = person_box
            person_area = (px2 - px1) * (py2 - py1)
            
            for weapon_box in weapon_boxes:
                wx1, wy1, wx2, wy2, w_center_x, w_center_y = weapon_box
                weapon_area = (wx2 - wx1) * (wy2 - wy1)
                
                # Calculate distance between person and weapon centers
                distance = np.sqrt((p_center_x - w_center_x)**2 + (p_center_y - w_center_y)**2)
                
                # Check if weapon is close to person (likely being held)
                # Use a threshold based on person size
                person_diagonal = np.sqrt((px2 - px1)**2 + (py2 - py1)**2)
                proximity_threshold = person_diagonal * 0.8  # Weapon within 80% of person's diagonal
                
                if distance < proximity_threshold:
                    person_with_weapon = True
                    threat_score = 10  # High threat score for person with weapon
                    break
            
            if person_with_weapon:
                break
    
    # Determine final threat level - only person with weapon is a threat
    threat_detected = False
    if person_with_weapon:
        threat_detected = True
        status = "HIGH THREAT: Person with Weapon!"
        status_color = (0, 0, 255)
    elif weapon_detected:
        status = "CAUTION: Weapon Detected (No Person Nearby)"
        status_color = (0, 165, 255)
    elif person_detected:
        status = "Normal: Person Detected (No Weapon)"
        status_color = (0, 255, 0)
    else:
        status = "Normal: No Threats Detected"
        status_color = (0, 255, 0)
    
    # Display status and debug info
    cv2.putText(frame, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)
    cv2.putText(frame, f"Threat Score: {threat_score}", (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)
    
    # Display detected objects
    objects_text = "Detected: " + ", ".join(set(detected_objects))
    cv2.putText(frame, objects_text, (10, 90),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    return frame, threat_detected

class ThreatDetectionGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Threat Detection System")
        self.root.geometry("1400x900")
        
        # Initialize variables
        self.is_running = False
        self.cap = None
        self.model = None
        self.arduino = None
        self.frame_queue = queue.Queue(maxsize=2)  # Reduced queue size for better performance
        self.display_queue = queue.Queue(maxsize=1)  # Separate queue for display frames
        self.status_queue = queue.Queue()
        self.current_image = None  # Keep reference to prevent garbage collection
        
        # Performance tracking
        self.frame_count = 0
        self.start_time = time.time()
        self.last_fps_update = 0
        
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
        
        # Arduino status
        self.arduino_status = ttk.Label(self.control_frame, text="Arduino: Disconnected", font=("Arial", 10))
        self.arduino_status.grid(row=1, column=0, padx=5, pady=5)
        
        # Detection settings
        self.settings_frame = ttk.LabelFrame(self.control_frame, text="Settings", padding="5")
        self.settings_frame.grid(row=2, column=0, padx=5, pady=5, sticky="ew")
        
        # Confidence threshold slider
        ttk.Label(self.settings_frame, text="Detection Confidence:").grid(row=0, column=0, padx=5, pady=2)
        self.confidence_var = tk.DoubleVar(value=0.5)
        self.confidence_slider = ttk.Scale(self.settings_frame, from_=0.1, to=0.9, 
                                         variable=self.confidence_var, orient="horizontal")
        self.confidence_slider.grid(row=1, column=0, padx=5, pady=2, sticky="ew")
        
        # Confidence value display
        self.confidence_label = ttk.Label(self.settings_frame, text="Confidence: 0.5", font=("Arial", 9))
        self.confidence_label.grid(row=2, column=0, padx=5, pady=2)
        
        # Bind slider to update label
        self.confidence_slider.config(command=self.update_confidence_label)
        
        # Status indicators
        self.status_frame = ttk.LabelFrame(self.main_frame, text="System Status", padding="5")
        self.status_frame.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")
        
        self.threat_status = ttk.Label(self.status_frame, text="Threat Status: Normal", 
                                     font=("Arial", 12, "bold"))
        self.threat_status.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        self.detection_info = ttk.Label(self.status_frame, text="Detection Info: None", 
                                      font=("Arial", 10))
        self.detection_info.grid(row=1, column=0, padx=5, pady=2, sticky="w")
        
        self.fps_label = ttk.Label(self.status_frame, text="FPS: 0", font=("Arial", 10))
        self.fps_label.grid(row=2, column=0, padx=5, pady=2, sticky="w")
        
        self.frame_count_label = ttk.Label(self.status_frame, text="Frames Processed: 0", 
                                         font=("Arial", 10))
        self.frame_count_label.grid(row=3, column=0, padx=5, pady=2, sticky="w")
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=2)
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(0, weight=3)
        self.main_frame.rowconfigure(1, weight=1)
        self.settings_frame.columnconfigure(0, weight=1)
        
        # Initialize system
        self.initialize_system()
        
        # Start status update thread
        self.update_status()
        self.update_display()
    
    def initialize_system(self):
        """Initialize the YOLO model and Arduino connection"""
        try:
            # Show loading message
            self.threat_status.config(text="Initializing System...", foreground="blue")
            self.root.update()
            
            # Load YOLO model
            self.model = load_yolo()
            
            # Setup Arduino
            self.arduino = setup_arduino()
            if self.arduino:
                self.arduino_status.config(text="Arduino: Connected", foreground="green")
            else:
                self.arduino_status.config(text="Arduino: Disconnected", foreground="red")
            
            self.threat_status.config(text="Threat Status: Ready", foreground="green")
            messagebox.showinfo("Success", "System initialized successfully!")
            
        except Exception as e:
            self.threat_status.config(text="Threat Status: Initialization Failed", foreground="red")
            messagebox.showerror("Error", f"Failed to initialize system: {str(e)}")
    
    def toggle_detection(self):
        """Toggle the threat detection system on/off"""
        if not self.is_running:
            self.start_detection()
        else:
            self.stop_detection()
    
    def start_detection(self):
        """Start the threat detection system"""
        if not self.model:
            messagebox.showerror("Error", "YOLO model not loaded!")
            return
            
        self.is_running = True
        self.start_button.config(text="Stop Detection")
        self.cap = cv2.VideoCapture(0)
        
        # Set camera properties for better performance
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        if not self.cap.isOpened():
            messagebox.showerror("Error", "Could not open webcam!")
            self.stop_detection()
            return
        
        # Reset counters
        self.frame_count = 0
        self.start_time = time.time()
        
        # Start processing threads
        threading.Thread(target=self.capture_frames, daemon=True).start()
        threading.Thread(target=self.process_frames, daemon=True).start()
    
    def stop_detection(self):
        """Stop the threat detection system"""
        self.is_running = False
        self.start_button.config(text="Start Detection")
        if self.cap:
            self.cap.release()
            self.cap = None
        
        # Clear queues
        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
            except queue.Empty:
                break
        
        while not self.display_queue.empty():
            try:
                self.display_queue.get_nowait()
            except queue.Empty:
                break
    
    def capture_frames(self):
        """Capture frames from camera in separate thread"""
        while self.is_running:
            if self.cap is None:
                break
                
            ret, frame = self.cap.read()
            if not ret:
                break
            
            self.frame_count += 1
            
            # Put frame in queue (non-blocking)
            try:
                self.frame_queue.put_nowait(frame)
            except queue.Full:
                # Remove old frame and add new one
                try:
                    self.frame_queue.get_nowait()
                    self.frame_queue.put_nowait(frame)
                except queue.Empty:
                    pass
            
            # Small delay to prevent overwhelming the queue
            time.sleep(0.01)  # ~100 FPS capture rate
    
    def process_frames(self):
        """Process frames with threat detection in separate thread"""
        last_detection_time = 0
        detection_interval = 0.2  # Run detection every 0.2 seconds for better responsiveness
        threat_detected = False
        
        while self.is_running:
            try:
                frame = self.frame_queue.get(timeout=0.1)
            except queue.Empty:
                continue
            
            current_time = time.time()
            
            # Run detection periodically
            if current_time - last_detection_time >= detection_interval:
                # Get current confidence threshold from slider
                confidence_threshold = self.confidence_var.get()
                
                # Process frame with threat detection using custom function with confidence
                processed_frame, threat_detected = detect_threat_with_confidence(frame, self.model, confidence_threshold)
                last_detection_time = current_time
                
                # Send status update
                try:
                    self.status_queue.put_nowait({
                        'threat_detected': threat_detected,
                        'frame_count': self.frame_count,
                        'fps': self.frame_count / (current_time - self.start_time) if (current_time - self.start_time) > 0 else 0
                    })
                except queue.Full:
                    pass
                
                # Send signal to Arduino if threat detected
                if self.arduino and threat_detected:
                    try:
                        self.arduino.write("1".encode())
                    except:
                        pass
            else:
                # Use the frame as-is for display (no processing)
                processed_frame = frame
            
            # Put processed frame in display queue
            try:
                self.display_queue.put_nowait(processed_frame)
            except queue.Full:
                # Remove old frame and add new one
                try:
                    self.display_queue.get_nowait()
                    self.display_queue.put_nowait(processed_frame)
                except queue.Empty:
                    pass
    
    def update_display(self):
        """Update display in main thread"""
        if self.is_running:
            try:
                frame = self.display_queue.get_nowait()
                
                # Convert frame to PhotoImage
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                img = ImageTk.PhotoImage(image=img)
                
                # Keep reference to prevent garbage collection
                self.current_image = img
                
                # Update video label
                self.video_label.config(image=img)
                
            except queue.Empty:
                pass
        
        # Schedule next update (30 FPS display rate)
        self.root.after(33, self.update_display)
    
    def update_status(self):
        """Update status display in main thread"""
        try:
            while not self.status_queue.empty():
                status = self.status_queue.get_nowait()
                
                # Update threat status
                if status['threat_detected']:
                    self.threat_status.config(text="Threat Status: HIGH THREAT!", foreground="red")
                    self.detection_info.config(text="Detection: Person with Weapon Detected", foreground="red")
                else:
                    self.threat_status.config(text="Threat Status: Normal", foreground="green")
                    self.detection_info.config(text="Detection: No Threats", foreground="green")
                
                # Update FPS and frame count
                self.fps_label.config(text=f"FPS: {status['fps']:.1f}")
                self.frame_count_label.config(text=f"Frames Processed: {status['frame_count']}")
                
        except queue.Empty:
            pass
        
        # Update FPS even when no status updates
        if self.is_running:
            current_time = time.time()
            if current_time - self.last_fps_update >= 0.5:  # Update FPS every 0.5 seconds
                fps = self.frame_count / (current_time - self.start_time) if (current_time - self.start_time) > 0 else 0
                self.fps_label.config(text=f"FPS: {fps:.1f}")
                self.frame_count_label.config(text=f"Frames Processed: {self.frame_count}")
                self.last_fps_update = current_time
        
        # Schedule next update
        self.root.after(100, self.update_status)
    
    def update_confidence_label(self, value=None):
        """Update the confidence label when the slider is moved"""
        confidence = self.confidence_var.get()
        self.confidence_label.config(text=f"Confidence: {confidence:.1f}")
    
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