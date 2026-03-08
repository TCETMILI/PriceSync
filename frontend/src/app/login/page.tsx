'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/authStore';
import { motion } from 'framer-motion';
import { Lock, User, Activity } from 'lucide-react';

export default function LoginPage() {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const login = useAuthStore((state) => state.login);
    const router = useRouter();

    const handleLogin = (e: React.FormEvent) => {
        e.preventDefault();
        const success = login(username, password);
        if (success) {
            router.push('/');
        } else {
            setError('Hatalı kullanıcı adı veya şifre.');
        }
    };

    return (
        <div className="min-h-screen bg-slate-100 flex items-center justify-center p-4">
            <div className="max-w-md w-full">
                {/* Logo */}
                <div className="text-center mb-10 flex flex-col items-center">
                    <img src="/meridyen-logo.png" alt="Meridyen Logo" className="h-20 drop-shadow-md mb-6" />
                    <h1 className="text-4xl font-extrabold text-slate-900 tracking-tight mb-2">
                        Price<span className="text-[#0062ff]">Sync</span>
                    </h1>
                    <p className="text-slate-600 font-medium text-lg">Fiyatlandırma Senkronizasyonu Zekası</p>
                </div>

                {/* Form Container */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-white rounded-3xl p-8 border border-slate-200 shadow-xl shadow-slate-300/40"
                >
                    <h2 className="text-xl font-bold text-slate-800 mb-6">Operatör Girişi</h2>

                    <form onSubmit={handleLogin} className="space-y-5">
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-2">Kullanıcı Adı</label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                                    <User className="h-5 w-5 text-slate-400" />
                                </div>
                                <input
                                    type="text"
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    className="block w-full pl-11 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors text-slate-800 placeholder:text-slate-400 font-medium"
                                    placeholder="Admin"
                                    required
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-2">Şifre</label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                                    <Lock className="h-5 w-5 text-slate-400" />
                                </div>
                                <input
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="block w-full pl-11 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors text-slate-800 placeholder:text-slate-400 font-medium tracking-widest"
                                    placeholder="••••••••"
                                    required
                                />
                            </div>
                        </div>

                        {error && (
                            <motion.p
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                className="text-red-500 text-sm font-medium"
                            >
                                {error}
                            </motion.p>
                        )}

                        <button
                            type="submit"
                            className="w-full bg-[#001b3a] hover:bg-[#002855] text-white font-semibold py-3.5 px-4 rounded-xl transition-colors shadow-lg shadow-[#001b3a]/20 mt-4"
                        >
                            Sisteme Giriş Yap
                        </button>
                    </form>
                </motion.div>

                <p className="text-center text-slate-500 font-medium text-sm mt-8">
                    © 2025 Meridyen AI. Tüm Hakları Saklıdır.
                </p>
            </div>
        </div >
    );
}
