import type { Metadata } from "next";
import "./globals.css";
import ChatFloatingButton from "../components/ChatFloatingButton";

export const metadata: Metadata = {
  title: "PULSE BRIDGE — AI Healthcare Accessibility Platform",
  description: "AI Medical Report Explainer, Verified Doctor Discovery (RAG), and Emergency Blood Donor Network for Pakistan. Aligned with UN SDG 03.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <head>
        <link
          rel="preconnect"
          href="https://fonts.googleapis.com"
        />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Manrope:wght@300;400;500;600;700;800&family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Noto+Nastaliq+Urdu:wght@400;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-full flex flex-col bg-slate-50 text-slate-900 font-sans">
        {children}
        <ChatFloatingButton />
      </body>
    </html>
  );
}
