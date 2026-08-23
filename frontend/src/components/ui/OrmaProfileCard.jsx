import React from 'react';
import { motion } from 'framer-motion';
import { User, ShieldCheck, Mail, Globe, KeyRound, Phone, Plus, Edit2 } from 'lucide-react';

export default function OrmaProfileCard({
  user,
  onEditProfile,
  onChangePassword,
  onEditPhone,
  className = ''
}) {
  const isCaregiver = user?.role === 'caregiver';
  const displayName = user?.name || (isCaregiver ? 'Caregiver' : 'Elderly Member');
  const displayEmail = user?.email || 'user@orma.ai';
  const roleLabel = isCaregiver ? 'Caregiver Account' : 'Parent / Elderly Account';
  const timezone = user?.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';
  const phone = user?.phone || '';

  return (
    <div className={`p-6 sm:p-8 rounded-3xl bg-slate-900/80 backdrop-blur-2xl border border-white/10 shadow-2xl relative overflow-hidden ${className}`}>
      {/* Ambient background glow */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />

      <div className="flex flex-col gap-6 relative z-10">
        {/* Top: Avatar & User Details */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-3xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white font-extrabold text-2xl shadow-xl border border-white/20 shrink-0">
              {displayName.charAt(0).toUpperCase()}
            </div>

            <div>
              <div className="flex items-center gap-2.5 flex-wrap">
                <h3 className="text-xl sm:text-2xl font-black text-white tracking-tight">
                  {displayName}
                </h3>
                <span className="px-3 py-1 rounded-full text-xs font-bold bg-blue-500/15 text-blue-400 border border-blue-500/25 inline-flex items-center gap-1.5">
                  <ShieldCheck className="w-3.5 h-3.5" />
                  {roleLabel}
                </span>
              </div>

              <div className="flex flex-wrap items-center gap-y-1 gap-x-4 mt-2 text-xs sm:text-sm text-slate-400">
                <div className="flex items-center gap-1.5">
                  <Mail className="w-3.5 h-3.5 text-slate-500" />
                  <span>{displayEmail}</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <Globe className="w-3.5 h-3.5 text-slate-500" />
                  <span>{timezone}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Top Actions */}
          <div className="flex items-center gap-3 w-full sm:w-auto">
            {onChangePassword && (
              <button
                type="button"
                onClick={onChangePassword}
                className="flex-1 sm:flex-none px-4 py-2.5 rounded-xl bg-slate-800/80 hover:bg-slate-800 text-slate-200 border border-white/10 hover:border-white/20 text-xs font-bold transition-colors inline-flex items-center justify-center gap-1.5 cursor-pointer min-h-[44px]"
              >
                <KeyRound className="w-4 h-4 text-blue-400" />
                <span>Change Password</span>
              </button>
            )}

            {onEditProfile && (
              <button
                type="button"
                onClick={onEditProfile}
                className="flex-1 sm:flex-none px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold transition-all shadow-md shadow-blue-600/20 inline-flex items-center justify-center gap-1.5 cursor-pointer min-h-[44px]"
              >
                <User className="w-4 h-4" />
                <span>Edit Info</span>
              </button>
            )}
          </div>
        </div>

        {/* Bottom: Emergency Contact Phone Section */}
        <div className="pt-5 border-t border-white/10 flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-950/40 p-4 rounded-2xl border border-white/5">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400 shrink-0">
              <Phone className="w-4 h-4" />
            </div>
            <div>
              <p className="text-xs font-bold uppercase tracking-wider text-slate-400">
                Emergency Contact Phone
              </p>
              <p className="text-sm font-bold text-white mt-0.5 font-mono">
                {phone ? (
                  <span className="text-cyan-300">{phone}</span>
                ) : (
                  <span className="text-slate-400 font-sans font-normal text-xs">No phone number added</span>
                )}
              </p>
            </div>
          </div>

          {onEditPhone && (
            <button
              type="button"
              onClick={onEditPhone}
              className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-blue-400 hover:text-blue-300 border border-white/10 text-xs font-bold transition-colors inline-flex items-center justify-center gap-1.5 cursor-pointer min-h-[44px]"
            >
              {phone ? (
                <>
                  <Edit2 className="w-3.5 h-3.5" />
                  <span>Edit Phone</span>
                </>
              ) : (
                <>
                  <Plus className="w-3.5 h-3.5" />
                  <span>Add Phone Number</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
