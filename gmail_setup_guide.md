# 🔧 Gmail App Password Setup Guide

## 🚨 Error: (534, b'5.7.9 Application-specific p...)

This error means Gmail is rejecting your app password. Here's how to fix it:

## 📋 Step-by-Step Fix

### Step 1: Enable 2-Step Verification
1. Go to [Google Account Settings](https://myaccount.google.com/)
2. Click **"Security"** in the left sidebar
3. Find **"2-Step Verification"** and click **"Get Started"**
4. Follow the steps to enable 2-Step Verification
5. **Wait 24 hours** after enabling (Google requirement)

### Step 2: Generate App Password
1. Go back to **"Security"** in Google Account Settings
2. Find **"App passwords"** (appears after 2-Step Verification is enabled)
3. Click **"App passwords"**
4. Select **"Mail"** as the app
5. Select **"Other (Custom name)"** and name it "Threat Detection"
6. Click **"Generate"**
7. **Copy the 16-character password** (looks like: `abcd efgh ijkl mnop`)

### Step 3: Update Your Configuration
1. In the GUI, click **"📧 Show Email Config"**
2. Enter your Gmail address in **"Sender"**
3. Enter the **16-character app password** (with spaces) in **"Password"**
4. Enter recipient email in **"Recipient"**
5. Click **"Save"**
6. Click **"Test"** to verify

## ⚠️ Common Mistakes

### ❌ Don't Use:
- Your regular Gmail password
- A password without spaces
- An old app password
- A password from a different account

### ✅ Do Use:
- The exact 16-character app password
- Include the spaces in the password
- A fresh app password
- The password from the same Gmail account

## 🔍 Troubleshooting

### If you still get errors:

1. **Check 2-Step Verification:**
   - Make sure it's been enabled for at least 24 hours
   - Verify it's enabled on the correct Google account

2. **Generate New App Password:**
   - Delete the old app password
   - Generate a completely new one
   - Make sure to select "Mail" as the app

3. **Check Account Security:**
   - Make sure your Google account isn't locked
   - Check if there are any security alerts

4. **Alternative: Use Less Secure Apps (Not Recommended)**
   - Only if app passwords don't work
   - Go to Google Account settings
   - Find "Less secure app access"
   - Enable it temporarily

## 📞 Still Having Issues?

If you continue to have problems:

1. **Check your Gmail account status** at [Google Account](https://myaccount.google.com/)
2. **Verify 2-Step Verification** is properly enabled
3. **Try generating the app password again**
4. **Make sure you're using the correct Gmail account**

## 🎯 Quick Test

After setting up, test with this format:
- **Sender:** your.email@gmail.com
- **Password:** abcd efgh ijkl mnop (16 characters with spaces)
- **Recipient:** recipient@example.com

The app password should look exactly like this: `thfw sild cwpt gxhs` (your actual password will be different) 