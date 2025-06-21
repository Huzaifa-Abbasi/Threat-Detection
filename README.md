# 🔒 AI-Based Threat Detection System using YOLOv8 and Arduino

This project is an AI-powered **real-time threat detection system** that uses the YOLOv8 model for object detection (e.g., weapons, persons) and communicates with an Arduino to trigger alarms or responses when threats are detected.

## 📌 Features

- 🔍 Real-time threat detection using YOLOv8
- 🚨 Detects weapons like knives, scissors, bottles, and suspicious people
- 🎯 Calculates threat levels and scores
- 🖥️ Displays detection results with bounding boxes and threat info
- 📟 Sends signal to Arduino to activate buzzer or alert device
- 📧 **Email alerts with threat images** (NEW!)
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
- **Arduino Uno/Nano** (optional for buzzer)

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
- Webcam (internal or external)
- Arduino (Uno/Nano, optional)
- Internet connection (for first-time model download)
- Gmail account (for email notifications)

### 🐍 Python Libraries

Install all required libraries using pip:

```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install opencv-python numpy pyserial ultralytics
```
