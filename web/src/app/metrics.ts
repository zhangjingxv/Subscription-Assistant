import { sendWebVital } from '@/lib/rum';

export function reportWebVitals(metric: any) {
  sendWebVital({ name: metric.name, value: metric.value, id: metric.id, label: metric.label });
}

