'use client';

import Image from 'next/image';
import { Droplets, FileText, House, Info, Stethoscope } from 'lucide-react';
import { motion } from 'framer-motion';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  language: 'en' | 'ur';
  setLanguage: (lang: 'en' | 'ur') => void;
  isScrolled: boolean;
}

const navItems = [
  { key: 'home', label: 'Home', icon: House },
  { key: 'reports', label: 'Reports', icon: FileText },
  { key: 'doctors', label: 'Doctors', icon: Stethoscope },
  { key: 'blood', label: 'Blood support', icon: Droplets },
  { key: 'about', label: 'About', icon: Info },
];

export default function Navbar({ activeTab, setActiveTab, language, setLanguage, isScrolled }: NavbarProps) {
  return (
    <header className="sticky top-0 z-50 px-3 pt-3 text-[#183f5b] sm:px-5">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: 'easeOut' }}
        className={`mx-auto max-w-[1500px] overflow-hidden rounded-[1.75rem] px-4 transition-all duration-300 ease-out ${
          isScrolled
            ? 'bg-white/95 backdrop-blur-2xl border-b border-[#dce5e4] shadow-[0_8px_32px_rgba(20,54,76,0.12)]'
            : 'bg-transparent border-transparent shadow-none'
        } sm:px-6 lg:px-8`}
      >
        <div className="flex min-h-[72px] items-center justify-between gap-3">
          <button
            type="button"
            onClick={() => setActiveTab('home')}
            className="flex shrink-0 items-center rounded-xl focus:outline-none focus:ring-2 focus:ring-[#d4f36b]"
            aria-label="Pulse Bridge home"
          >
            <Image
              src="/images/pulse-bridge-logo.png"
              alt="Pulse Bridge"
              width={425}
              height={185}
              priority
              className="h-[50px] w-auto object-contain sm:h-[58px]"
            />
          </button>

          <motion.nav
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.4, delay: 0.1 }}
            aria-label="Main navigation"
            className="hidden items-center gap-1 md:flex"
          >
            {navItems.map(({ key, label, icon: Icon }) => (
              <motion.button
                key={key}
                type="button"
                onClick={() => setActiveTab(key)}
                aria-current={activeTab === key ? 'page' : undefined}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className={`inline-flex items-center gap-2 rounded-full px-3 py-2 text-xs font-semibold transition lg:px-3.5 ${
                  activeTab === key
                    ? 'bg-[#d4f36b] text-[#183f5b] shadow-md'
                    : 'text-[#183f5b]/80 hover:bg-slate-900/5 hover:text-[#183f5b]'
                }`}
              >
                <Icon className="h-4 w-4" />
                {label}
              </motion.button>
            ))}
          </motion.nav>

          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.4, delay: 0.2 }}
            className="flex shrink-0 items-center gap-2"
          >
            <div className="flex items-center gap-0.5 rounded-full border border-[#183f5b]/10 bg-white/50 p-1 backdrop-blur-sm">
              <button
                type="button"
                onClick={() => setLanguage('en')}
                aria-pressed={language === 'en'}
                className={`rounded-full px-2.5 py-1.5 text-[10px] font-bold transition ${
                  language === 'en' ? 'bg-[#183f5b] text-white' : 'text-[#183f5b]/75 hover:text-[#183f5b]'
                }`}
              >
                EN
              </button>
              <button
                type="button"
                onClick={() => setLanguage('ur')}
                aria-pressed={language === 'ur'}
                className={`rounded-full px-2.5 py-1.5 text-xs font-bold transition ${
                  language === 'ur' ? 'bg-[#d4f36b] text-[#183f5b]' : 'text-[#183f5b]/75 hover:text-[#183f5b]'
                }`}
              >
                اردو
              </button>
            </div>
          </motion.div>
        </div>

        <motion.nav
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.3 }}
          aria-label="Mobile navigation"
          className="-mx-4 flex gap-1 overflow-x-auto px-4 pb-2 md:hidden sm:-mx-6 sm:px-6 lg:-mx-8 lg:px-8"
        >
          {navItems.map(({ key, label, icon: Icon }) => (
            <motion.button
              key={key}
              type="button"
              onClick={() => setActiveTab(key)}
              aria-current={activeTab === key ? 'page' : undefined}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className={`inline-flex shrink-0 items-center gap-1.5 rounded-full px-3 py-2 text-[11px] font-semibold transition ${
                activeTab === key
                  ? 'bg-[#d4f36b] text-[#183f5b]'
                  : 'text-[#183f5b]/80 hover:bg-slate-900/5 hover:text-[#183f5b]'
              }`}
            >
              <Icon className="h-3.5 w-3.5" />
              {label}
            </motion.button>
          ))}
        </motion.nav>
      </motion.div>
    </header>
  );
}
