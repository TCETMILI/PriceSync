'use client';

import { useState, useEffect } from 'react';

import { Activity, ShieldCheck, FileSpreadsheet, Layers } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import DashboardLayout from '@/components/DashboardLayout';

export default function DashboardCockpit() {
    const [statsData, setStatsData] = useState([
        { title: 'Toplam İşlenen', value: 0, target: 0, desc: 'Son 30 günde eşleştirme', icon: Layers, color: 'text-blue-500', bg: 'bg-blue-50' },
        { title: 'Bekleyen Onay', value: 0, target: 0, desc: 'Çözüm merkezinde', icon: Activity, color: 'text-orange-500', bg: 'bg-orange-50' },
        { title: 'AI Başarı Oranı', value: 0, target: 0, isPercent: true, desc: 'Otomatik onay oranı', icon: ShieldCheck, color: 'text-emerald-500', bg: 'bg-emerald-50' },
        { title: 'Güncellenen Excel', value: 0, target: 0, desc: 'Bu ayki Batch logları', icon: FileSpreadsheet, color: 'text-purple-500', bg: 'bg-purple-50' },
    ]);

    useEffect(() => {
        // Rastgele hedefler belirle
        const targets = [
            Math.floor(Math.random() * (15000 - 8000 + 1)) + 8000, // 8000-15000 arası
            Math.floor(Math.random() * (100 - 10 + 1)) + 10,       // 10-100 arası
            (Math.random() * (99.9 - 85.0) + 85.0).toFixed(1),     // 85.0-99.9 arası
            Math.floor(Math.random() * (200 - 20 + 1)) + 20        // 20-200 arası
        ];

        let startTimestamp: number | null = null;
        const duration = 1500; // 1.5 saniye

        const step = (timestamp: number) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);

            // easeOutQuad efekti
            const easeProgress = progress * (2 - progress);

            setStatsData(prev => prev.map((stat, idx) => {
                const target = Number(targets[idx]);
                let currentValue = progress === 1 ? target : target * easeProgress;

                return {
                    ...stat,
                    value: stat.isPercent ? Number(currentValue.toFixed(1)) : Math.floor(currentValue),
                    target: target
                };
            }));

            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        };

        window.requestAnimationFrame(step);
    }, []);

    const data = [
        { name: 'Pzt', islem: 400 },
        { name: 'Sal', islem: 300 },
        { name: 'Çar', islem: 550 },
        { name: 'Per', islem: 200 },
        { name: 'Cum', islem: 680 },
        { name: 'Cts', islem: 150 },
        { name: 'Paz', islem: 90 },
    ];

    return (
        <DashboardLayout>
            <div className="max-w-7xl mx-auto w-full">
                <div className="mb-10">
                    <h1 className="text-3xl font-extrabold text-slate-800 tracking-tight">Panel</h1>
                    <p className="text-slate-600 mt-1 font-medium">PriceSync Sistem Özeti ve İstatistikleri</p>
                </div>

                {/* Metrics Row */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
                    {statsData.map((stat, idx) => (
                        <div key={idx} className="bg-white rounded-3xl p-6 border border-slate-100 shadow-sm flex items-center gap-5">
                            <div className={`w-14 h-14 rounded-2xl flex items-center justify-center ${stat.bg}`}>
                                <stat.icon className={`w-7 h-7 ${stat.color}`} />
                            </div>
                            <div>
                                <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-1">{stat.title}</h3>
                                <div className="text-2xl font-bold text-slate-800">
                                    {stat.isPercent ? `%${stat.value}` : stat.value.toLocaleString('tr-TR')}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>

                {/* Chart Section */}
                <div className="bg-white rounded-3xl p-8 border border-slate-100 shadow-sm relative overflow-hidden">
                    {/* Şık arkaplan geçişi (SaaS cila) */}
                    <div className="absolute top-0 right-0 w-64 h-64 bg-emerald-50 rounded-full blur-3xl opacity-50 -mr-20 -mt-20"></div>

                    <div className="mb-6 relative z-10">
                        <h2 className="text-xl font-bold text-slate-800">Haftalık Eşleştirme Hacmi</h2>
                        <p className="text-slate-500 text-sm">Sistemden geçen toplam PDF satırları</p>
                    </div>

                    <div className="h-80 w-full relative z-10">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                                <defs>
                                    <linearGradient id="colorIslem" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 12 }} dy={10} />
                                <YAxis axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 12 }} />
                                <Tooltip
                                    contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                                    cursor={{ stroke: '#cbd5e1', strokeWidth: 1, strokeDasharray: '4 4' }}
                                />
                                <Area
                                    type="monotone"
                                    dataKey="islem"
                                    stroke="#10b981"
                                    strokeWidth={3}
                                    fillOpacity={1}
                                    fill="url(#colorIslem)"
                                    activeDot={{ r: 6, fill: '#10b981', stroke: '#fff', strokeWidth: 2 }}
                                />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}
