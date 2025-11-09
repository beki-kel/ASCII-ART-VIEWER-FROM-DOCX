# Render Deployment Guide

## Prerequisites
- GitHub account with your repository
- Render account (free tier available)

## Deployment Steps

### 1. Prepare Your Repository
Make sure all files are committed and pushed to GitHub:
```bash
git add -A
git commit -m "Prepare for Render deployment"
git push origin main
```

### 2. Connect to Render
1. Go to [render.com](https://render.com) and sign up/login
2. Click "New +" → "Web Service"
3. Connect your GitHub account if not already connected
4. Select your `ASCII-ART-VIEWER-FROM-DOCX` repository

### 3. Configure Your Service
- **Name**: ascii-art-viewer (or your preferred name)
- **Environment**: Python 3
- **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Plan**: Free (or your preferred plan)

### 4. Environment Variables
Add these environment variables in Render dashboard:
- `PYTHON_VERSION`: 3.11.0
- `ENVIRONMENT`: production
- `DEBUG`: false

### 5. Advanced Settings (Optional)
- **Health Check Path**: `/health`
- **Auto-Deploy**: Yes (recommended)

### 6. Deploy
1. Click "Create Web Service"
2. Render will automatically build and deploy your application
3. You'll get a URL like: `https://your-app-name.onrender.com`

## Post-Deployment

### Test Your Application
1. Visit your Render URL
2. Check the health endpoint: `https://your-app-name.onrender.com/health`
3. Test the ASCII art processing functionality
4. Verify WebSocket connections work

### Monitor Logs
- Use Render dashboard to monitor application logs
- Check for any startup errors or runtime issues

### Custom Domain (Optional)
- In Render dashboard, go to Settings → Custom Domains
- Add your domain and configure DNS

## Troubleshooting

### Common Issues:
1. **Build fails**: Check requirements.txt for incompatible versions
2. **App doesn't start**: Verify start command and port configuration
3. **Static files not loading**: Ensure correct file paths in templates
4. **WebSocket issues**: Render supports WebSockets on all plans

### Debugging:
- Check Render logs for detailed error messages
- Use the health check endpoint to verify basic functionality
- Test locally first: `uvicorn main:app --host 0.0.0.0 --port 8000`

## Free Tier Limitations
- Apps sleep after 15 minutes of inactivity
- 750 hours per month of usage
- Slower cold starts

For production use, consider upgrading to a paid plan for always-on service.