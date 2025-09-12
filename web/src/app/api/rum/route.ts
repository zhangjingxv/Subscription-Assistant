import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    // TODO: forward to your observability backend; for now, log to stdout
    console.log('[RUM]', JSON.stringify(body));
    return NextResponse.json({ status: 'ok' });
  } catch (e: any) {
    return NextResponse.json({ error: 'invalid payload' }, { status: 400 });
  }
}

