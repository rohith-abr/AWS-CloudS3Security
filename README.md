# 🌩️ CloudS3Security – AWS S3 Public Access Monitoring & Management Tool

CloudS3Security is a real-time security monitoring and remediation tool built to identify and fix public access misconfigurations in Amazon S3 buckets. It provides a user-friendly dashboard, alerting system, and one-click remediation for securing your cloud data.

---

## 🚀 Features

- 🔐 **Login with AWS Credentials** (Access Key & Secret Key)
- 📊 **Real-time Dashboard** showing:
  - Total files & storage in MB
  - Public vs Private buckets
  - Risk tags for high-risk file types
- ⚠️ **Alert System**
  - File-level access alerts
- ✅ **One-Click Remediation**:
  - “Make Private” button for any public bucket
- 📤 **Downloadable Reports** in PDF format
- 📧 **Email Notifications**
  
---

## 🔧 Installation Guide

Follow the steps below to install and run **CloudS3Security** on your system.

---

### 🖥️ Windows

1. **Unzip** the folder  
   Example path:  
   `C:\Users\YourName\Downloads\CloudS3Security`

2. **Open Command Prompt** and navigate to the project directory:
   ```bash
   cd Downloads\CloudS3Security
   ```

3. **Create a virtual environment**:
   ```bash
   python -m venv venv
   ```

4. **Activate the environment**:
   ```bash
   venv\Scripts\activate
   ```

5. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

6. **Run the Flask app**:
   ```bash
   python app.py
   ```
   → Access at: [http://127.0.0.1:4030](http://127.0.0.1:4030)

7. **Optional – Run Electron GUI**  
   First, install Node.js from [https://nodejs.org](https://nodejs.org)  
   Then run:
   ```bash
   npm install
   npm start
   ```

---

### 🍏 macOS

1. **Unzip** the folder  
   Example path:  
   `/Users/yourname/Downloads/CloudS3Security`

2. **Open Terminal** and navigate to the directory:
   ```bash
   cd Downloads/CloudS3Security
   ```

3. **Create and activate virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

4. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the Flask app**:
   ```bash
   python3 app.py
   ```
   → Access at: [http://127.0.0.1:4030](http://127.0.0.1:4030)

6. **Optional – Run Electron GUI**  
   Install Node.js from [https://nodejs.org](https://nodejs.org)  
   Then run:
   ```bash
   npm install
   npm start
   ```

---

✅ That’s it! Your app should now be running locally.
