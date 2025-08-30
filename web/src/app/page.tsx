export default function HomePage() {
  return (
    <main style={{ padding: 24, fontFamily: 'system-ui, sans-serif' }}>
      <h1>AttentionSync</h1>
      <p>Web UI is running.</p>
      <p>
        API: <code>{process.env.NEXT_PUBLIC_API_URL}</code>
      </p>
    </main>
  );
}

