'use client';

import React, { useState, useEffect } from 'react';
import { Search, MapPin, Stethoscope, Star, Clock, ExternalLink, ShieldCheck, Filter, ArrowRight, Loader2, DollarSign } from 'lucide-react';
import { searchDoctors, getDoctorFilterMeta } from '@/lib/api';
import { VerifiedDoctor, DoctorSearchResponse, DoctorFilterMetaResponse } from '@/types';
import { AnimatePresence, motion, type Variants } from 'framer-motion';

export default function DoctorFinderView() {
  const [query, setQuery] = useState('Pediatrician in Lahore under 2000 rupees');
  const [city, setCity] = useState('');
  const [specialization, setSpecialization] = useState('');
  const [maxFee, setMaxFee] = useState<number>(3000);
  const [minExperience, setMinExperience] = useState<number>(5);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<DoctorSearchResponse | null>(null);
  const [meta, setMeta] = useState<DoctorFilterMetaResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Load 117 cities and specializations for dropdowns
    getDoctorFilterMeta()
      .then(data => setMeta(data))
      .catch(err => console.log('Meta filter notice:', err));

    // Initial search
    handleSearch();
  }, []);

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const res = await searchDoctors({
        query: query || 'Top doctors in Pakistan',
        city: city || undefined,
        specialization: specialization || undefined,
        max_fee: maxFee || undefined,
        min_experience_years: minExperience || undefined,
        limit: 9,
      });
      setResults(res);
    } catch (err: any) {
      setError(err.message || 'Error occurred while searching verified doctors.');
    } finally {
      setLoading(false);
    }
  };

  const setPresetSearch = (q: string, c: string, s: string, fee: number) => {
    setQuery(q);
    setCity(c);
    setSpecialization(s);
    setMaxFee(fee);
    setLoading(true);
    searchDoctors({
      query: q,
      city: c || undefined,
      specialization: s || undefined,
      max_fee: fee,
      limit: 9,
    })
      .then(res => setResults(res))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  };

  const headerVariants: Variants = {
    hidden: { opacity: 0, y: 30 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: 'easeOut' } },
  };

  const cardVariants: Variants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: 'easeOut' } },
  };

  const resultVariants: Variants = {
    hidden: { opacity: 0, y: 30 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: 'easeOut' } },
  };

  const containerVariants: Variants = {
    visible: {
      transition: {
        staggerChildren: 0.08,
        delayChildren: 0.2,
      },
    },
  };

  const itemVariants: Variants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: 'easeOut' } },
  };

  return (
    <motion.div initial="hidden" animate="visible" variants={headerVariants} className="space-y-8 max-w-6xl mx-auto py-6">
      {/* Header Banner */}
      <motion.div
        variants={headerVariants}
        className="bg-gradient-to-r from-slate-950 via-teal-950 to-slate-900 rounded-3xl p-8 text-white shadow-xl relative overflow-hidden"
      >
        <div className="absolute right-0 top-0 bottom-0 w-1/3 bg-teal-400/10 rounded-full blur-3xl pointer-events-none" />
        <motion.div
          initial={{ opacity: 0, x: -30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="relative z-10 max-w-2xl"
        >
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-500/20 border border-teal-400/30 text-teal-300 text-xs font-semibold mb-4">
            <ShieldCheck className="w-3.5 h-3.5 text-teal-400" /> Find a doctor
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight sm:text-4xl">
            Verified Doctor Discovery
          </h1>
          <p className="mt-3 text-slate-300 text-sm sm:text-base leading-relaxed">
            Browse doctor listings by medical need, location, consultation fee, and experience.
            Review profile details and contact information before choosing a provider.
          </p>
        </motion.div>
      </motion.div>

      {/* Search & Filter Bar */}
      <motion.div
        variants={cardVariants}
        className="bg-white rounded-2xl border border-slate-200/80 shadow-sm p-6"
      >
        <form onSubmit={handleSearch} className="space-y-4">
          {/* Natural Language Search Input */}
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Describe your medical need (e.g., 'Skin doctor in Quetta under 3500 rupees', 'Heart surgeon in Lahore')..."
              className="w-full pl-12 pr-32 py-3.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-600 text-sm font-medium text-slate-900 placeholder:text-slate-400"
            />
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              type="submit"
              disabled={loading}
              className="absolute right-2 top-1/2 -translate-y-1/2 px-5 py-2 rounded-lg bg-teal-600 hover:bg-teal-700 text-white font-bold text-xs shadow-sm transition-all flex items-center gap-1.5 cursor-pointer"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Search'}
            </motion.button>
          </div>

          {/* Structured Filter Row */}
          <motion.div
            variants={containerVariants}
            className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 pt-2"
          >
            {/* City Dropdown */}
            <motion.div variants={itemVariants}>
              <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1">
                City Filter
              </label>
              <select
                value={city}
                onChange={(e) => setCity(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs font-semibold text-slate-700 focus:outline-none focus:border-teal-600 bg-white"
              >
                <option value="">All Cities (117 Total)</option>
                {meta?.cities?.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </motion.div>

            {/* Specialization Dropdown */}
            <motion.div variants={itemVariants}>
              <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1">
                Specialty
              </label>
              <select
                value={specialization}
                onChange={(e) => setSpecialization(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs font-semibold text-slate-700 focus:outline-none focus:border-teal-600 bg-white"
              >
                <option value="">All Specialties</option>
                {meta?.specializations?.slice(0, 40).map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </motion.div>

            {/* Max Fee Slider */}
            <motion.div variants={itemVariants}>
              <div className="flex justify-between items-center mb-1">
                <label className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
                  Max Fee
                </label>
                <span className="text-xs font-extrabold text-teal-700">{maxFee} PKR</span>
              </div>
              <input
                type="range"
                min="0"
                max="10000"
                step="500"
                value={maxFee}
                onChange={(e) => setMaxFee(Number(e.target.value))}
                className="w-full accent-teal-600 cursor-pointer"
              />
            </motion.div>

            {/* Min Experience */}
            <motion.div variants={itemVariants}>
              <div className="flex justify-between items-center mb-1">
                <label className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
                  Min Experience
                </label>
                <span className="text-xs font-extrabold text-teal-700">{minExperience}+ Yrs</span>
              </div>
              <input
                type="range"
                min="1"
                max="40"
                value={minExperience}
                onChange={(e) => setMinExperience(Number(e.target.value))}
                className="w-full accent-teal-600 cursor-pointer"
              />
            </motion.div>
          </motion.div>

          {/* Quick Filter Presets */}
          <motion.div
            variants={containerVariants}
            className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-100"
          >
            <span className="text-xs font-semibold text-slate-400">Quick Searches:</span>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              type="button"
              onClick={() => setPresetSearch('Pediatrician in Lahore', 'Lahore', 'Pediatrician', 2500)}
              variants={itemVariants}
              className="text-xs px-2.5 py-1 rounded-md bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium"
            >
              👶 Child Specialist (Lahore)
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              type="button"
              onClick={() => setPresetSearch('Dermatologist in Quetta', 'Quetta', 'Dermatologist', 3000)}
              variants={itemVariants}
              className="text-xs px-2.5 py-1 rounded-md bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium"
            >
              🩺 Skin Specialist (Quetta)
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              type="button"
              onClick={() => setPresetSearch('General Physician in Islamabad', 'Islamabad', 'General Physician', 1500)}
              variants={itemVariants}
              className="text-xs px-2.5 py-1 rounded-md bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium"
            >
              💊 General Physician (Islamabad)
            </motion.button>
          </motion.div>
        </form>
      </motion.div>

      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-semibold"
          >
            {error}
          </motion.div>
        )}
      </AnimatePresence>

      {/* RAG Grounded Summary */}
      <AnimatePresence>
        {results && (
          <motion.div
            key="results"
            initial="hidden"
            animate="visible"
            exit="exit"
            variants={resultVariants}
            className="space-y-6"
          >
            <motion.div
              variants={itemVariants}
              className="p-4 rounded-2xl bg-teal-50 border border-teal-200 text-teal-900 text-xs sm:text-sm font-medium flex items-start gap-3 shadow-xs"
            >
              <ShieldCheck className="w-5 h-5 text-teal-600 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold">GROUNDED RECOMMENDATION: </span>
                {results.grounded_summary}
              </div>
            </motion.div>

            {/* Doctor Cards Grid */}
            <motion.div
              variants={containerVariants}
              className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5"
            >
              {results.doctors.map((doc) => (
                <motion.div
                  key={doc.id}
                  variants={itemVariants}
                  whileHover={{ y: -4, boxShadow: '0 20px 40px rgba(28,64,78,0.1)', borderColor: '#416f90' }}
                  className="bg-white rounded-2xl border border-slate-200 p-6 flex flex-col justify-between transition-all group"
                >
                  <div>
                    {/* Top Bar: Specialty & Verified Tag */}
                    <div className="flex items-start justify-between gap-2 mb-3">
                      <span className="text-xs font-bold px-2.5 py-1 rounded-lg bg-teal-50 text-teal-700 border border-teal-200">
                        {doc.specialization_primary}
                      </span>
                      <span className="inline-flex items-center gap-1 text-[10px] font-extrabold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                        <ShieldCheck className="w-3 h-3" /> Verified
                      </span>
                    </div>

                    {/* Doctor Name and Credentials */}
                    <h3 className="font-extrabold text-base text-slate-900 group-hover:text-teal-700 transition-colors">
                      {doc.doctor_name}
                    </h3>
                    <p className="text-xs text-slate-500 font-medium mt-0.5 line-clamp-1">
                      {doc.qualifications}
                    </p>

                    {/* Location & Hospital */}
                    <div className="mt-3 space-y-1.5 text-xs text-slate-600">
                      <div className="flex items-center gap-1.5 font-semibold text-slate-800">
                        <MapPin className="w-3.5 h-3.5 text-teal-600 shrink-0" />
                        <span>{doc.city}</span>
                        {doc.hospital_name && (
                          <>
                            <span className="text-slate-300">•</span>
                            <span className="truncate">{doc.hospital_name}</span>
                          </>
                        )}
                      </div>
                      {doc.hospital_address && (
                        <p className="text-[11px] text-slate-400 pl-5 line-clamp-1">
                          {doc.hospital_address}
                        </p>
                      )}
                    </div>

                    {/* Stats Row */}
                    <div className="mt-4 pt-3 border-t border-slate-100 grid grid-cols-3 gap-2 text-center">
                      <div className="p-2 rounded-lg bg-slate-50">
                        <span className="block text-[10px] font-bold text-slate-400 uppercase">Exp</span>
                        <span className="text-xs font-extrabold text-slate-800">{doc.experience_years.toFixed(0)} Yrs</span>
                      </div>
                      <div className="p-2 rounded-lg bg-slate-50">
                        <span className="block text-[10px] font-bold text-slate-400 uppercase">Rating</span>
                        <span className="text-xs font-extrabold text-amber-600 flex items-center justify-center gap-0.5">
                          <Star className="w-3 h-3 fill-amber-500 text-amber-500" />
                          {doc.patient_satisfaction_pct.toFixed(0)}%
                        </span>
                      </div>
                      <div className="p-2 rounded-lg bg-slate-50">
                        <span className="block text-[10px] font-bold text-slate-400 uppercase">Reviews</span>
                        <span className="text-xs font-extrabold text-slate-800">{doc.total_reviews}</span>
                      </div>
                    </div>
                  </div>

                  {/* Bottom Fee & External Profile Link */}
                  <div className="mt-5 pt-4 border-t border-slate-100 flex items-center justify-between">
                    <div>
                      <span className="block text-[10px] font-bold text-slate-400 uppercase">Consultation Fee</span>
                      <span className="text-base font-extrabold text-teal-700">
                        {doc.fee_pkr === 0 ? 'Free / Welfare' : `${doc.fee_pkr.toLocaleString()} PKR`}
                      </span>
                    </div>

                    {doc.profile_url ? (
                      <a
                        href={doc.profile_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-teal-600 hover:text-white text-slate-700 font-bold text-xs transition-colors"
                      >
                        Marham Profile <ExternalLink className="w-3 h-3" />
                      </a>
                    ) : (
                      <span className="text-[11px] font-medium text-slate-400 italic">
                        Profile link unlisted
                      </span>
                    )}
                  </div>
                </motion.div>
              ))}
            </motion.div>

            <AnimatePresence>
              {results.doctors.length === 0 && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  className="text-center py-12 bg-white rounded-2xl border border-slate-200 p-8"
                >
                  <Stethoscope className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                  <h3 className="text-base font-bold text-slate-800">No verified doctors found</h3>
                  <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">
                    No practitioners in our dataset matched this exact combination. Try broadening your fee limit or switching to a nearby city.
                  </p>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
