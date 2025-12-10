# API Key Validation Fixes

## **Issue Description**

When accessing `tl-sage.vercel.app` from a different browser or computer, the add API key screen would appear but validation would fail, with no server-side calls being made to the backend.

## **Root Cause Analysis**

The problem was caused by a **mismatch between frontend API configuration and backend accessibility**:

1. **Frontend API Base URL**: Defaulted to `http://localhost:8000` when `NEXT_PUBLIC_API_URL` environment variable was not set
2. **Backend Server**: Accessible at `http://209.38.142.207:8000` from the internet
3. **CORS Configuration**: Backend was properly configured to allow `https://tl-sage.vercel.app`
4. **API Calls**: Frontend was attempting to call `localhost:8000` (which doesn't exist on remote machines)

## **Fixes Implemented**

### **1. Frontend API Configuration Update**

**File**: `frontend/src/lib/api.ts`

**Change**: Updated API base URL logic to use relative URLs in production

```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 
  (typeof window !== 'undefined' && window.location.hostname !== 'localhost' 
    ? '/api'  // Use relative URL for production (works with Next.js rewrites)
    : 'http://localhost:8000');
```

**Why**: Relative URLs (`/api`) work with Next.js rewrites and don't depend on hardcoded localhost URLs

### **2. Next.js Rewrite Configuration**

**File**: `frontend/next.config.ts`

**Change**: Configured API route rewrites to forward requests to the actual backend server

```typescript
const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://209.38.142.207:8000/:path*',
      },
    ];
  },
};
```

**Why**: Routes all `/api/*` requests to the actual backend server instead of localhost

### **3. Debug Logging Added**

**File**: `frontend/src/lib/api.ts`

**Change**: Added console logging to help troubleshoot API configuration issues

```typescript
// Debug logging
if (typeof window !== 'undefined') {
  console.log('API Base URL:', API_BASE_URL);
  console.log('Current hostname:', window.location.hostname);
  console.log('NEXT_PUBLIC_API_URL:', process.env.NEXT_PUBLIC_API_URL);
}
```

**Why**: Provides visibility into what API base URL is being used in different environments

## **How the Fix Works**

### **Before Fix**
1. User visits `tl-sage.vercel.app` from different computer
2. Frontend loads with no `NEXT_PUBLIC_API_URL` set
3. API client defaults to `http://localhost:8000`
4. API calls fail because `localhost:8000` doesn't exist on remote machine
5. No server-side calls are made

### **After Fix**
1. User visits `tl-sage.vercel.app` from different computer
2. Frontend detects non-localhost hostname
3. API client uses `/api` as base URL
4. Next.js rewrites `/api/validate-key` to `http://209.38.142.207:8000/validate-key`
5. API calls succeed and reach the backend server

## **Environment Variables Required**

### **Vercel Deployment**
- `BACKEND_URL`: `http://209.38.142.207:8000` (already set)
- `NEXT_PUBLIC_API_URL`: Can be left unset (will use `/api`)

### **Local Development**
- No environment variables needed (defaults to `http://localhost:8000`)

## **Testing the Fix**

### **1. Deploy Changes**
```bash
# Frontend changes will auto-deploy to Vercel
git push origin main
```

### **2. Verify from Different Computer**
1. Open `tl-sage.vercel.app` in a different browser/computer
2. Open browser console (F12)
3. Check console logs for:
   - `API Base URL: /api`
   - `Current hostname: tl-sage.vercel.app`
   - `NEXT_PUBLIC_API_URL: undefined`

### **3. Test API Key Validation**
1. Enter a valid TwelveLabs API key
2. Submit the form
3. Check that validation succeeds
4. Verify backend logs show the API call

## **Backend Verification**

The backend server at `http://209.38.142.207:8000` is confirmed accessible via:
- ✅ Health endpoint: `GET /health` returns successful response
- ✅ CORS properly configured for `https://tl-sage.vercel.app`
- ✅ API key validation endpoint: `POST /validate-key` functional

## **Files Modified**

1. **`frontend/src/lib/api.ts`**
   - Updated API base URL logic
   - Added debug logging

2. **`frontend/next.config.ts`**
   - Added API rewrite configuration
   - Hardcoded production backend URL

## **Deployment Notes**

- **Frontend**: Changes auto-deploy to Vercel
- **Backend**: No changes required (already accessible)
- **Environment**: Vercel environment variables already configured
- **Testing**: Verify from different computer/browser after deployment

## **Future Improvements**

1. **Environment Variable Fallback**: Consider using `NEXT_PUBLIC_API_URL` for more flexible configuration
2. **Health Check**: Add frontend health check to verify backend connectivity
3. **Error Handling**: Improve error messages for network connectivity issues
4. **Monitoring**: Add logging for failed API calls to help with debugging

## **Related Documentation**

- [User Guide](USER_GUIDE.md) - API endpoint documentation
- [Developer Guide](DEVELOPER_GUIDE.md) - Technical implementation details
- [Upload Process](UPLOAD_PROCESS.md) - Video processing workflow
- [Large Video Handling](LARGE_VIDEO_HANDLING.md) - Video size limitations


