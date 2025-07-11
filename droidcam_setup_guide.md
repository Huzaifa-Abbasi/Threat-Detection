# 📱 DroidCam Setup Guide for AI Threat Detection System

This guide will help you set up DroidCam to use your phone's camera with the AI Threat Detection System.

## 🎯 What is DroidCam?

DroidCam is a free app that turns your smartphone into a wireless webcam. It allows you to use your phone's camera for video calls, streaming, and in our case, AI threat detection.

## 📋 Prerequisites

- **Android or iOS smartphone**
- **Computer with WiFi capability**
- **Both devices on the same WiFi network**
- **DroidCam app installed on your phone**

## 📱 Step 1: Install DroidCam App

### Android
1. Open Google Play Store
2. Search for "DroidCam"
3. Install "DroidCam - Webcam" by Dev47Apps
4. Open the app

### iOS
1. Open App Store
2. Search for "DroidCam"
3. Install "DroidCam" by Dev47Apps
4. Open the app

## 🔧 Step 2: Configure DroidCam App

1. **Open DroidCam app** on your phone
2. **Grant camera permissions** when prompted
3. **Note the IP address** displayed on the app (e.g., `192.168.1.100`)
4. **Note the port number** (usually `4747`)
5. **Tap "Start"** to begin streaming

## 💻 Step 3: Test DroidCam Connection

### Option 1: Standalone Test
Run the dedicated DroidCam test:
```bash
python threat_detection.py --test-droidcam
```

### Option 2: Test During Main Program
1. Run the main program: `python threat_detection.py`
2. Select option "3. Test DroidCam connection"
3. Enter your DroidCam URL when prompted

## 🌐 Step 4: DroidCam URL Format

The DroidCam URL follows this format:
```
http://[YOUR_PHONE_IP]:4747/video
```

### Common Examples:
- `http://192.168.1.100:4747/video`
- `http://192.168.1.101:4747/video`
- `http://10.0.0.100:4747/video`

### How to Find Your Phone's IP:
1. **In DroidCam app**: The IP is displayed on the main screen
2. **In Android Settings**: 
   - Settings → Network & Internet → WiFi
   - Tap your connected network
   - Look for "IP address"
3. **In iOS Settings**:
   - Settings → WiFi
   - Tap the "i" icon next to your network
   - Look for "IP Address"

## 🚀 Step 5: Using DroidCam with Threat Detection

1. **Start DroidCam app** on your phone
2. **Run the threat detection system**:
   ```bash
   python threat_detection.py
   ```
3. **Select camera source**: Choose option "2. DroidCam (IP Camera)"
4. **Enter DroidCam URL**: Use the URL from your phone
5. **Start detection**: The system will use your phone's camera

## 🔍 Troubleshooting

### Connection Issues

**Problem**: "Server unreachable" or "Connection timeout"
**Solutions**:
- ✅ Ensure both devices are on the same WiFi network
- ✅ Check if DroidCam app is running and streaming
- ✅ Verify the IP address matches your phone's IP
- ✅ Try restarting DroidCam app
- ✅ Check if any firewall is blocking the connection

**Problem**: "Connection unstable" or poor video quality
**Solutions**:
- ✅ Move devices closer to WiFi router
- ✅ Reduce WiFi network congestion
- ✅ Check phone's battery level (low battery can affect performance)
- ✅ Close other apps on your phone
- ✅ Try using 5GHz WiFi if available

### Video Quality Issues

**Problem**: Low frame rate or lag
**Solutions**:
- ✅ Use 5GHz WiFi instead of 2.4GHz
- ✅ Reduce distance between phone and router
- ✅ Close background apps on phone
- ✅ Ensure good lighting conditions

**Problem**: Video not displaying
**Solutions**:
- ✅ Check if camera permissions are granted
- ✅ Restart DroidCam app
- ✅ Try different camera (front/back) in DroidCam settings

## ⚙️ Advanced Configuration

### Custom Port
If you need to use a different port:
1. In DroidCam app, go to Settings
2. Change the port number
3. Update the URL accordingly: `http://[IP]:[PORT]/video`

### Quality Settings
In DroidCam app settings, you can adjust:
- **Resolution**: Higher resolution = better quality but more bandwidth
- **Frame Rate**: Higher FPS = smoother video but more processing
- **Bitrate**: Higher bitrate = better quality but more network usage

## 🔒 Security Considerations

- **Local Network Only**: DroidCam only works on your local WiFi network
- **No Internet Required**: The connection is direct between your phone and computer
- **Temporary Connection**: DroidCam connection is only active while the app is running

## 📞 Support

If you're still having issues:

1. **Check DroidCam's official documentation**: https://www.dev47apps.com/
2. **Verify your network setup**: Ensure both devices are on the same network
3. **Try alternative IP camera apps**: IP Webcam, EpocCam, etc.
4. **Use USB connection**: Some phones support USB webcam mode

## 🎉 Success!

Once DroidCam is working, you can:
- ✅ Use your phone's camera for threat detection
- ✅ Position your phone for optimal surveillance angles
- ✅ Monitor areas without moving your computer
- ✅ Use multiple phones for different camera angles

---

**Note**: DroidCam is a third-party app. The threat detection system is not affiliated with DroidCam developers.
