# 📧 OACA Email Configuration Guide

## Quick Setup for Gmail

### Step 1: Enable 2-Factor Authentication
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable **2-Step Verification** if not already enabled

### Step 2: Generate App Password
1. In Google Account Security, go to **2-Step Verification**
2. Scroll down to **App passwords**
3. Select **Mail** as the app
4. Copy the generated 16-character password

### Step 3: Set Environment Variables
Create a `.env` file in your project root with:

```env
# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-16-character-app-password
SMTP_FROM_EMAIL=noreply@oaca.local
SMTP_FROM_NAME=OACA Aviation System
```

### Step 4: Test Configuration
Run the email setup script:
```bash
python setup_email.py
```

## Other Email Providers

### Outlook/Hotmail
```env
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USERNAME=your-email@outlook.com
SMTP_PASSWORD=your-password
```

### Yahoo
```env
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587
SMTP_USERNAME=your-email@yahoo.com
SMTP_PASSWORD=your-app-password
```

### Custom SMTP Server
```env
SMTP_SERVER=mail.your-domain.com
SMTP_PORT=587
SMTP_USERNAME=your-email@your-domain.com
SMTP_PASSWORD=your-password
```

## Email Template Features

The OACA system sends professional HTML emails with:

- ✈️ **Aviation-themed branding** with OACA colors
- 🔐 **Complete login credentials** (email, matricule, password)
- 📱 **Responsive design** that works on all devices
- ⚠️ **Security warnings** and login instructions
- 🎨 **Professional styling** with gradients and shadows

## Troubleshooting

### "Authentication failed"
- ✅ Use app password, not regular password
- ✅ Ensure 2FA is enabled for Gmail
- ✅ Check username is correct

### "Connection refused"
- ✅ Verify SMTP server and port
- ✅ Check firewall settings
- ✅ Try port 465 for SSL

### "Email not received"
- ✅ Check spam folder
- ✅ Verify email address is correct
- ✅ Check SMTP logs in console

## Security Notes

- 🔒 **Never commit** `.env` file to version control
- 🔒 **Use app passwords** instead of main passwords
- 🔒 **Rotate credentials** regularly
- 🔒 **Monitor email logs** for suspicious activity

## Testing

After configuration, create a test user to verify:
1. Email is sent successfully
2. HTML template renders correctly
3. Credentials are included
4. Styling looks professional

The system will show "✅ Welcome email sent successfully" in the dashboard when working correctly.
