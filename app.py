from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
import boto3
from datetime import datetime
from io import BytesIO
import json
import csv
import os
import requests
from fpdf import FPDF
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = 'clouds3_ui_secret'

EVAL_LOG = "evaluation_results.csv"
LAMBDA_EMAIL_URL = "https://7rxnxdyszh.execute-api.us-east-1.amazonaws.com/prod/SendEmailCloudS3"

def log_evaluation(file_name, predicted_risk, true_risk):
    file_exists = os.path.exists(EVAL_LOG)
    with open(EVAL_LOG, mode='a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["file_name", "predicted_risk", "true_risk"])
        writer.writerow([file_name, predicted_risk, true_risk])

def send_alert_email(subject, message, to):
    payload = {
        "to": to,
        "subject": subject,
        "message": message
    }
    headers = {
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(LAMBDA_EMAIL_URL, json=payload, headers=headers)
        print("✅ Email API response:", response.json())
        return response.json()
    except Exception as e:
        print("❌ Error sending email:", str(e))
        return {"message": "Failed to send email"}

@app.route('/')
def home():
    return redirect(url_for('email_page'))

@app.route('/email', methods=['GET', 'POST'])
def email_page():
    if request.method == 'POST':
        session['username'] = request.form.get('username')
        session['email'] = request.form.get('email')
        session['alerts_enabled'] = False
        return redirect(url_for('intro'))
    return render_template('email.html')

@app.route('/intro', methods=['GET', 'POST'])
def intro():
    if request.method == 'POST':
        return redirect(url_for('login'))
    return render_template('intro.html', username=session.get('username'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        access_key = request.form.get('access_key')
        secret_key = request.form.get('secret_key')
        if not access_key or not secret_key:
            return render_template('login.html', error="Please provide both AWS keys.")
        session['access_key'] = access_key
        session['secret_key'] = secret_key
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('email_page'))

@app.route('/toggle_alerts', methods=['POST'])
def toggle_alerts():
    session['alerts_enabled'] = not session.get('alerts_enabled', False)
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    username = session.get('username')
    access_key = session.get('access_key')
    secret_key = session.get('secret_key')
    if not access_key or not secret_key:
        return redirect(url_for('login'))

    try:
        s3 = boto3.client('s3', aws_access_key_id=access_key, aws_secret_access_key=secret_key)
        buckets = s3.list_buckets()
    except:
        return render_template("login.html", error="Invalid AWS credentials.")

    buckets_list = buckets['Buckets']
    if not buckets_list:
        return render_template('index.html', username=username, data=[], total=0, size_gb=0, public_count=0, private_count=0, show_warning=False, high_risk_files=[])

    latest_bucket = sorted(buckets_list, key=lambda b: b['CreationDate'], reverse=True)[0]

    total_files, total_size, all_data, high_risk_files = 0, 0, [], []
    ext = ['leak', 'public', 'sensitive', 'csv', 'zip', 'env', 'password']
    risky_keywords = ["leak", "backup", "env", "csv", "sql", "password"]

    for bucket in buckets_list:
        try:
            name = bucket['Name']
            created = bucket['CreationDate'].strftime('%Y-%m-%d %H:%M:%S')
            objects = s3.list_objects_v2(Bucket=name).get('Contents', [])
            count = len(objects)
            size = sum(obj['Size'] for obj in objects)
            total_files += count
            total_size += size

            is_public = False
            try:
                if s3.get_bucket_policy_status(Bucket=name)['PolicyStatus']['IsPublic']:
                    is_public = True
            except: pass
            try:
                for g in s3.get_bucket_acl(Bucket=name)['Grants']:
                    if g.get('Grantee', {}).get('URI') == 'http://acs.amazonaws.com/groups/global/AllUsers':
                        is_public = True
            except: pass

            tag = "High Risk" if any(x in obj['Key'].lower() for obj in objects for x in ext) else ""

            if session.get('alerts_enabled') and name == latest_bucket['Name']:
                risky_files = []
                for obj in objects:
                    key = obj['Key']
                    if any(keyword in key.lower() for keyword in risky_keywords):
                        risky_files.append(f"{key} (⚠️ High Risk)")
                    else:
                        risky_files.append(key)
                file_summary = '<br>- '.join(risky_files) if risky_files else "No files in this bucket."
                message = f"""Hi {session['username']},<br><br>You've created a new S3 bucket.<br><br>🪣 <b>Bucket Name:</b> {name}<br>📅 <b>Created On:</b> {created}<br>🔐 <b>Status:</b> {'Public' if is_public else 'Private'}<br><br>📁 <b>Files:</b><br>- {file_summary}<br><br>Regards,<br><b>CloudS3Security</b>"""
                send_alert_email(
                    f"🔔 {session['username']}, New S3 Bucket Created on AWS",
                    message,
                    session['email']
                )

            for obj in objects:
                key = obj['Key']
                predicted_risk = 1 if any(e in key.lower() for e in ext) else 0
                true_risk = 1 if any(e in key.lower() for e in ["leak", "backup", "env", "csv", "sql"]) else 0
                log_evaluation(key, predicted_risk, true_risk)
                if predicted_risk:
                    high_risk_files.append(key)

            all_data.append({
                'bucket': name,
                'files': count,
                'size': round(size / (1024 ** 2), 2),
                'status': 'Public' if is_public else 'Private',
                'uploaded': created,
                'fixed': '' if is_public else datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'tag': tag
            })
        except:
            continue

    session['report_data'] = all_data  # Save for PDF generation

    return render_template('index.html',
        username=username,
        data=all_data,
        total=total_files,
        size_gb=round(total_size / (1024 ** 2), 2),
        public_count=len([d for d in all_data if d['status'] == 'Public']),
        private_count=len([d for d in all_data if d['status'] == 'Private']),
        show_warning=len([d for d in all_data if d['status'] == 'Public']) >= 3,
        high_risk_files=high_risk_files
    )

@app.route('/make_private/<bucket>', methods=['POST'])
def make_private(bucket):
    access_key = session.get('access_key')
    secret_key = session.get('secret_key')
    try:
        s3 = boto3.client('s3', aws_access_key_id=access_key, aws_secret_access_key=secret_key)
        s3.delete_bucket_policy(Bucket=bucket)
        s3.put_public_access_block(
            Bucket=bucket,
            PublicAccessBlockConfiguration={
                'BlockPublicAcls': True,
                'IgnorePublicAcls': True,
                'BlockPublicPolicy': True,
                'RestrictPublicBuckets': True
            }
        )
    except Exception as e:
        print("Remediation Error:", e)
    return redirect(url_for('dashboard'))

@app.route('/make_public/<bucket>', methods=['POST'])
def make_public(bucket):
    access_key = session.get('access_key')
    secret_key = session.get('secret_key')
    try:
        s3 = boto3.client('s3', aws_access_key_id=access_key, aws_secret_access_key=secret_key)
        s3.put_public_access_block(
            Bucket=bucket,
            PublicAccessBlockConfiguration={
                'BlockPublicAcls': False,
                'IgnorePublicAcls': False,
                'BlockPublicPolicy': False,
                'RestrictPublicBuckets': False
            }
        )
        public_policy = {
            "Version": "2012-10-17",
            "Statement": [{
                "Sid": "PublicReadGetObject",
                "Effect": "Allow",
                "Principal": "*",
                "Action": "s3:GetObject",
                "Resource": f"arn:aws:s3:::{bucket}/*"
            }]
        }
        s3.put_bucket_policy(Bucket=bucket, Policy=json.dumps(public_policy))
    except Exception as e:
        print("Make Public Error:", e)
    return redirect(url_for('dashboard'))

@app.route('/download_report')
def download_report():
    data = session.get('report_data', [])
    if not data:
        return "No data available for report."

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.cell(200, 10, "CloudS3Security - Bucket Report", ln=True, align='C')
    pdf.ln(5)

    headers = ["Bucket", "Files", "Size(MB)", "Status", "Uploaded", "Remediated", "Risk"]
    widths = [35, 15, 20, 20, 35, 35, 25]

    for i, header in enumerate(headers):
        pdf.cell(widths[i], 8, header, border=1, align='C')
    pdf.ln()

    for row in data:
        row_data = [
            row['bucket'],
            str(row['files']),
            f"{row['size']:.2f}",
            row['status'],
            row['uploaded'],
            row['fixed'],
            row['tag'] if row['tag'] else '-'
        ]
        for i, cell in enumerate(row_data):
            pdf.cell(widths[i], 8, cell, border=1)
        pdf.ln()

    file_path = "s3_report.pdf"
    pdf.output(file_path)
    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 4060))
    app.run(use_reloader=False, debug=True, port=4030)