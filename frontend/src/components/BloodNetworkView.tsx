'use client';

import React, { useState } from 'react';
import { Heart, Search, MapPin, Phone, MessageSquare, AlertCircle, ShieldCheck, UserPlus, CheckCircle2, Loader2, Clock, Calendar } from 'lucide-react';
import { matchBloodDonors, registerDonor } from '@/lib/api';
import { MatchedDonor, BloodMatchResponse } from '@/types';
import { motion, AnimatePresence } from 'framer-motion';

const BLOOD_GROUPS = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'];

export default function BloodNetworkView() {
  const [subTab, setSubTab] = useState<'match' | 'register'>('match');

  // Matching state
  const [recipientGroup, setRecipientGroup] = useState('B+');
  const [city, setCity] = useState('Lahore');
  const [area, setArea] = useState('Gulberg');
  const [urgency, setUrgency] = useState('Emergency');
  const [onlyAvailable, setOnlyAvailable] = useState(true);
  const [loading, setLoading] = useState(false);
  const [matches, setMatches] = useState<BloodMatchResponse | null>(null);
  const [revealedContacts, setRevealedContacts] = useState<Record<string, boolean>>({});
  const [error, setError] = useState<string | null>(null);

  // Donor Registration form state
  const [regForm, setRegForm] = useState({
    full_name: '',
    age: 26,
    gender: 'Male',
    blood_group: 'O-',
    city: 'Lahore',
    area: 'Gulberg',
    address: '',
    contact_number: '',
    availability: 'Available',
  });
  const [regSuccess, setRegSuccess] = useState<string | null>(null);

  // Animation variants
  const headerVariants = {
    hidden: { opacity: 0, y: 30 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: 'easeOut' } },
  };

  const cardVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: 'easeOut' } },
  };

  const containerVariants = {
    visible: {
      transition: {
        staggerChildren: 0.08,
        delayChildren: 0.2,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: 'easeOut' } },
  };

  const tabVariants = {
    hidden: { opacity: 0, x: -20 },
    visible: { opacity: 1, x: 0, transition: { duration: 0.4, ease: 'easeOut' } },
  };

  // Initial match search on mount
  React.useEffect(() => {
    handleSearch();
  }, []);

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await matchBloodDonors({
        recipient_blood_group: recipientGroup,
        city,
        area: area || undefined,
        urgency,
        only_available: onlyAvailable,
      });
      setMatches(res);
    } catch (err: any) {
      setError(err.message || 'Error occurred while searching blood donors.');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await registerDonor(regForm);
      setRegSuccess('You have successfully enrolled as an emergency voluntary donor. Thank you for saving lives!');
      setRegForm({
        full_name: '',
        age: 26,
        gender: 'Male',
        blood_group: 'O-',
        city: 'Lahore',
        area: 'Gulberg',
        address: '',
        contact_number: '',
        availability: 'Available',
      });
    } catch (err: any) {
      setError(err.message || 'Failed to register blood donor.');
    } finally {
      setLoading(false);
    }
  };

  const toggleRevealPhone = (code: string) => {
    setRevealedContacts((prev) => ({ ...prev, [code]: !prev[code] }));
  };

  return (
    <motion.div initial="hidden" animate="visible" variants={headerVariants} className="space-y-8 max-w-6xl mx-auto py-6">
      {/* Header Banner */}
      <motion.div
        variants={headerVariants}
        className="bg-gradient-to-r from-rose-950 via-slate-950 to-slate-900 rounded-3xl p-8 text-white shadow-xl relative overflow-hidden"
      >
        <div className="absolute right-0 top-0 bottom-0 w-1/3 bg-rose-500/10 rounded-full blur-3xl pointer-events-none" />
        <motion.div
          initial={{ opacity: 0, x: -30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="relative z-10 max-w-2xl"
        >
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-rose-500/20 border border-rose-400/30 text-rose-300 text-xs font-semibold mb-4">
            <Heart className="w-3.5 h-3.5 text-rose-400 fill-rose-400" /> Life-Saving Emergency Mobilization
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight sm:text-4xl">
            Smart Blood Donor Network
          </h1>
          <p className="mt-3 text-slate-300 text-sm sm:text-base leading-relaxed">
            Location-aware, blood group compatibility-guided donor matching. Connect directly with active voluntary
            Pakistani donors while safeguarding privacy through consent-based communication.
          </p>
        </motion.div>
      </motion.div>

      {/* Sub-navigation Tabs */}
      <motion.div
        variants={containerVariants}
        className="flex border-b border-slate-200"
      >
        <motion.button
          variants={tabVariants}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => { setSubTab('match'); setError(null); }}
          className={`pb-3 px-4 font-bold text-sm border-b-2 transition-all flex items-center gap-2 ${
            subTab === 'match'
              ? 'border-rose-600 text-rose-700'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Search className="w-4 h-4" /> Emergency Donor Matcher
        </motion.button>
        <motion.button
          variants={tabVariants}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => { setSubTab('register'); setError(null); }}
          className={`pb-3 px-4 font-bold text-sm border-b-2 transition-all flex items-center gap-2 ${
            subTab === 'register'
              ? 'border-rose-600 text-rose-700'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <UserPlus className="w-4 h-4" /> Register as a Donor
        </motion.button>
      </motion.div>

      {/* TAB 1: EMERGENCY DONOR MATCHER */}
      <AnimatePresence mode="wait">
        {subTab === 'match' && (
          <motion.div
            key="match"
            initial="hidden"
            animate="visible"
            exit="exit"
            variants={tabVariants}
            className="space-y-6"
          >
            <motion.div
              variants={cardVariants}
              className="bg-white rounded-2xl border border-slate-200/80 shadow-sm p-6"
            >
              <form onSubmit={handleSearch} className="space-y-4">
                <motion.div
                  variants={containerVariants}
                  className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4"
                >
                  {/* Recipient Blood Group */}
                  <motion.div variants={itemVariants}>
                    <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1.5">
                      Recipient Blood Group
                    </label>
                    <select
                      value={recipientGroup}
                      onChange={(e) => setRecipientGroup(e.target.value)}
                      className="w-full px-3 py-2.5 rounded-xl border border-slate-300 text-sm font-bold text-slate-900 focus:outline-none focus:border-rose-600 bg-white"
                    >
                      {BLOOD_GROUPS.map((bg) => (
                        <option key={bg} value={bg}>{bg}</option>
                      ))}
                    </select>
                  </motion.div>

                  {/* City */}
                  <motion.div variants={itemVariants}>
                    <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1.5">
                      City
                    </label>
                    <input
                      type="text"
                      value={city}
                      onChange={(e) => setCity(e.target.value)}
                      placeholder="e.g. Lahore, Karachi"
                      className="w-full px-3 py-2.5 rounded-xl border border-slate-300 text-sm font-semibold text-slate-900 focus:outline-none focus:border-rose-600"
                    />
                  </motion.div>

                  {/* Area */}
                  <motion.div variants={itemVariants}>
                    <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1.5">
                      Area / Sector (Optional)
                    </label>
                    <input
                      type="text"
                      value={area}
                      onChange={(e) => setArea(e.target.value)}
                      placeholder="e.g. Gulberg, Hayatabad"
                      className="w-full px-3 py-2.5 rounded-xl border border-slate-300 text-sm font-semibold text-slate-900 focus:outline-none focus:border-rose-600"
                    />
                  </motion.div>

                  {/* Urgency */}
                  <motion.div variants={itemVariants}>
                    <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1.5">
                      Urgency Priority
                    </label>
                    <select
                      value={urgency}
                      onChange={(e) => setUrgency(e.target.value)}
                      className="w-full px-3 py-2.5 rounded-xl border border-slate-300 text-sm font-bold text-rose-700 focus:outline-none focus:border-rose-600 bg-white"
                    >
                      <option value="Emergency">🚨 Emergency (Immediate)</option>
                      <option value="Urgent">⚠️ Urgent (Within 12 hrs)</option>
                      <option value="Standard">Standard (Scheduled)</option>
                    </select>
                  </motion.div>
                </motion.div>

                <motion.div
                  variants={itemVariants}
                  className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-3 border-t border-slate-100"
                >
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="only-avail"
                      checked={onlyAvailable}
                      onChange={(e) => setOnlyAvailable(e.target.checked)}
                      className="w-4 h-4 text-rose-600 rounded border-slate-300 focus:ring-rose-500"
                    />
                    <label htmlFor="only-avail" className="text-xs text-slate-600 font-medium cursor-pointer">
                      Show only currently available donors (exclude donors on 90-day cooldown)
                    </label>
                  </div>

                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    type="submit"
                    disabled={loading}
                    className="px-6 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs shadow-md shadow-rose-600/20 transition-all flex items-center justify-center gap-2 cursor-pointer"
                  >
                    {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Find Compatible Donors'}
                  </motion.button>
                </motion.div>
              </form>
            </motion.div>

            {/* Compatibility Information Card */}
            <AnimatePresence>
              {matches && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  className="p-4 rounded-2xl bg-slate-100 border border-slate-200 text-xs flex flex-wrap items-center justify-between gap-3"
                >
                  <div className="flex items-center gap-2 font-semibold text-slate-700">
                    <span>Safe Donors for <strong className="text-rose-700 text-sm">{matches.recipient_group}</strong>:</span>
                    <div className="flex gap-1.5">
                      {matches.compatible_donor_groups.map((g) => (
                        <span key={g} className="px-2 py-0.5 rounded-md bg-white border border-slate-300 font-extrabold text-slate-900">
                          {g}
                        </span>
                      ))}
                    </div>
                  </div>
                  <span className="font-bold text-slate-500">
                    {matches.total_matches} Verified Donors Available
                  </span>
                </motion.div>
              )}
            </AnimatePresence>

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

            {/* Matched Donors Grid */}
            <AnimatePresence>
              {matches && (
                <motion.div
                  key="donors-grid"
                  variants={containerVariants}
                  className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5"
                >
                  {matches.donors.map((donor) => {
                    const isRevealed = revealedContacts[donor.donor_code];
                    return (
                      <motion.div
                        key={donor.donor_code}
                        variants={itemVariants}
                        whileHover={{ y: -4, boxShadow: '0 20px 40px rgba(220,38,38,0.1)', borderColor: '#dc2626' }}
                        className="bg-white rounded-2xl border border-slate-200 p-6 flex flex-col justify-between transition-all"
                      >
                        <div>
                          {/* Top Bar: Blood Group & Proximity */}
                          <div className="flex items-start justify-between gap-2 mb-3">
                            <div className="flex items-center gap-2">
                              <span className="w-10 h-10 rounded-xl bg-rose-50 text-rose-700 border border-rose-200 font-black text-base flex items-center justify-center">
                                {donor.blood_group}
                              </span>
                              <div>
                                <span className="text-[10px] font-bold text-slate-400 block uppercase">Code</span>
                                <span className="text-xs font-extrabold text-slate-800">{donor.donor_code}</span>
                              </div>
                            </div>

                            <span
                              className={`text-[10px] font-extrabold px-2.5 py-1 rounded-full uppercase tracking-wider ${
                                donor.distance_rank === 1
                                  ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                                  : donor.distance_rank === 2
                                  ? 'bg-teal-50 text-teal-800 border border-teal-200'
                                  : 'bg-slate-100 text-slate-600'
                              }`}
                            >
                              {donor.distance_rank === 1 ? '📍 Exact Area' : donor.distance_rank === 2 ? 'Same City' : 'Regional'}
                            </span>
                          </div>

                          {/* Donor Name & Compatibility Reason */}
                          <h3 className="font-extrabold text-base text-slate-900">
                            {donor.full_name}
                          </h3>
                          <p className="text-[11px] text-teal-700 font-semibold mt-0.5">
                            {donor.compatibility_reason}
                          </p>

                          {/* Address & Availability */}
                          <div className="mt-3 space-y-1 text-xs text-slate-600">
                            <div className="flex items-center gap-1.5 font-medium">
                              <MapPin className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                              <span className="truncate">{donor.full_address}</span>
                            </div>
                            <div className="flex items-center gap-1.5 font-medium text-[11px] text-slate-500">
                              <Calendar className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                              <span>Last donation: {donor.last_donation_date || 'None on record'}</span>
                            </div>
                          </div>
                        </div>

                        {/* Contact & WhatsApp Action */}
                        <div className="mt-5 pt-4 border-t border-slate-100 space-y-2">
                          <div className="flex items-center justify-between text-xs font-semibold">
                            <span className="text-slate-500">Phone:</span>
                            <div className="flex items-center gap-2">
                              <span className="font-mono text-slate-900">
                                {isRevealed && donor.raw_contact ? donor.raw_contact : donor.masked_contact}
                              </span>
                              {!isRevealed && (
                                <motion.button
                                  whileHover={{ scale: 1.05 }}
                                  whileTap={{ scale: 0.95 }}
                                  onClick={() => toggleRevealPhone(donor.donor_code)}
                                  className="text-[10px] text-rose-600 hover:text-rose-700 font-bold underline cursor-pointer"
                                >
                                  Show
                                </motion.button>
                              )}
                            </div>
                          </div>

                          <a
                            href={donor.whatsapp_link}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="w-full py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs flex items-center justify-center gap-2 transition-colors cursor-pointer shadow-xs"
                          >
                            <MessageSquare className="w-4 h-4 fill-white" /> Emergency WhatsApp Connect
                          </a>
                        </div>
                      </motion.div>
                    );
                  })}
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        )}
      </AnimatePresence>

      {/* TAB 2: REGISTER AS A DONOR */}
      <AnimatePresence mode="wait">
        {subTab === 'register' && (
          <motion.div
            key="register"
            initial="hidden"
            animate="visible"
            exit="exit"
            variants={tabVariants}
            className="space-y-6"
          >
            <motion.div
              variants={cardVariants}
              className="bg-white rounded-2xl border border-slate-200/80 shadow-sm p-6 sm:p-8 max-w-2xl mx-auto"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
                <div>
                  <h2 className="text-xl font-extrabold text-slate-900">Volunteer as a Blood Donor</h2>
                  <p className="text-xs text-slate-500 mt-1">
                    Join the Pulse Bridge emergency registry. Your phone number is masked to protect against scrapers.
                  </p>
                </div>
                <Heart className="w-10 h-10 text-rose-500 fill-rose-500/20" />
              </div>

              <AnimatePresence>
                {regSuccess && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    className="mb-6 p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold flex items-center gap-2"
                  >
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                    {regSuccess}
                  </motion.div>
                )}
              </AnimatePresence>

              <motion.form
                onSubmit={handleRegister}
                variants={containerVariants}
                className="space-y-4"
              >
                <motion.div
                  variants={itemVariants}
                  className="grid grid-cols-1 sm:grid-cols-2 gap-4"
                >
                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">Full Name</label>
                    <input
                      type="text"
                      required
                      value={regForm.full_name}
                      onChange={(e) => setRegForm({ ...regForm, full_name: e.target.value })}
                      placeholder="e.g. Usman Tariq"
                      className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs font-medium focus:border-rose-600"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">Blood Group</label>
                    <select
                      value={regForm.blood_group}
                      onChange={(e) => setRegForm({ ...regForm, blood_group: e.target.value })}
                      className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs font-bold focus:border-rose-600 bg-white"
                    >
                      {BLOOD_GROUPS.map((bg) => (
                        <option key={bg} value={bg}>{bg}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">Age (18-65)</label>
                    <input
                      type="number"
                      min="18"
                      max="65"
                      required
                      value={regForm.age}
                      onChange={(e) => setRegForm({ ...regForm, age: Number(e.target.value) })}
                      className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs font-medium focus:border-rose-600"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">Gender</label>
                    <select
                      value={regForm.gender}
                      onChange={(e) => setRegForm({ ...regForm, gender: e.target.value })}
                      className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs font-medium focus:border-rose-600 bg-white"
                    >
                      <option value="Male">Male</option>
                      <option value="Female">Female</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">City</label>
                    <input
                      type="text"
                      required
                      value={regForm.city}
                      onChange={(e) => setRegForm({ ...regForm, city: e.target.value })}
                      placeholder="e.g. Lahore"
                      className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs font-medium focus:border-rose-600"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">Area / Neighborhood</label>
                    <input
                      type="text"
                      required
                      value={regForm.area}
                      onChange={(e) => setRegForm({ ...regForm, area: e.target.value })}
                      placeholder="e.g. Gulberg III"
                      className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs font-medium focus:border-rose-600"
                    />
                  </div>
                </motion.div>

                <motion.div variants={itemVariants}>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Full Street Address</label>
                  <input
                    type="text"
                    required
                    value={regForm.address}
                    onChange={(e) => setRegForm({ ...regForm, address: e.target.value })}
                    placeholder="House #, Street #, Sector..."
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs font-medium focus:border-rose-600"
                  />
                </motion.div>

                <motion.div variants={itemVariants}>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Mobile / WhatsApp Number</label>
                  <input
                    type="text"
                    required
                    value={regForm.contact_number}
                    onChange={(e) => setRegForm({ ...regForm, contact_number: e.target.value })}
                    placeholder="03001234567"
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 text-xs font-medium focus:border-rose-600 font-mono"
                  />
                </motion.div>

                <motion.div variants={itemVariants}>
                  <motion.button
                    whileHover={{ scale: 1.01 }}
                    whileTap={{ scale: 0.99 }}
                    type="submit"
                    disabled={loading}
                    className="w-full py-3 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-bold text-sm shadow-md transition-all cursor-pointer"
                  >
                    {loading ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : 'Enroll in Donor Registry'}
                  </motion.button>
                </motion.div>
              </motion.form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
