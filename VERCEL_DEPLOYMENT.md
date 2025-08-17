# 🚀 Vercel Deployment Guide

## Your Setup
- **Frontend**: Deployed on Vercel (connected to GitHub repo)
- **Backend**: Running on production server at `209.38.142.207:8000`
- **Current Machine**: This IS your production backend

## Environment Variables Setup

### 1. In Vercel Dashboard
Go to your project settings → Environment Variables and add:

```
NEXT_PUBLIC_API_URL=http://209.38.142.207:8000
```

**This points to your production backend running on this machine**

### 2. Local Development
Create `.env.local` in the frontend folder:

```bash
# Copy from env.example and update
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Deployment Steps

### 1. Commit and Push
```bash
git add .
git commit -m "Configure for Vercel deployment with production backend"
git push origin main
```

### 2. Vercel Auto-Deploy
- Vercel will automatically detect the push
- Build and deploy your frontend
- Frontend will connect to your production backend at `209.38.142.207:8000`

### 3. Verify Deployment
- Check your Vercel deployment URL
- Verify the frontend can connect to your production backend
- Test video upload and comparison

## Configuration Files Updated

✅ **`frontend/src/lib/api.ts`** - Uses environment variable for API URL
✅ **`frontend/next.config.ts`** - Dynamic backend URL in rewrites
✅ **`frontend/env.example`** - Points to your production backend: `209.38.142.207:8000`

## Production Backend Status

- **IP**: `209.38.142.207`
- **Port**: `8000`
- **Status**: ✅ Accessible from internet
- **Health**: ✅ Running and healthy

## Troubleshooting

### Frontend Can't Connect to Backend
1. Check `NEXT_PUBLIC_API_URL=http://209.38.142.207:8000` in Vercel
2. Verify backend is running: `python3 app.py`
3. Check if port 8000 is open and accessible

### Build Errors
1. Ensure environment variable is set in Vercel dashboard
2. Check Next.js config syntax
3. Verify TypeScript compilation

## Local vs Production

- **Local**: Uses `http://localhost:8000`
- **Production**: Uses `http://209.38.142.207:8000` (your current machine)
- **Environment**: Automatically switches based on deployment
