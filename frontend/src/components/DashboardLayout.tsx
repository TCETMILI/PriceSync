'use client';

import { ReactNode, useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuthStore } from '@/store/authStore';
import Link from 'next/link';
import { Activity, LayoutDashboard, RefreshCcw, CheckSquare, LogOut, Loader2 } from 'lucide-react';

export default function DashboardLayout({ children }: { children: ReactNode }) {
    const [isMounted, setIsMounted] = useState(false);
    const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
    const logout = useAuthStore((state) => state.logout);
    const router = useRouter();
    const pathname = usePathname();

    useEffect(() => {
        setIsMounted(true);
    }, []);

    useEffect(() => {
        if (isMounted) {
            // İstemci tarafında auth kontrolü
            if (!isAuthenticated) {
                router.push('/login');
            }
        }
    }, [isMounted, isAuthenticated, router]);

    // Hydration öncesi gizle
    if (!isMounted || !isAuthenticated) {
        return (
            <div className="h-screen w-full flex flex-col justify-center items-center bg-slate-50">
                <div className="p-4 bg-emerald-100/50 rounded-full mb-4 animate-pulse">
                    <Loader2 className="w-8 h-8 text-emerald-600 animate-spin" />
                </div>
                <p className="text-slate-500 font-medium">Sistem Yükleniyor...</p>
            </div>
        );
    }

    const handleLogout = () => {
        logout();
        router.push('/login');
    };

    const menuItems = [
        { name: 'Panel (PriceSync)', path: '/', icon: LayoutDashboard },
        { name: 'Fiyat Güncelle (PriceSync Engine)', path: '/sync', icon: RefreshCcw },
    ];

    return (
        <div className="flex h-screen bg-slate-50">
            {/* Sidebar */}
            <aside className="w-72 bg-[#001b3a] text-slate-200 flex flex-col transition-all shadow-xl z-20">
                {/* Logo Alanı */}
                <div className="h-32 flex items-center justify-center px-6 border-b border-white/10">
                    <img src="/meridyen-logo.png" alt="Meridyen Logo" className="h-20 drop-shadow-sm" />
                </div>

                {/* Menü */}
                <nav className="flex-1 px-4 py-8 space-y-2">
                    <div className="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-6 px-3">
                        Operasyonlar
                    </div>

                    {menuItems.map((item) => {
                        const isActive = pathname === item.path;
                        const Icon = item.icon;
                        return (
                            <Link
                                key={item.path}
                                href={item.path}
                                className={`flex items-center gap-3 px-3 py-3 rounded-xl transition-all ${isActive
                                    ? 'bg-emerald-500/10 text-emerald-400 font-medium'
                                    : 'hover:bg-white/5 hover:text-white'
                                    }`}
                            >
                                <Icon className="w-5 h-5" />
                                {item.name}
                            </Link>
                        );
                    })}
                </nav>

                {/* Footer Profil */}
                <div className="p-4 border-t border-white/10">
                    <button
                        onClick={handleLogout}
                        className="flex items-center gap-3 w-full px-3 py-3 rounded-xl hover:bg-red-500/10 hover:text-red-400 transition-colors"
                    >
                        <LogOut className="w-5 h-5" />
                        <span>Güvenli Çıkış</span>
                    </button>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 overflow-y-auto">
                <div className="p-8">
                    {children}
                </div>
            </main>
        </div>
    );
}
