'use client';

import { Inter } from 'next/font/google';

const inter = Inter({ subsets: ['latin'] });

interface DynamicBodyProps {
  children: React.ReactNode;
}

export default function DynamicBody({ children }: DynamicBodyProps) {
  return (
    <body className={inter.className}>
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
        {children}
      </div>
    </body>
  );
}
