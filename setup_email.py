#!/usr/bin/env python3
"""
OACA Email Configuration Setup
This script helps configure SMTP settings for sending welcome emails.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def test_smtp_connection(smtp_server, smtp_port, username, password):
    """Test SMTP connection with provided credentials"""
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(username, password)
        server.quit()
        return True, "Connection successful!"
    except Exception as e:
        return False, f"Connection failed: {str(e)}"

def send_test_email(smtp_server, smtp_port, username, password, from_email, from_name, to_email):
    """Send a test email to verify configuration"""
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "OACA Email Configuration Test"
        msg['From'] = f"{from_name} <{from_email}>"
        msg['To'] = to_email
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Email Test</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #0b1d44 0%, #0a1a3d 100%); border-radius: 16px; padding: 40px; color: white;">
                <h1 style="color: #e6eeff; text-align: center; margin-bottom: 20px;">✅ Email Configuration Test</h1>
                <p style="color: #9db0d9; text-align: center; font-size: 18px;">
                    Congratulations! Your OACA email system is working correctly.
                </p>
                <div style="background: rgba(34, 197, 94, 0.1); border: 1px solid rgba(34, 197, 94, 0.3); border-radius: 8px; padding: 20px; margin: 20px 0;">
                    <h3 style="color: #22c55e; margin: 0 0 10px 0;">Configuration Details:</h3>
                    <p style="margin: 5px 0; color: #e6eeff;"><strong>SMTP Server:</strong> {smtp_server}:{smtp_port}</p>
                    <p style="margin: 5px 0; color: #e6eeff;"><strong>From:</strong> {from_name} &lt;{from_email}&gt;</p>
                    <p style="margin: 5px 0; color: #e6eeff;"><strong>To:</strong> {to_email}</p>
                </div>
                <p style="color: #9db0d9; text-align: center; font-size: 14px; margin-top: 30px;">
                    This test email was sent at {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </p>
            </div>
        </body>
        </html>
        """
        
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(username, password)
        server.sendmail(from_email, to_email, msg.as_string())
        server.quit()
        
        return True, "Test email sent successfully!"
    except Exception as e:
        return False, f"Failed to send test email: {str(e)}"

def main():
    print("=" * 60)
    print("OACA Email Configuration Setup")
    print("=" * 60)
    print()
    
    print("This script will help you configure SMTP settings for sending welcome emails.")
    print("You'll need SMTP credentials from your email provider.")
    print()
    
    # Get SMTP configuration
    print("Enter your SMTP configuration:")
    smtp_server = input("SMTP Server (e.g., smtp.gmail.com): ").strip()
    smtp_port = int(input("SMTP Port (e.g., 587): ").strip() or "587")
    username = input("SMTP Username (your email): ").strip()
    password = input("SMTP Password (or app password): ").strip()
    from_email = input("From Email (e.g., noreply@oaca.local): ").strip()
    from_name = input("From Name (e.g., OACA Aviation System): ").strip()
    
    print()
    print("Testing SMTP connection...")
    success, message = test_smtp_connection(smtp_server, smtp_port, username, password)
    print(f"Result: {message}")
    
    if not success:
        print("\n❌ SMTP connection failed. Please check your credentials and try again.")
        return
    
    print("\n✅ SMTP connection successful!")
    
    # Ask if user wants to send test email
    test_email = input("\nSend test email? (y/n): ").strip().lower()
    if test_email == 'y':
        to_email = input("Test email address: ").strip()
        print("Sending test email...")
        success, message = send_test_email(smtp_server, smtp_port, username, password, from_email, from_name, to_email)
        print(f"Result: {message}")
        
        if success:
            print("\n🎉 Email configuration is working perfectly!")
        else:
            print("\n❌ Test email failed. Please check your settings.")
    
    # Generate .env content
    print("\n" + "=" * 60)
    print("Environment Variables Configuration")
    print("=" * 60)
    print()
    print("Add these variables to your .env file or set them as environment variables:")
    print()
    print(f"SMTP_SERVER={smtp_server}")
    print(f"SMTP_PORT={smtp_port}")
    print(f"SMTP_USERNAME={username}")
    print(f"SMTP_PASSWORD={password}")
    print(f"SMTP_FROM_EMAIL={from_email}")
    print(f"SMTP_FROM_NAME={from_name}")
    print()
    print("After setting these variables, restart your application.")
    print("New users will receive beautiful welcome emails with their credentials!")

if __name__ == "__main__":
    main()
