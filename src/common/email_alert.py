# src/common/email_alert.py
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent

# ⚠️ এখানে আপনার Gmail এবং App Password দিন
SENDER_EMAIL = "apshoraahmed770@gmail.com" 
SENDER_PASSWORD = "tslf kaly ypfx vhlm" # নিচে দেখুন কীভাবে বানাবেন

def get_user_email_by_machine(machine_id: str) -> str:
    """মেশিনের আইডি দিয়ে রেজিস্টার্ড ইউজারের ইমেইল খুঁজে বের করা"""
    users_file = BASE_DIR / "users.json"
    if not users_file.exists():
        return None
        
    with open(users_file, "r") as f:
        data = json.load(f)
        
    for user in data["users"]:
        if machine_id in user["assigned_machines"]:
            return user["email"], user["name"]
    return None, None

def send_critical_alert(machine_id: str, details: dict):
    """Critical হলে ইমেইল পাঠানো"""
    receiver_email, user_name = get_user_email_by_machine(machine_id)
    
    if not receiver_email:
        print(f"⚠️ No registered user found for machine: {machine_id}")
        return

    # ইমেইলের বিষয়বস্তু তৈরি করা (কারণসহ)
    subject = f"🚨 URGENT: Critical Alert for {machine_id.replace('_', ' ').title()}"
    
    # Details ডিকশনারি থেকে সুন্দর একটি মেসেজ বানানো
    reason_text = "\n".join([f"• {key.replace('_', ' ').title()}: {value}" for key, value in details.items()])
    
    body = f"""
    Hello {user_name},

    This is an automated alert from the Industrial AI Predictive Maintenance System.

    ⚠️ Your machine '{machine_id}' has entered a CRITICAL state.

    🔍 Reason for Critical Alert:
    {reason_text}

    Please inspect the machine immediately via the Dashboard to prevent catastrophic failure.

    Regards,
    AI Maintenance Team
    """

    # ইমেইল কনফিগারেশন
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = receiver_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Gmail SMTP সার্ভার ব্যবহার করা হচ্ছে
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"✅ Critical Alert Email sent successfully to {receiver_email}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")