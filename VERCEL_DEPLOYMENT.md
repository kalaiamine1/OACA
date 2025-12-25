# Vercel Deployment Guide for OACA

This guide will help you deploy your Flask application to Vercel.

## Prerequisites

1. A Vercel account (sign up at [vercel.com](https://vercel.com))
2. Vercel CLI installed (optional, for CLI deployment)
3. MongoDB Atlas account (or your MongoDB connection string)
4. All environment variables ready

## Step 1: Install Vercel CLI (Optional)

If you want to deploy from the command line:

```bash
npm install -g vercel
```

Or use the Vercel web dashboard instead.

## Step 2: Set Up Environment Variables

Before deploying, you need to set up the following environment variables in Vercel:

### Required Environment Variables

1. **MONGO_URI** - Your MongoDB connection string
   - Example: `mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority`

2. **DB_NAME** - Your database name
   - Example: `OACA`

3. **JWT_SECRET** - A secure random string for JWT token signing
   - Generate a strong secret: `openssl rand -hex 32`
   - **Important**: Use a strong, random secret in production!

4. **COOKIE_SECURE** - Set to `true` for HTTPS (Vercel uses HTTPS)
   - Value: `true`

5. **COOKIE_SAMESITE** - Cookie SameSite attribute
   - Value: `Lax` or `None` (if using cross-site)

### Optional Environment Variables

6. **JWT_EXPIRES_MIN** - JWT token expiration in minutes (default: 15)

7. **DEFAULT_USER_EMAIL** - Default admin email (default: kalaiamine203@gmail.com)

8. **DEFAULT_USER_PASSWORD** - Default admin password (default: ChangeMe123!)

9. **SMTP_SERVER** - SMTP server for emails (default: smtp.gmail.com)

10. **SMTP_PORT** - SMTP port (default: 587)

11. **SMTP_USERNAME** - SMTP username/email

12. **SMTP_PASSWORD** - SMTP password/app password

13. **SMTP_FROM_EMAIL** - From email address

14. **SMTP_FROM_NAME** - From name

## Step 3: Deploy to Vercel

### Option A: Deploy via Vercel Dashboard

1. Go to [vercel.com](https://vercel.com) and sign in
2. Click "Add New Project"
3. Import your Git repository (GitHub, GitLab, or Bitbucket)
4. Configure the project:
   - **Framework Preset**: Other
   - **Root Directory**: `./` (root)
   - **Build Command**: Leave empty (Vercel will auto-detect)
   - **Output Directory**: Leave empty
5. Add all environment variables from Step 2
6. Click "Deploy"

### Option B: Deploy via CLI

1. Navigate to your project directory:
   ```bash
   cd C:\Users\PC\Desktop\OACA
   ```

2. Login to Vercel:
   ```bash
   vercel login
   ```

3. Deploy:
   ```bash
   vercel
   ```

4. For production deployment:
   ```bash
   vercel --prod
   ```

5. Set environment variables via CLI:
   ```bash
   vercel env add MONGO_URI
   vercel env add DB_NAME
   vercel env add JWT_SECRET
   vercel env add COOKIE_SECURE
   # ... add all other variables
   ```

## Step 4: Configure MongoDB Atlas (if using)

If you're using MongoDB Atlas:

1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create a cluster (free tier available)
3. Get your connection string
4. Add your Vercel deployment IP to MongoDB Atlas Network Access:
   - Go to Network Access
   - Click "Add IP Address"
   - Click "Allow Access from Anywhere" (0.0.0.0/0) for simplicity
   - Or add Vercel's IP ranges (check Vercel docs)

## Step 5: Verify Deployment

After deployment:

1. Visit your Vercel deployment URL (e.g., `https://your-project.vercel.app`)
2. Test the application:
   - Try accessing `/home`
   - Try logging in with default credentials
   - Test API endpoints

## Important Notes

### OpenCV on Vercel

- The project uses `opencv-python-headless` which is optimized for serverless
- If you encounter size issues, OpenCV features will gracefully degrade
- Face detection features may not work if OpenCV fails to load

### File Uploads

- The `uploads/` directory is excluded from deployment
- File uploads in serverless environments require external storage (S3, Cloudinary, etc.)
- Consider migrating file uploads to a cloud storage service

### Cold Starts

- Vercel serverless functions have cold starts
- First request after inactivity may be slower
- MongoDB connection is established on each cold start

### Static Files

- HTML, CSS, JS, and image files are served as static files
- Large files may need to be moved to a CDN

## Troubleshooting

### Build Fails

- Check that all dependencies in `requirements.txt` are compatible
- Ensure Python version is 3.10 (configured in `vercel.json`)
- Check build logs in Vercel dashboard

### MongoDB Connection Issues

- Verify `MONGO_URI` is correct
- Check MongoDB Atlas network access settings
- Ensure IP whitelist includes Vercel IPs

### Environment Variables Not Working

- Make sure variables are set for the correct environment (Production, Preview, Development)
- Redeploy after adding new environment variables
- Check variable names match exactly (case-sensitive)

### 404 Errors

- Verify `vercel.json` routes are correct
- Check that static files are in the root directory
- Ensure API routes start with `/api/`

## Updating Your Deployment

After making changes:

1. **Via Git**: Push to your connected repository, Vercel will auto-deploy
2. **Via CLI**: Run `vercel --prod` again

## Support

- Vercel Docs: https://vercel.com/docs
- Flask on Vercel: https://vercel.com/docs/frameworks/flask
- MongoDB Atlas: https://docs.atlas.mongodb.com

