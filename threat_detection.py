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
import threading

# Email configuration - Update these with your email settings
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',  # For Gmail
    'smtp_port': 587,
    'sender_email': 'try.huzaifa@gmail.com',  # Replace with your email
    'sender_password': 'letstryit',  # Replace with your app password
    'recipient_email': 'huzaifaa66asi@gmail.com',  # Replace with recipient email
    'subject_prefix': 'THREAT DETECTED - AI Security System'
}

def is_email_config_valid():
    """Check if EMAIL_CONFIG has all required fields and they are non-empty."""
    required = ['sender_email', 'sender_password', 'recipient_email']
    for key in required:
        if not EMAIL_CONFIG.get(key):
            print(f"[EMAIL] Missing or empty config: {key}")
            return False
    return True

def send_threat_email(frame, threat_details):
    """Send an email with the threat detection image and details."""
    print(f"[EMAIL] Preparing to send email. Config: {EMAIL_CONFIG}")
    print(f"[EMAIL] Threat details: {threat_details}")
    if not is_email_config_valid():
        print("❌ Email config incomplete. Cannot send email. Please check sender, password, and recipient.")
        return False
    temp_image_path = None
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['sender_email']
        msg['To'] = EMAIL_CONFIG['recipient_email']
        msg['Subject'] = f"{EMAIL_CONFIG['subject_prefix']} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        body = (
            f"⚠️ THREAT DETECTED ⚠️\n\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Threat Level: {threat_details.get('threat_level', 'Unknown')}\n"
            f"Threat Score: {threat_details.get('threat_score', 0)}\n"
            f"Detected Objects: {', '.join(threat_details.get('detected_objects', []))}\n\n"
            "This is an automated alert from your AI Threat Detection System.\n"
            "Please review the attached image and take appropriate action.\n\n---\nAI Security System\nAutomated Threat Detection"
        )
        msg.attach(MIMEText(body, 'plain'))
        temp_image_path = f"threat_detection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        cv2.imwrite(temp_image_path, frame)
        with open(temp_image_path, 'rb') as f:
            img_data = f.read()
            msg.attach(MIMEImage(img_data, name=os.path.basename(temp_image_path)))
        with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
            server.starttls()
            server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
            server.sendmail(
                EMAIL_CONFIG['sender_email'],
                EMAIL_CONFIG['recipient_email'],
                msg.as_string()
            )
        print(f"✅ Threat alert email sent successfully to {EMAIL_CONFIG['recipient_email']}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if temp_image_path and os.path.exists(temp_image_path):
            os.remove(temp_image_path)

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
    """Check if YOLOv8 model exists and return its path. No download logic here."""
    model_path = "yolov8n.pt"
    if not os.path.exists(model_path):
        print(f"Error: Model file '{model_path}' not found. Please ensure the file is present in the directory.")
        raise FileNotFoundError(f"Model file '{model_path}' not found.")
    return model_path

def load_yolo():
    """Load the YOLOv8n model."""
    model_path = download_yolo_model()
    model = YOLO(model_path)
    print("Model classes:", model.names)
    print("\n[INFO] Please verify that the weapon_classes list below matches your model's class names:")
    print("Current weapon_classes:", ['knife', 'scissors', 'baseball bat', 'bottle', 'cell phone', 'pistol', 'gun'])
    print("If your model uses different class names for weapons, update the weapon_classes list in detect_threat().\n")
    return model

def detect_threat(frame, model):
    """Detect potential threats in a frame using YOLOv8 (only 'gun' and 'rifle' classes supported, no person class)."""
    if frame is None or frame.size == 0:
        print("⚠️ Invalid frame received")
        return None, False, {
            'threat_level': 'Error',
            'threat_score': 0,
            'detected_objects': [],
            'status': 'Invalid frame'
        }
    frame = cv2.resize(frame, (480, 480))
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
    try:
        # Lowered confidence threshold for more stable detection
        results = model(frame, conf=0.15)[0]
    except Exception as e:
        print(f"⚠️ YOLO inference error: {e}")
        return frame, False, {
            'threat_level': 'Error',
            'threat_score': 0,
            'detected_objects': [],
            'status': 'Model inference error'
        }
    weapon_classes = ['gun', 'rifle']
    weapon_detected = False
    threat_score = 0
    detected_objects = []
    detected_class_names = set()
    for result in results.boxes.data.tolist():
        x1, y1, x2, y2, confidence, class_id = result
        class_name = results.names[int(class_id)]
        detected_class_names.add(class_name)
        detected_objects.append(class_name)
        color = (0, 0, 255) if class_name in weapon_classes else (255, 255, 255)
        if class_name in weapon_classes:
            weapon_detected = True
            threat_score = 10
        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
        cv2.putText(frame, f"{class_name}: {confidence:.2f}", (int(x1), int(y1 - 10)),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    if detected_class_names:
        print(f"[DEBUG] Detected classes in frame: {detected_class_names}")
    if weapon_detected:
        threat_detected = True
        status = "HIGH THREAT: Weapon Detected!"
        status_color = (0, 0, 255)
        threat_level = "HIGH THREAT"
    else:
        threat_detected = False
        status = "Normal: No Threats Detected"
        status_color = (0, 255, 0)
        threat_level = "NORMAL"
    cv2.putText(frame, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)
    cv2.putText(frame, f"Threat Score: {threat_score}", (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)
    objects_text = "Detected: " + ", ".join(set(detected_objects))
    cv2.putText(frame, objects_text, (10, 90),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    return frame, threat_detected, {
        'threat_level': threat_level,
        'threat_score': threat_score,
        'detected_objects': list(set(detected_objects)),
        'status': status,
        'weapon_detected': weapon_detected
    }

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
    
    detection_buffer = [False] * 10  # Increased buffer size for more smoothing
    hold_counter = 0  # Hold period counter
    hold_period = 10  # Number of frames to hold alert after last detection
    
    print("System ready! Press 'q' to exit.")
    print("📧 Email alerts will be sent when threats are detected.")
    
    def send_email_background(frame, threat_details):
        threading.Thread(target=send_threat_email, args=(frame.copy(), threat_details), daemon=True).start()
    while True:
        try:
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame")
                break
            result = detect_threat(frame, model)
            if result is None:
                print("⚠️ Skipping frame due to detection error")
                continue
            frame, threat_detected, threat_details = result
            frame_count += 1
            if frame_count % 30 == 0:
                end_time = time.time()
                fps = 30 / (end_time - start_time)
                start_time = time.time()
                cv2.putText(frame, f"FPS: {fps:.1f}", (10, 120),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.imshow("AI Threat Detection System", frame)
            detection_buffer.pop(0)
            detection_buffer.append(threat_detected)
            # Require detection in at least 2 of last 10 frames
            smoothed_threat = sum(detection_buffer) >= 2
            # Hold period logic: keep alert active for 10 frames after last detection
            if smoothed_threat:
                hold_counter = hold_period
            elif hold_counter > 0:
                hold_counter -= 1
                smoothed_threat = True
            if arduino and smoothed_threat != previous_state:
                try:
                    signal = "1" if smoothed_threat else "0"
                    arduino.write(signal.encode())
                    print(f"Sent signal {signal} to Arduino")
                    previous_state = smoothed_threat
                except Exception as e:
                    print(f"⚠️ Failed to send signal to Arduino: {e}")
            current_time = time.time()
            if smoothed_threat and (current_time - last_email_time) > email_cooldown:
                if not is_email_config_valid():
                    print("[EMAIL] Email config incomplete. Not sending email.")
                else:
                    print("📧 Sending threat alert email (background)...")
                    send_email_background(frame, threat_details)
                    last_email_time = current_time
                    print(f"⏰ Next email can be sent in {email_cooldown} seconds")
            if cv2.waitKey(1) == ord('q'):
                break
        except Exception as e:
            print(f"⚠️ Error in main loop: {e}")
            print("Continuing...")
            time.sleep(0.1)
            continue
    cap.release()
    cv2.destroyAllWindows()
    if arduino:
        arduino.close()
        print("Arduino connection closed")
    print("System shutdown complete")
    
    return True

if __name__ == "__main__":
    main()