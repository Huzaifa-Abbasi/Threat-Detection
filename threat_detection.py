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
import requests
from urllib.parse import urlparse

# Email configuration - Update these with your email settings
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',  # For Gmail
    'smtp_port': 587,
    'sender_email': 'try.huzaifa@gmail.com',  # Replace with your email
    'sender_password': 'letstryit',  # Replace with your app password
    'recipient_email': 'huzaifaa66asi@gmail.com',  # Replace with recipient email
    'subject_prefix': 'THREAT DETECTED - AI Security System'
}

# DroidCam configuration
DROIDCAM_CONFIG = {
    'default_url': 'http://192.168.1.100:4747/video',
    'timeout': 5,
    'retry_attempts': 3,
    'connection_test_frames': 5
}

def test_droidcam_connection(url):
    """Test DroidCam connection and return status."""
    print(f"🔍 Testing DroidCam connection to: {url}")
    
    try:
        # Ensure URL has proper format
        if not url.startswith('http://') and not url.startswith('https://'):
            url = 'http://' + url
        
        # Test basic connectivity
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        print(f"Testing server connectivity to: {base_url}")
        
        # Test if server is reachable
        response = requests.get(base_url, timeout=DROIDCAM_CONFIG['timeout'])
        if response.status_code != 200:
            print(f"❌ DroidCam server responded with status: {response.status_code}")
            return False, f"Server error: {response.status_code}"
        
        print("✅ Server connectivity test passed")
        
        # Test video stream
        print(f"Testing video stream at: {url}")
        cap = cv2.VideoCapture(url)
        if not cap.isOpened():
            print("❌ Could not open DroidCam video stream")
            return False, "Could not open video stream"
        
        print("✅ Video stream opened successfully")
        
        # Test reading frames
        success_count = 0
        for i in range(DROIDCAM_CONFIG['connection_test_frames']):
            ret, frame = cap.read()
            if ret and frame is not None and frame.size > 0:
                success_count += 1
                print(f"Frame {i+1}: Success ({frame.shape})")
            else:
                print(f"Frame {i+1}: Failed to read")
            time.sleep(0.1)
        
        cap.release()
        
        if success_count >= 3:
            print(f"✅ DroidCam connection successful! ({success_count}/{DROIDCAM_CONFIG['connection_test_frames']} frames)")
            return True, f"Connected successfully ({success_count}/{DROIDCAM_CONFIG['connection_test_frames']} frames)"
        else:
            print(f"⚠️ DroidCam connected but unstable ({success_count}/{DROIDCAM_CONFIG['connection_test_frames']} frames)")
            return False, f"Connection unstable ({success_count}/{DROIDCAM_CONFIG['connection_test_frames']} frames)"
            
    except requests.exceptions.ConnectionError:
        print("❌ DroidCam connection failed - server unreachable")
        return False, "Server unreachable"
    except requests.exceptions.Timeout:
        print("❌ DroidCam connection timeout")
        return False, "Connection timeout"
    except Exception as e:
        print(f"❌ DroidCam test error: {str(e)}")
        return False, f"Test error: {str(e)}"

def setup_droidcam(url=None):
    """Setup DroidCam connection with retry logic."""
    if url is None:
        url = DROIDCAM_CONFIG['default_url']
    
    print(f"📱 Setting up DroidCam connection to: {url}")
    
    for attempt in range(DROIDCAM_CONFIG['retry_attempts']):
        try:
            cap = cv2.VideoCapture(url)
            
            if not cap.isOpened():
                print(f"⚠️ Attempt {attempt + 1}: Could not open DroidCam stream")
                if attempt < DROIDCAM_CONFIG['retry_attempts'] - 1:
                    time.sleep(1)
                    continue
                else:
                    print("❌ Failed to connect to DroidCam after all attempts")
                    return None
            
            # Test reading a frame
            ret, frame = cap.read()
            if not ret or frame is None:
                print(f"⚠️ Attempt {attempt + 1}: Could not read frame from DroidCam")
                cap.release()
                if attempt < DROIDCAM_CONFIG['retry_attempts'] - 1:
                    time.sleep(1)
                    continue
                else:
                    print("❌ Failed to read frames from DroidCam after all attempts")
                    return None
            
            print(f"✅ DroidCam connected successfully on attempt {attempt + 1}")
            return cap
            
        except Exception as e:
            print(f"⚠️ Attempt {attempt + 1}: DroidCam setup error: {str(e)}")
            if attempt < DROIDCAM_CONFIG['retry_attempts'] - 1:
                time.sleep(1)
                continue
            else:
                print("❌ Failed to setup DroidCam after all attempts")
                return None
    
    return None

