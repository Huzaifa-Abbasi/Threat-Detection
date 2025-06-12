import cv2
import numpy as np
import serial
import time
import os
from ultralytics import YOLO

def download_yolo_model():
    """Download YOLOv8 model if it doesn't exist."""
    model_path = "yolov8s.pt"
    if not os.path.exists(model_path):
        print("Downloading YOLOv8 model...")
        model = YOLO('yolov8s.pt')
        model.save(model_path)
        print("Model downloaded successfully!")
    return model_path

def load_yolo():
    """Load the YOLOv8 model."""
    model_path = download_yolo_model()
    model = YOLO(model_path)
    return model

def detect_threat(frame, model):
    """Detect potential threats in a frame using YOLOv8."""
    # Resize frame for better performance
    frame = cv2.resize(frame, (640, 480))
    height, width, channels = frame.shape
    
    # Define frame center coordinates
    frame_center_x = width / 2
    frame_center_y = height / 2
    
    # Check if frame is too dark
    frame_brightness = np.mean(frame)
    if frame_brightness < 30:
        cv2.putText(frame, "Warning: Poor lighting or camera blocked", (10, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        return frame, False
    
    # Run YOLOv8 inference
    results = model(frame, conf=0.5)[0]  # Increased confidence threshold
    
    # Define threat classes
    weapon_classes = ['knife', 'scissors', 'baseball bat', 'bottle', 'cell phone']
    person_detected = False
    weapon_detected = False
    threat_score = 0
    detected_objects = []
    
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
            # Person threat assessment
            if area_ratio > 0.15:  # Person is close
                threat_score += 2
            if distance_from_center < 0.3:  # Person is central
                threat_score += 1
            color = (0, 255, 0)  # Green for person
            
        elif class_name in weapon_classes:
            weapon_detected = True
            threat_score += 4  # Weapons are serious threats
            color = (0, 0, 255)  # Red for weapons
        
        # Draw bounding boxes and labels
        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
        cv2.putText(frame, f"{class_name}: {confidence:.2f}", (int(x1), int(y1 - 10)),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    
    # Determine final threat level
    threat_detected = False
    if person_detected and weapon_detected:
        threat_score += 3  # Additional points for person with weapon
        threat_detected = True
        status = "HIGH THREAT: Person with Weapon!"
        status_color = (0, 0, 255)
    elif weapon_detected:
        threat_detected = True
        status = "THREAT: Weapon Detected!"
        status_color = (0, 0, 255)
    elif person_detected and threat_score >= 3:
        threat_detected = True
        status = "CAUTION: Suspicious Person"
        status_color = (0, 165, 255)
    else:
        status = "Normal"
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

def setup_arduino(port=None, baud_rate=9600):
    """Establish serial communication with Arduino."""
    # Try common serial ports
    potential_ports = []
    
    # Add OS-specific common ports
    if os.name == 'nt':  # Windows
        potential_ports = ['COM%s' % (i + 1) for i in range(10)]
    else:  # Linux/Mac
        potential_ports = ['/dev/ttyUSB%s' % i for i in range(10)]
        potential_ports += ['/dev/ttyACM%s' % i for i in range(10)]
    
    # If port is specified, try it first
    if port:
        potential_ports.insert(0, port)
    
    # Try ports until one works
    for port in potential_ports:
        try:
            arduino = serial.Serial(port=port, baudrate=baud_rate, timeout=1)
            time.sleep(2)  # Allow time for connection to establish
            print(f"Connected to Arduino on {port}")
            return arduino
        except (serial.SerialException, OSError):
            continue
    
    print("Failed to connect to Arduino on any port")
    return None

def main():
    """Main program execution."""
    # Load YOLOv8 model
    print("Loading YOLOv8 model...")
    model = load_yolo()
    print("YOLOv8 model loaded successfully!")
    
    # Setup Arduino
    print("Connecting to Arduino...")
    arduino = setup_arduino()
    
    # Start webcam
    print("Starting webcam...")
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return
    
    previous_state = False  # Track the previous threat state
    frame_count = 0
    start_time = time.time()
    
    print("System ready! Press 'q' to exit.")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break
        
        # Detect threats
        frame, threat_detected = detect_threat(frame, model)
        
        # Calculate and display FPS
        frame_count += 1
        if frame_count % 30 == 0:
            end_time = time.time()
            fps = 30 / (end_time - start_time)
            start_time = time.time()
            cv2.putText(frame, f"FPS: {fps:.1f}", (10, 120),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Show frame
        cv2.imshow("AI Threat Detection System", frame)
        
        # Send signal to Arduino if state changed
        if arduino and threat_detected != previous_state:
            signal = "1" if threat_detected else "0"
            arduino.write(signal.encode())
            print(f"Sent signal {signal} to Arduino")
            previous_state = threat_detected
        
        # Exit if 'q' is pressed
        if cv2.waitKey(1) == ord('q'):
            break
    
    # Clean up
    cap.release()
    cv2.destroyAllWindows()
    if arduino:
        arduino.close()
        print("Arduino connection closed")
    print("System shutdown complete")

if __name__ == "__main__":
    main()