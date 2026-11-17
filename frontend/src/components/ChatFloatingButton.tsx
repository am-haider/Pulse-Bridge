"use client";

import { useState } from "react";
import { Stethoscope } from "lucide-react";
import ChatModal from "./ChatModal";

export default function ChatFloatingButton() {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="fixed bottom-6 right-6 z-50 flex h-14 w-14 items-center justify-center rounded-full bg-[#0f172a] text-[#f8f4ec] shadow-xl shadow-slate-900/20 transition hover:scale-105 hover:bg-[#111827] focus:outline-none focus:ring-2 focus:ring-[#0f172a]/20"
        aria-label="Open doctor assistant chat"
      >
        <Stethoscope size={24} className="stroke-2" />
      </button>

      {open && <ChatModal onClose={() => setOpen(false)} />}
    </>
  );
}