def setup_camera_source(source_type="webcam", droidcam_url=None):
    """Setup camera source (webcam or DroidCam)."""
    print(f"📷 Setting up camera source: {source_type}")
    
    if source_type.lower() == "droidcam" or source_type.lower() == "ipcam":
        if droidcam_url is None:
            droidcam_url = DROIDCAM_CONFIG['default_url']
        
        print(f"📱 Attempting DroidCam connection to: {droidcam_url}")
        cap = setup_droidcam(droidcam_url)
        
        if cap is None:
            print("❌ DroidCam connection failed")
            return None  # Return None instead of falling back to webcam
        else:
            print("✅ DroidCam connection established")
    else:
        # Default webcam setup
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ Failed to open webcam")
            return None
        print("✅ Webcam connection established")
    
    # Set camera properties for better performance
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer size for lower latency
    
    return cap

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

def test_droidcam_standalone():
    """Standalone function to test DroidCam connection."""
    print("🔍 DroidCam Connection Tester")
    print("=" * 40)
    
    print("Enter your DroidCam connection details:")
    print("(The system will automatically add 'http://' and '/video')")
    
    # Get IP address
    ip_address = input("Enter your phone's IP address (e.g., 192.168.1.100): ").strip()
    if not ip_address:
        print("❌ IP address is required!")
        return
    
    # Get port (with default)
    port_input = input("Enter port number (press Enter for default 4747): ").strip()
    port = port_input if port_input else "4747"
    
    # Build the full URL
    droidcam_url = f"http://{ip_address}:{port}/video"
    
    print(f"\nTesting connection to: {droidcam_url}")
    print("Make sure:")
    print("1. DroidCam app is running on your phone")
    print("2. Your phone and computer are on the same WiFi network")
    print("3. The IP address matches your phone's IP address")
    
    input("\nPress Enter to start testing...")
    
    success, message = test_droidcam_connection(droidcam_url)
    
    if success:
        print(f"\n✅ SUCCESS: {message}")
        print("\nDroidCam is working correctly!")
        print("You can now use this URL in the main threat detection system.")
        
        # Test actual video capture
        print("\nTesting video capture...")
        cap = setup_droidcam(droidcam_url)
        if cap:
            print("✅ Video capture test successful!")
            print("Reading a few frames to verify...")
            
            for i in range(5):
                ret, frame = cap.read()
                if ret and frame is not None:
                    print(f"Frame {i+1}: {frame.shape}")
                else:
                    print(f"Frame {i+1}: Failed to read")
                time.sleep(0.5)
            
            cap.release()
            print("✅ DroidCam is fully functional!")
        else:
            print("❌ Video capture test failed")
    else:
        print(f"\n❌ FAILED: {message}")
        print("\nTroubleshooting tips:")
        print("1. Check if DroidCam app is running on your phone")
        print("2. Verify your phone's IP address (check DroidCam app)")
        print("3. Ensure both devices are on the same WiFi network")
        print("4. Try restarting DroidCam app")
        print("5. Check if any firewall is blocking the connection")

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
    
    # Interactive menu for camera selection
    print("\n📷 Camera Selection Menu:")
    print("=" * 40)
    print("1. Use PC Webcam")
    print("2. Use DroidCam Virtual Camera (Recommended)")
    print("3. Use DroidCam with IP")
    print("4. Test DroidCam connection")
    print("5. Exit")
    
    cap = None
    while cap is None:
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            print("Using PC webcam...")
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                print("❌ Failed to open webcam. Please try again.")
                continue
            print("✅ Webcam connection established")
            
        elif choice == '2':
            print("Using DroidCam Virtual Camera...")
            cap = cv2.VideoCapture(1)  # This is the working DroidCam index
            if not cap.isOpened():
                print("❌ Failed to open DroidCam Virtual Camera.")
                print("Make sure DroidCam is installed and running on your PC.")
                continue
            
            # Test reading a frame
            ret, frame = cap.read()
            if not ret:
                print("❌ Could not read frame from DroidCam Virtual Camera.")
                cap.release()
                continue
                
            print("✅ DroidCam Virtual Camera connection successful!")
            
        elif choice == '3':
            print("\nDroidCam IP Connection Setup:")
            print("1. Make sure DroidCam is running on your phone")
            print("2. Check the IP address shown in DroidCam app")
            print("3. Enter the details below:")
            
            ip = input("\nEnter DroidCam IP address (e.g., 192.168.100.2): ").strip()
            if not ip:
                print("IP address cannot be empty. Please try again.")
                continue
                
            port = input("Enter DroidCam port (default: 4747): ").strip() or "4747"
            
            # First try the virtual camera
            print("\nTrying virtual camera first...")
            cap = cv2.VideoCapture(1)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    print("✅ Virtual camera connection successful!")
                    break
                cap.release()
            
            # If virtual camera fails, try IP
            print("\nTrying IP connection...")
            source = f"http://{ip}:{port}/video"
            print(f"Connecting to: {source}")
            
            cap = cv2.VideoCapture(source, cv2.CAP_FFMPEG)
            if not cap.isOpened():
                # If HTTP fails, try RTSP
                rtsp_url = source.replace('http://', 'rtsp://')
                print(f"Trying RTSP connection: {rtsp_url}")
                cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
            
            if not cap.isOpened():
                print("❌ Failed to connect to DroidCam via IP.")
                print("Please try option 2 (DroidCam Virtual Camera) instead.")
                continue
                
            print("✅ DroidCam IP connection successful!")
            
        elif choice == '4':
            print("Testing DroidCam connection...")
            print("Enter your DroidCam connection details:")
            print("(The system will automatically add 'http://' and '/video')")
            
            # Get IP address
            ip_address = input("Enter your phone's IP address (e.g., 192.168.1.100): ").strip()
            if not ip_address:
                print("❌ IP address is required!")
                continue
            
            # Get port (with default)
            port_input = input("Enter port number (press Enter for default 4747): ").strip()
            port = port_input if port_input else "4747"
            
            # Build the full URL
            droidcam_url = f"http://{ip_address}:{port}/video"
            print(f"Testing connection to: {droidcam_url}")
            
            success, message = test_droidcam_connection(droidcam_url)
            if success:
                print(f"✅ {message}")
                use_droidcam = input("DroidCam test successful! Use DroidCam? (y/n): ").strip().lower()
                if use_droidcam == 'y':
                    # Try virtual camera first
                    print("Trying virtual camera...")
                    cap = cv2.VideoCapture(1)
                    if cap.isOpened():
                        ret, frame = cap.read()
                        if ret:
                            print("✅ Using DroidCam Virtual Camera!")
                            break
                        cap.release()
                    
                    # Fallback to IP
                    cap = setup_camera_source("droidcam", droidcam_url)
                    if cap is None:
                        print("❌ DroidCam connection failed despite successful test. Please try again.")
                        continue
                else:
                    print("Using webcam instead...")
                    cap = cv2.VideoCapture(0)
                    if not cap.isOpened():
                        print("❌ Failed to open webcam. Please try again.")
                        continue
            else:
                print(f"❌ {message}")
                print("DroidCam test failed. Please try again or select a different option.")
                continue
                
        elif choice == '5':
            print("Exiting...")
            return
        else:
            print("Invalid choice. Please try again.")
            continue
    
    if not cap or not cap.isOpened():
        print("Error: Could not open camera.")
        print("\nTroubleshooting steps:")
        print("1. Make sure your webcam is connected and working")
        print("2. Check if another application is using the webcam")
        print("3. For DroidCam: Make sure the app is running on your phone")
        print("4. For DroidCam: Verify your phone and computer are on the same network")
        return

    # Set camera properties for better performance
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer size for lower latency
    
    print("\nPress 'q' to quit")
    print("Press 's' to save current frame")
    print("Press 'r' to reset counters")
    print("📧 Email alerts will be sent when threats are detected.")
    
    previous_state = False  # Track the previous threat state
    frame_count = 0
    start_time = time.time()
    last_email_time = 0  # Track last email sent time
    email_cooldown = 60  # Send email only once every 60 seconds
    
    # Threat detection statistics
    threat_count = 0
    total_threats_detected = 0
    
    detection_buffer = [False] * 10  # Increased buffer size for more smoothing
    hold_counter = 0  # Hold period counter
    hold_period = 10  # Number of frames to hold alert after last detection
    
    def send_email_background(frame, threat_details):
        threading.Thread(target=send_threat_email, args=(frame.copy(), threat_details), daemon=True).start()
    
    def save_current_frame(frame, threat_details):
        """Save the current frame with threat information."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"threat_detection_{timestamp}.jpg"
        
        # Create a copy of the frame to add save confirmation
        save_frame = frame.copy()
        cv2.putText(save_frame, f"SAVED: {timestamp}", (10, save_frame.shape[0] - 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        cv2.imwrite(filename, save_frame)
        print(f"✅ Frame saved as: {filename}")
        print(f"   Threat Level: {threat_details.get('threat_level', 'Unknown')}")
        print(f"   Detected Objects: {', '.join(threat_details.get('detected_objects', []))}")
    
    def reset_counters():
        """Reset all counters and statistics."""
        nonlocal frame_count, threat_count, total_threats_detected, start_time, last_email_time
        frame_count = 0
        threat_count = 0
        total_threats_detected = 0
        start_time = time.time()
        last_email_time = 0
        print("🔄 All counters reset!")
    
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
            
            # Update threat statistics
            if threat_detected:
                threat_count += 1
                if threat_count == 1:  # First detection in sequence
                    total_threats_detected += 1
            
            # Calculate FPS
            if frame_count % 30 == 0:
                end_time = time.time()
                fps = 30 / (end_time - start_time)
                start_time = time.time()
                cv2.putText(frame, f"FPS: {fps:.1f}", (10, 120),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Add statistics to frame
            cv2.putText(frame, f"Frame: {frame_count}", (10, 150),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(frame, f"Threats: {total_threats_detected}", (10, 170),
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
            
            # Reset threat count when no threat detected
            if not threat_detected:
                threat_count = 0
            
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
            
            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                save_current_frame(frame, threat_details)
            elif key == ord('r'):
                reset_counters()
                
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
    import sys
    
    # Check if DroidCam test is requested
    if len(sys.argv) > 1 and sys.argv[1] == "--test-droidcam":
        test_droidcam_standalone()
    else:
        main()