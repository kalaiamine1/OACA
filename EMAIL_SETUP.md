# Email Configuration for OACA

## Overview
The OACA system sends welcome emails to new users with their login credentials. This guide explains how to configure email sending.

## Environment Variables

Create a `.env` file in the project root with the following email configuration:

```env
# Email Configuration (SMTP)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@oaca.local
SMTP_FROM_NAME=OACA Aviation System
```

## Gmail Setup

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate an App Password**:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate a password for "Mail"
   - Use this password as `SMTP_PASSWORD`

## Other Email Providers

### Outlook/Hotmail
```env
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
```

### Yahoo
```env
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587
```

### Custom SMTP
```env
SMTP_SERVER=mail.your-domain.com
SMTP_PORT=587
SMTP_USERNAME=your-email@your-domain.com
SMTP_PASSWORD=your-password
```

## Testing

1. Start the application
2. Create a new user via the admin dashboard
3. Check the console logs for email status
4. Verify the email is received

## Fallback Behavior

If email configuration is not provided or fails:
- User creation still succeeds
- Credentials are logged to console
- Admin is notified of email failure
- User can still access the system

## Email Template

The system sends a professional HTML email with:
- OACA branding and styling
- User's login credentials (email, matricule, password)
- Role information
- Login instructions
- Security warnings

## Troubleshooting

### Common Issues

1. **"Authentication failed"**
   - Check username/password
   - Ensure 2FA is enabled for Gmail
   - Use app password, not regular password

2. **"Connection refused"**
   - Check SMTP server and port
   - Verify firewall settings
   - Test with different port (465 for SSL)

3. **"Email not received"**
   - Check spam folder
   - Verify email address is correct
   - Check SMTP logs in console

### Debug Mode

Enable debug logging by checking the console output when creating users. The system will show:
- Email sending attempts
- Success/failure messages
- SMTP connection details

