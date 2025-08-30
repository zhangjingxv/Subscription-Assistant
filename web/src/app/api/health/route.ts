import { NextResponse } from 'next/server';

export async function GET() {
  return NextResponse.json({
    status: 'healthy',
    service: 'attentionsync-web',
    timestamp: new Date().toISOString()
  });
}