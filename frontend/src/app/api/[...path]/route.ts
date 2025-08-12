import { NextRequest, NextResponse } from 'next/server';
import { handleUpload, type HandleUploadBody } from '@vercel/blob/client';

const backendUrl = () => process.env.BACKEND_URL || process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

function passthroughHeaders(headers: Headers): HeadersInit {
  const h: Record<string, string> = {};
  const forward = ['x-api-key', 'content-type'];
  headers.forEach((value, key) => {
    const k = key.toLowerCase();
    if (forward.includes(k)) h[k] = value;
  });
  return h;
}

async function getBody(req: NextRequest): Promise<BodyInit | undefined> {
  const ct = req.headers.get('content-type') || '';
  if (ct.includes('multipart/form-data')) {
    const form = await req.formData();
    return form as unknown as BodyInit;
  }
  if (ct.includes('application/json')) {
    const json = await req.json().catch(() => undefined);
    return json ? JSON.stringify(json) : undefined;
  }
  const text = await req.text().catch(() => undefined);
  return text;
}

async function proxy(res: Response) {
  const contentType = res.headers.get('content-type') || '';
  const init: ResponseInit = { status: res.status, headers: { 'content-type': contentType } };
  if (contentType.startsWith('application/json')) {
    const data = await res.json().catch(() => null);
    return Response.json(data, init);
  }
  const buf = await res.arrayBuffer();
  return new Response(buf, init);
}

type RouteContext = {
  params: Promise<{ path: string[] }>
}

export async function GET(req: NextRequest, context: RouteContext) {
  const params = await context.params;
  const search = req.nextUrl.search || '';
  const target = `${backendUrl()}/${(params?.path || []).join('/')}${search}`;
  const res = await fetch(target, { method: 'GET', headers: passthroughHeaders(req.headers), cache: 'no-store' });
  return proxy(res);
}

export async function POST(req: NextRequest, context: RouteContext) {
  const params = await context.params;
  const path = (params?.path || []).join('/');
  
  // Handle blob upload endpoint specially
  if (path === 'blob/upload') {
    const body = (await req.json()) as HandleUploadBody;
    
    try {
      const jsonResponse = await handleUpload({
        body,
        request: req,
        onBeforeGenerateToken: async (pathname, clientPayload) => {
          return {
            allowedContentTypes: ['video/*'],
            maximumSizeInBytes: 5 * 1024 * 1024 * 1024, // 5GB
            addRandomSuffix: true,
          };
        },
        onUploadCompleted: async ({ blob, tokenPayload }) => {
          console.log('blob upload completed', blob, tokenPayload);
        },
      });
      
      return NextResponse.json(jsonResponse);
    } catch (error) {
      return NextResponse.json(
        { error: error instanceof Error ? error.message : String(error) },
        { status: 400 },
      );
    }
  }
  
  // Regular proxy for other endpoints
  const search = req.nextUrl.search || '';
  const target = `${backendUrl()}/${path}${search}`;
  const body = await getBody(req);
  const res = await fetch(target, { method: 'POST', headers: passthroughHeaders(req.headers), body });
  return proxy(res);
}

export async function PUT(req: NextRequest, context: RouteContext) {
  const params = await context.params;
  const search = req.nextUrl.search || '';
  const target = `${backendUrl()}/${(params?.path || []).join('/')}${search}`;
  const body = await getBody(req);
  const res = await fetch(target, { method: 'PUT', headers: passthroughHeaders(req.headers), body });
  return proxy(res);
}

export async function DELETE(req: NextRequest, context: RouteContext) {
  const params = await context.params;
  const search = req.nextUrl.search || '';
  const target = `${backendUrl()}/${(params?.path || []).join('/')}${search}`;
  const res = await fetch(target, { method: 'DELETE', headers: passthroughHeaders(req.headers) });
  return proxy(res);
}


