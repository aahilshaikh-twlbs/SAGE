import { handleUpload, type HandleUploadBody } from '@vercel/blob/client';
import { NextResponse } from 'next/server';

export async function POST(request: Request): Promise<NextResponse> {
  const body = (await request.json()) as HandleUploadBody;
  try {
    const jsonResponse = await handleUpload({
      token: process.env.BLOB_READ_WRITE_TOKEN,
      request,
      body,
      onBeforeGenerateToken: async (pathname, clientPayload) => {
        return {
          access: 'public',
          addRandomSuffix: true,
          allowedContentTypes: ['video/*'],
          maximumSizeInBytes: 5 * 1024 * 1024 * 1024, // 5GB
          cacheControlMaxAge: 60 * 60 * 24 * 30, // 30 days
        };
      },
      onUploadCompleted: async ({ blob }) => {
        // no-op; client receives blob.url after upload
        console.log('Blob upload completed:', blob.url);
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


