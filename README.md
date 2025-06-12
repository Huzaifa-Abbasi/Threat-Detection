# 🔒 AI-Based Threat Detection System using YOLOv8 and Arduino

This project is an AI-powered **real-time threat detection system** that uses the YOLOv8 model for object detection (e.g., weapons, persons) and communicates with an Arduino to trigger alarms or responses when threats are detected.

## 📌 Features

- 🔍 Real-time threat detection using YOLOv8
- 🚨 Detects weapons like knives, scissors, bottles, and suspicious people
- 🎯 Calculates threat levels and scores
- 🖥️ Displays detection results with bounding boxes and threat info
- 📟 Sends signal to Arduino to activate buzzer or alert device
- ⚠️ Warns on low lighting conditions or blocked camera
- 📦 Modular code for easy extension (logs, alerts, GUI, etc.)

---

## 🧠 Technologies Used

- **Python 3.10**
- **YOLOv8** via `ultralytics`
- **OpenCV** for camera feed and display
- **NumPy**
- **Serial Communication** (`pyserial`) for Arduino
- **Arduino Uno/Nano** (optional for buzzer)

---

## ⚙️ Setup Instructions

### ✅ Requirements

- Python 3.10
- Webcam (internal or external)
- Arduino (Uno/Nano, optional)
- Internet connection (for first-time model download)

### 🐍 Python Libraries

Install all required libraries using pip:

```bash
pip install opencv-python numpy pyserial ultralytics
