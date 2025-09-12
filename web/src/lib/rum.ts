export type WebVitalMetric = {
  name: string;
  value: number;
  id?: string;
  label?: string;
};

export async function sendWebVital(metric: WebVitalMetric) {
  try {
    const body = JSON.stringify({
      metric,
      url: typeof window !== 'undefined' ? window.location.href : '',
      ts: Date.now(),
      ua: typeof navigator !== 'undefined' ? navigator.userAgent : '',
    });

    if ('sendBeacon' in navigator) {
      navigator.sendBeacon('/api/rum', body);
      return;
    }

    await fetch('/api/rum', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body,
      keepalive: true,
    });
  } catch (_) {
    // swallow
  }
}

