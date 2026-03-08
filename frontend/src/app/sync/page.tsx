'use client';

import { useState, useCallback, useEffect } from 'react';
import { UploadCloud, FileText, CheckCircle2, Loader2, ArrowRight, Download, RefreshCcw } from 'lucide-react';
import { usePipelineStore } from '@/store/pipelineStore';
import { listenToPipelineStatus } from '@/lib/sse';
import { motion, AnimatePresence } from 'framer-motion';
import DashboardLayout from '@/components/DashboardLayout';

export default function Home() {
  const { status, message, progress, setStatus } = usePipelineStore();
  const [isHovered, setIsHovered] = useState(false);
  const [file, setFile] = useState<File | null>(null);

  // SSE Dinleyici
  useEffect(() => {
    if (status === 'processing') {
      const sse = listenToPipelineStatus(
        (data) => {
          if (data.status === 'error') {
            setStatus('error', data.message, 0);
          } else if (data.status === 'completed') {
            setStatus('completed', data.message, 100);
          } else {
            setStatus('processing', data.message, data.progress);
          }
        },
        () => {
          // Error handler
          setStatus('error', 'Sunucu ile bağlantı kesildi!', 0);
        }
      );
      return () => sse.close();
    }
  }, [status, setStatus]);

  const onDrop = useCallback(async (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsHovered(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile.type !== 'application/pdf') {
        alert('Lütfen sadece PDF dosyası yükleyin!');
        return;
      }
      handleUpload(droppedFile);
    }
  }, []);

  const handleUpload = async (pdfFile: File) => {
    setFile(pdfFile);
    setStatus('uploading', 'Dosya yükleniyor...', 5);

    const formData = new FormData();
    formData.append('file', pdfFile);

    try {
      const response = await fetch('http://localhost:8000/upload-pdf', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Yükleme hatası');

      setStatus('processing', 'Analiz başlatılıyor...', 10);
    } catch (err) {
      setStatus('error', 'Dosya gönderilirken hata oluştu.', 0);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleUpload(e.target.files[0]);
    }
  };

  return (
    <DashboardLayout>
      <main className="flex flex-col w-full max-w-5xl mx-auto">
        {/* Header */}
        <div className="max-w-4xl mx-auto w-full text-center mb-12">
          <h1 className="text-4xl font-extrabold text-[#001b3a] tracking-tight">
            Price<span className="text-emerald-500">Sync</span> Engine
          </h1>
          <p className="mt-4 text-lg text-slate-500 max-w-2xl mx-auto">
            Tedarikçi fiyat listelerinizi vizyon modelleriyle saniyeler içinde okuyun ve ERP veritabanınızla %100 uyumla eşleştirin.
          </p>
        </div>

        <div className="max-w-3xl mx-auto w-full">
          <AnimatePresence mode="wait">
            {/* UPLOAD STATE */}
            {status === 'idle' || status === 'error' ? (
              <motion.div
                key="upload"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className={`
                relative flex flex-col items-center justify-center p-12 mt-4 
                border-2 border-dashed rounded-3xl transition-all bg-white
                ${isHovered ? 'border-emerald-400 bg-emerald-50/50' : 'border-slate-200'}
                ${status === 'error' ? 'border-red-300 bg-red-50' : ''}
              `}
                onDragOver={(e) => { e.preventDefault(); setIsHovered(true); }}
                onDragLeave={() => setIsHovered(false)}
                onDrop={onDrop}
              >
                <div className="p-4 bg-emerald-100/50 rounded-full mb-6">
                  <UploadCloud className="w-10 h-10 text-emerald-600" />
                </div>
                <h3 className="text-xl font-semibold text-slate-800 mb-2">
                  PDF Fiyat Listesini Sürükleyin
                </h3>
                <p className="text-slate-500 mb-8 text-center max-w-md">
                  YİTAŞ veya benzeri tedarikçilerinizin fiyat listelerini (PDF) buraya bırakın veya bilgisayarınızdan seçin.
                </p>

                <label className="cursor-pointer group">
                  <div className="bg-[#001b3a] hover:bg-[#002855] text-white px-8 py-3.5 rounded-xl font-medium transition-colors shadow-sm shadow-slate-200/50 flex items-center gap-2">
                    <FileText className="w-4 h-4" />
                    Dosya Seçin
                  </div>
                  <input type="file" className="hidden" accept=".pdf" onChange={handleFileInput} />
                </label>

                {status === 'error' && (
                  <div className="mt-6 text-red-500 font-medium text-sm text-center">
                    Hata: {message}
                  </div>
                )}
              </motion.div>
            ) : (
              /* PROGRESS STATE */
              <motion.div
                key="progress"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="bg-white rounded-3xl p-10 border border-slate-100 shadow-xl shadow-slate-200/20"
              >
                <div className="flex items-start justify-between mb-8">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-emerald-50 rounded-xl flex items-center justify-center border border-emerald-100">
                      <FileText className="w-6 h-6 text-emerald-600" />
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-slate-800">
                        {file?.name || "Belge İşleniyor"}
                      </h3>
                      <p className="text-slate-500 text-sm">
                        {status === 'completed' ? 'İşlem Başarılı' : 'Vektörel Arama & AI Hakemi Devrede'}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-3xl font-bold text-[#001b3a]">{progress}%</span>
                  </div>
                </div>

                {/* İlerleme Çubuğu */}
                <div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden mb-6 relative">
                  <motion.div
                    className="absolute top-0 left-0 h-full bg-emerald-500"
                    initial={{ width: 0 }}
                    animate={{ width: `${progress}%` }}
                    transition={{ ease: "easeInOut", duration: 0.5 }}
                  />
                </div>

                {/* Canlı Mesaj ve Durum İkonları */}
                <div className="flex flex-col gap-4">
                  <div className="flex items-center justify-between p-4 bg-slate-50 rounded-2xl border border-slate-100">
                    <div className="flex items-center gap-3">
                      {status === 'completed' ? (
                        <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                      ) : (
                        <Loader2 className="w-5 h-5 text-slate-400 animate-spin" />
                      )}
                      <span className="text-slate-600 font-medium">{message}</span>
                    </div>
                  </div>

                  {/* Otonom İndirme Butonları (İşlem Bitince Görünür) */}
                  {status === 'completed' && (
                    <div className="flex flex-col gap-4 w-full">
                      <div className="flex gap-4 w-full">
                        <a href={`http://localhost:8000/download-excel?t=${Date.now()}`} download className="flex-1 flex flex-col items-center justify-center gap-1 p-4 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 text-emerald-700 rounded-2xl transition-all shadow-sm group">
                          <div className="flex items-center gap-2 font-bold text-lg">
                            <Download className="w-5 h-5 group-hover:-translate-y-1 transition-transform" /> Güncel Fiyatlı Excel
                          </div>
                          <span className="text-xs font-medium text-emerald-600">Veritabanına Aktarılanlar</span>
                        </a>

                        <a href={`http://localhost:8000/download-report?t=${Date.now()}`} download className="flex-1 flex flex-col items-center justify-center gap-1 p-4 bg-blue-50 hover:bg-blue-100 border border-blue-200 text-blue-700 rounded-2xl transition-all shadow-sm group">
                          <div className="flex items-center gap-2 font-bold text-lg">
                            <FileText className="w-5 h-5 group-hover:-translate-y-1 transition-transform" /> AI İşlem Raporu
                          </div>
                          <span className="text-xs font-medium text-blue-600">Audit Log & Güven Skorları</span>
                        </a>
                      </div>

                      <button
                        onClick={() => {
                          setStatus('idle', 'Sistem Hazır. İşlem başlatmak için belgenizi sürükleyin.', 0);
                          setFile(null);
                        }}
                        className="w-full flex items-center justify-center gap-2 p-4 bg-slate-100/80 hover:bg-slate-200 border border-slate-200 text-slate-700 hover:text-slate-900 rounded-2xl transition-all shadow-sm font-semibold text-lg group"
                      >
                        <RefreshCcw className="w-5 h-5 group-hover:-rotate-90 transition-transform duration-300" /> Yeni Fiyat Listesi Yükle
                      </button>
                    </div>
                  )}
                </div>
              </motion.div>
            )}

          </AnimatePresence>
        </div>
      </main>
    </DashboardLayout>
  );
}
