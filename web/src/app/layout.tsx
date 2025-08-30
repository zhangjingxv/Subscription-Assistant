export const metadata = {
  title: 'AttentionSync',
  description: 'Intelligent information aggregation platform',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

