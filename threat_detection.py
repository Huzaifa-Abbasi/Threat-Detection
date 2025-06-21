import cv2
import numpy as np
import serial
import time
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime
from ultralytics import YOLO

# Email configuration - Update these with your email settings
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',  # For Gmail
    'smtp_port': 587,
    'sender_email': 'try.huzaifa@gmail.com',  # Replace with your email
    'sender_password': 'letstryit',  # Replace with your app password
    'recipient_email': 'huzaifaa66asi@gmail.com',  # Replace with recipient email
    'subject_prefix': 'THREAT DETECTED - AI Security System'
}

def send_threat_email(frame, threat_details):
    """
    Send an email with the threat detection image and details.
    
    Args:
        frame: The captured frame with threat detection
        threat_details: Dictionary containing threat information
    """
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['sender_email']
        msg['To'] = EMAIL_CONFIG['recipient_email']
        msg['Subject'] = f"{EMAIL_CONFIG['subject_prefix']} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Create email body
        body = f"""
        ⚠️ THREAT DETECTED ⚠️
        
        Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        Threat Level: {threat_details.get('threat_level', 'Unknown')}
        Threat Score: {threat_details.get('threat_score', 0)}
        Detected Objects: {', '.join(threat_details.get('detected_objects', []))}
        
        This is an automated alert from your AI Threat Detection System.
        Please review the attached image and take appropriate action.
        
        ---
        AI Security System
        Automated Threat Detection
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Convert frame to image and attach
        # Save frame temporarily
        temp_image_path = f"threat_detection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        cv2.imwrite(temp_image_path, frame)
        
        # Attach image
        with open(temp_image_path, 'rb') as f:
            img_data = f.read()
            image = MIMEImage(img_data, name=os.path.basename(temp_image_path))
            msg.attach(image)
        
        # Send email
        server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
        server.starttls()
        server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
        text = msg.as_string()
        server.sendmail(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['recipient_email'], text)
        server.quit()
        
        # Clean up temporary file
        os.remove(temp_image_path)
        
        print(f"✅ Threat alert email sent successfully to {EMAIL_CONFIG['recipient_email']}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send email: {str(e)}")
        # Clean up temporary file if it exists
        if 'temp_image_path' in locals() and os.path.exists(temp_image_path):
            os.remove(temp_image_path)
        return False

def setup_email_config():
    """
    Interactive setup for email configuration.
    """
    print("\n📧 Email Configuration Setup")
    print("=" * 40)
    
    # Check if email config file exists
    config_file = "email_config.txt"
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                lines = f.readlines()
                if len(lines) >= 3:
                    EMAIL_CONFIG['sender_email'] = lines[0].strip()
                    EMAIL_CONFIG['sender_password'] = lines[1].strip()
                    EMAIL_CONFIG['recipient_email'] = lines[2].strip()
                    print("✅ Email configuration loaded from file")
                    return
        except:
            pass
    
    print("Please configure your email settings:")
    EMAIL_CONFIG['sender_email'] = input("Sender Email (Gmail): ").strip()
    EMAIL_CONFIG['sender_password'] = input("App Password (not regular password): ").strip()
    EMAIL_CONFIG['recipient_email'] = input("Recipient Email: ").strip()
    
    # Save configuration
    try:
        with open(config_file, 'w') as f:
            f.write(f"{EMAIL_CONFIG['sender_email']}\n")
            f.write(f"{EMAIL_CONFIG['sender_password']}\n")
            f.write(f"{EMAIL_CONFIG['recipient_email']}\n")
        print("✅ Email configuration saved")
    except Exception as e:
        print(f"⚠️ Could not save email configuration: {e}")

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
    # Validate frame
    if frame is None or frame.size == 0:
        print("⚠️ Invalid frame received")
        return None, False, {
            'threat_level': 'Error',
            'threat_score': 0,
            'detected_objects': [],
            'status': 'Invalid frame'
        }
    
    # Resize frame for better performance (balanced size)
    frame = cv2.resize(frame, (480, 480))  # Balanced size for speed and accuracy
    height, width, channels = frame.shape
    
    # Define frame center coordinates
    frame_center_x = width / 2
    frame_center_y = height / 2
    
    # Check if frame is too dark
    frame_brightness = np.mean(frame)
    if frame_brightness < 30:
        cv2.putText(frame, "Warning: Poor lighting or camera blocked", (10, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        return frame, False, {
            'threat_level': 'Warning',
            'threat_score': 0,
            'detected_objects': ['poor_lighting'],
            'status': 'Poor lighting or camera blocked'
        }
    
    # Run YOLOv8 inference with balanced confidence threshold
    try:
        results = model(frame, conf=0.55)[0]  # Balanced confidence threshold
    except Exception as e:
        print(f"⚠️ YOLO inference error: {e}")
        # Return safe default values
        return frame, False, {
            'threat_level': 'Error',
            'threat_score': 0,
            'detected_objects': [],
            'status': 'Model inference error'
        }
    
    # Define threat classes
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
        center_x = x1 + w/2
        center_y = y1 + h/2
        
        # Initialize color variable
        color = (255, 255, 255)  # Default white color
        
        # Assess threat based on object type
        if class_name == 'person':
            person_detected = True
            person_boxes.append((x1, y1, x2, y2, center_x, center_y))
            color = (0, 255, 0)  # Green for person
            
        elif class_name in weapon_classes:
            weapon_detected = True
            weapon_boxes.append((x1, y1, x2, y2, center_x, center_y))
            color = (0, 0, 255)  # Red for weapons
        
        # Draw bounding boxes and labels for all detected objects
        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
        cv2.putText(frame, f"{class_name}: {confidence:.2f}", (int(x1), int(y1 - 10)),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    
    # Check for person-weapon proximity (person holding weapon)
    person_with_weapon = False
    if person_detected and weapon_detected:
        for person_box in person_boxes:
            px1, py1, px2, py2, p_center_x, p_center_y = person_box
            
            for weapon_box in weapon_boxes:
                wx1, wy1, wx2, wy2, w_center_x, w_center_y = weapon_box
                
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
        threat_level = "HIGH THREAT"
    elif weapon_detected:
        status = "CAUTION: Weapon Detected (No Person Nearby)"
        status_color = (0, 165, 255)
        threat_level = "CAUTION"
    elif person_detected:
        status = "Normal: Person Detected (No Weapon)"
        status_color = (0, 255, 0)
        threat_level = "NORMAL"
    else:
        status = "Normal: No Threats Detected"
        status_color = (0, 255, 0)
        threat_level = "NORMAL"
    
    # Display status and debug info
    cv2.putText(frame, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)
    cv2.putText(frame, f"Threat Score: {threat_score}", (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)
    
    # Display detected objects
    objects_text = "Detected: " + ", ".join(set(detected_objects))
    cv2.putText(frame, objects_text, (10, 90),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    # Create threat details dictionary
    threat_details = {
        'threat_level': threat_level,
        'threat_score': threat_score,
        'detected_objects': list(set(detected_objects)),
        'status': status,
        'person_detected': person_detected,
        'weapon_detected': weapon_detected,
        'person_with_weapon': person_with_weapon
    }
    
    return frame, threat_detected, threat_details

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
    
    # Setup email configuration
    setup_email_config()
    
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
    last_email_time = 0  # Track last email sent time
    email_cooldown = 60  # Send email only once every 60 seconds
    
    print("System ready! Press 'q' to exit.")
    print("📧 Email alerts will be sent when threats are detected.")
    
    while True:
        try:
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame")
                break
            
            # Detect threats
            result = detect_threat(frame, model)
            if result is None:
                print("⚠️ Skipping frame due to detection error")
                continue
                
            frame, threat_detected, threat_details = result
            
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
                try:
                    signal = "1" if threat_detected else "0"
                    arduino.write(signal.encode())
                    print(f"Sent signal {signal} to Arduino")
                    previous_state = threat_detected
                except Exception as e:
                    print(f"⚠️ Failed to send signal to Arduino: {e}")
            
            # Send email if threat detected (with cooldown)
            current_time = time.time()
            if threat_detected and (current_time - last_email_time) > email_cooldown:
                print("📧 Sending threat alert email...")
                if send_threat_email(frame, threat_details):
                    last_email_time = current_time
                    print(f"⏰ Next email can be sent in {email_cooldown} seconds")
            
            # Exit if 'q' is pressed
            if cv2.waitKey(1) == ord('q'):
                break
                
        except Exception as e:
            print(f"⚠️ Error in main loop: {e}")
            print("Continuing...")
            time.sleep(0.1)  # Small delay to prevent rapid error loops
            continue
    
    # Clean up
    cap.release()
    cv2.destroyAllWindows()
    if arduino:
        arduino.close()
        print("Arduino connection closed")
    print("System shutdown complete")

if __name__ == "__main__":
    main()