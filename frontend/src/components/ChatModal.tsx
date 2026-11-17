"use client";

import { FormEvent, useRef, useState } from "react";
import { Loader2, Send, Stethoscope, X } from "lucide-react";
import { chatWithDoctor } from "@/lib/api";
import { motion, AnimatePresence } from "framer-motion";

type Message = {
  sender: "user" | "bot";
  text: string;
};

type ChatModalProps = {
  onClose: () => void;
};

const modalVariants = {
  hidden: { opacity: 0, y: 30, scale: 0.95 },
  visible: { opacity: 1, y: 0, scale: 1, transition: { duration: 0.3, ease: 'easeOut' } },
  exit: { opacity: 0, y: 20, scale: 0.95, transition: { duration: 0.2, ease: 'easeIn' } },
};

const messageVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.3, ease: 'easeOut' } },
};

const inputVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.3, delay: 0.1, ease: 'easeOut' } },
};

const itemVariants = {
  hidden: { opacity: 0, y: 10 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.2, ease: 'easeOut' } },
};

export default function ChatModal({ onClose }: ChatModalProps) {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<Message[]>([
    {
      sender: "bot",
      text: "Hello. I can help explain lab reports, guide you to a doctor, or support urgent blood needs.",
    },
  ]);
  const [isSending, setIsSending] = useState(false);
  const requestInFlight = useRef(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    const trimmed = message.trim();

    if (!trimmed || requestInFlight.current) {
      return;
    }

    requestInFlight.current = true;
    setIsSending(true);
    setMessages((current) => [...current, { sender: "user", text: trimmed }]);
    setMessage("");

    try {
      const data = await chatWithDoctor(trimmed);
      setMessages((current) => [...current, { sender: "bot", text: data.reply }]);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "The request failed unexpectedly.";
      setMessages((current) => [...current, { sender: "bot", text: errorMessage }]);
    } finally {
      requestInFlight.current = false;
      setIsSending(false);
    }
  };

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      exit="exit"
      variants={modalVariants}
      className="fixed inset-0 z-50 flex items-end justify-end bg-slate-900/30 p-4 backdrop-blur-sm"
    >
      <motion.div
        className="w-full max-w-md overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-2xl"
      >
        <motion.div
          variants={inputVariants}
          className="flex items-center justify-between bg-[#0f172a] px-4 py-3 text-white"
        >
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#c9a86a] text-[#0f172a]">
              <Stethoscope className="h-4 w-4" />
            </div>
            <div>
              <p className="text-sm font-bold">Doctor Assistant</p>
              <p className="text-[10px] text-slate-300">Available</p>
            </div>
          </div>
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            type="button"
            onClick={onClose}
            className="rounded-full p-1.5 text-slate-300 transition hover:bg-white/10 hover:text-white"
            aria-label="Close chat"
          >
            <X className="h-4 w-4" />
          </motion.button>
        </motion.div>

        <motion.div
          variants={inputVariants}
          className="max-h-96 space-y-3 overflow-y-auto bg-[#f8f4ec] p-4"
        >
          <AnimatePresence>
            {messages.map((entry, index) => (
              <motion.div
                key={`${entry.sender}-${index}`}
                initial="hidden"
                animate="visible"
                exit="exit"
                variants={messageVariants}
                className={`max-w-[85%] rounded-2xl px-3 py-2 text-sm leading-relaxed ${
                  entry.sender === "user"
                    ? "ml-auto bg-[#0f172a] text-white"
                    : "bg-white text-slate-700 shadow-sm ring-1 ring-slate-200"
                }`}
              >
                {entry.text}
              </motion.div>
            ))}
          </AnimatePresence>
          {isSending && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="flex items-center gap-2 rounded-2xl bg-white px-3 py-2 text-sm text-slate-600 shadow-sm ring-1 ring-slate-200"
            >
              <Loader2 className="h-4 w-4 animate-spin text-[#0f766e]" />
              Waiting for a response...
            </motion.div>
          )}
        </motion.div>

        <motion.form
          onSubmit={handleSubmit}
          variants={inputVariants}
          className="flex items-center gap-2 border-t border-slate-200 bg-white p-3"
        >
          <motion.div
            variants={itemVariants}
            style={{ flex: 1 }}
          >
            <input
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              placeholder="Ask about a report or doctor..."
              maxLength={4000}
              disabled={isSending}
              className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-800 placeholder:text-slate-400 focus:border-[#0f766e] focus:outline-none focus:ring-2 focus:ring-[#0f766e]/10"
              aria-label="Message"
            />
          </motion.div>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            type="submit"
            className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-[#0f766e] text-white transition hover:bg-[#0a5a56] disabled:cursor-not-allowed disabled:bg-slate-300"
            aria-label="Send message"
            disabled={!message.trim() || isSending}
          >
            <Send className="h-4 w-4" />
          </motion.button>
        </motion.form>
      </motion.div>
    </motion.div>
  );
}
