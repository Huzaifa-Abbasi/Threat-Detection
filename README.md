# 🔒 AI-Based Threat Detection System using YOLOv8 and Arduino

This project is an AI-powered **real-time threat detection system** that uses the YOLOv8 model for object detection (e.g., weapons, persons) and communicates with an Arduino to trigger alarms or responses when threats are detected.

## 📌 Features

- 🔍 Real-time threat detection using YOLOv8
- 🚨 Detects weapons like knives, scissors, bottles, and suspicious people
- 🎯 Calculates threat levels and scores
- 🖥️ Displays detection results with bounding boxes and threat info
- 📟 Sends signal to Arduino to activate buzzer or alert device
- 📧 **Email alerts with threat images** (NEW!)
- 📱 **DroidCam support for phone camera** (NEW!)
- ⚠️ Warns on low lighting conditions or blocked camera
- 📦 Modular code for easy extension (logs, alerts, GUI, etc.)

---

## 🧠 Technologies Used

- **Python 3.10**
- **YOLOv8** via `ultralytics`
- **OpenCV** for camera feed and display
- **NumPy**
- **Serial Communication** (`pyserial`) for Arduino
- **SMTP Email** for threat notifications
- **Requests** for DroidCam connection testing
- **Arduino Uno/Nano** (optional for buzzer)

---

## 📷 Camera Sources

The system supports multiple camera sources for flexible deployment:

### 🖥️ Webcam (Default)
- Uses your computer's built-in or USB webcam
- Simple setup, no additional hardware needed
- Good for desktop monitoring

### 📱 DroidCam (Phone Camera)
- Use your smartphone as a wireless camera
- Perfect for remote monitoring and surveillance
- Position your phone anywhere within WiFi range
- Supports both Android and iOS devices

#### Quick DroidCam Setup:
1. Install DroidCam app on your phone
2. Run: `python threat_detection.py --test-droidcam`
3. Follow the interactive setup guide
4. Use your phone's camera for threat detection

**📖 Full DroidCam Guide**: See `droidcam_setup_guide.md` for detailed instructions.

---

## 📧 Email Notification Setup

### 🎯 Overview
The system can automatically send email alerts with threat detection images when potential threats are detected. This feature is perfect for:
- Security monitoring
- Remote surveillance
- Automated incident reporting
- Integration with security systems

### ⚙️ Email Configuration

#### Option 1: Interactive Setup (Recommended)
Run the dedicated email setup script:
```bash
python setup_email.py
```

#### Option 2: Manual Configuration
1. **Get Gmail App Password:**
   - Go to your Google Account settings
   - Enable 2-Step Verification
   - Go to Security > App passwords
   - Generate a new app password for 'Mail'

2. **Create email_config.txt:**
   ```
   your_email@gmail.com
   your_app_password_here
   recipient@example.com
   ```

### 🔧 Email Features
- **Automatic Image Capture:** Saves and attaches threat detection frames
- **Detailed Threat Information:** Includes threat level, score, and detected objects
- **Cooldown Protection:** Prevents spam (1 email per minute maximum)
- **Professional Formatting:** Clean, informative email layout
- **Error Handling:** Graceful failure handling with user feedback

### 📋 Email Content
Each threat alert includes:
- ⚠️ Threat level and score
- 📅 Timestamp of detection
- 🎯 List of detected objects
- 📸 Attached image with detection overlay
- 📝 Detailed threat analysis

---

## ⚙️ Setup Instructions

### ✅ Requirements

- Python 3.10
- Webcam (internal or external) OR smartphone with DroidCam app
- Arduino (Uno/Nano, optional)
- Internet connection (for first-time model download)
- Gmail account (for email notifications)
- WiFi network (for DroidCam functionality)

### 🐍 Python Libraries

Install all required libraries using pip:

```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install opencv-python numpy pyserial ultralytics requests
```

### 🚀 Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the system:**
   ```bash
   python threat_detection.py
   ```

3. **Choose camera source:**
   - Option 1: Webcam (default)
   - Option 2: DroidCam (phone camera)
   - Option 3: Test DroidCam connection

4. **Configure email (optional):**
   - Follow the interactive email setup
   - Or create `email_config.txt` manually

### 📱 DroidCam Quick Test

Test DroidCam connection without running full detection:
```bash
python threat_detection.py --test-droidcam
```

---

## 🎮 Usage

### Basic Usage
```bash
python threat_detection.py
```

### DroidCam Testing
```bash
python threat_detection.py --test-droidcam
```

### GUI Version (Alternative)
```bash
python threat_detection_gui.py
```

### Controls
- **'q'**: Quit the application
- **Camera Selection**: Choose between webcam and DroidCam
- **Email Setup**: Configure email alerts interactively

---

## 🔧 Configuration

### Camera Settings
- **Resolution**: 640x480 (configurable)
- **Frame Rate**: 30 FPS
- **Buffer Size**: Optimized for low latency

### DroidCam Settings
- **Default URL**: `http://192.168.1.100:4747/video`
- **Timeout**: 5 seconds
- **Retry Attempts**: 3
- **Test Frames**: 5 frames for connection validation

### Email Settings
- **Cooldown**: 60 seconds between emails
- **Image Format**: JPEG
- **SMTP**: Gmail (configurable)

---

## 🛠️ Troubleshooting

### Camera Issues
- **Webcam not detected**: Check device manager and permissions
- **DroidCam connection failed**: See `droidcam_setup_guide.md`
- **Poor video quality**: Check lighting and camera settings

### Email Issues
- **Authentication failed**: Verify app password and 2FA
- **Connection timeout**: Check internet and SMTP settings
- **No emails sent**: Check email configuration

### Detection Issues
- **Low accuracy**: Ensure good lighting conditions
- **False positives**: Adjust confidence threshold in code
- **Model not loading**: Check if `yolov8n.pt` is present

---

## 📁 Project Structure

```
Threat-Detection/
├── threat_detection.py          # Main detection script
├── threat_detection_gui.py      # GUI version
├── requirements.txt             # Python dependencies
├── yolov8n.pt                  # YOLOv8 model file
├── email_config.txt            # Email configuration
├── droidcam_setup_guide.md     # DroidCam setup guide
├── gmail_setup_guide.md        # Email setup guide
├── threat_alert_system.ino     # Arduino code
└── README.md                   # This file
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 Acknowledgments

- **YOLOv8** by Ultralytics for object detection
- **OpenCV** for computer vision capabilities
- **DroidCam** by Dev47Apps for phone camera integration
- **Arduino** community for hardware integration

---

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the setup guides
3. Open an issue on GitHub

**Happy Threat Detection! 🛡️**
