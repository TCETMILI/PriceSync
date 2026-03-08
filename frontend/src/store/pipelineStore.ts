import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface PipelineState {
    status: 'idle' | 'uploading' | 'processing' | 'completed' | 'error' | 'resolution';
    message: string;
    progress: number;
    setStatus: (status: PipelineState['status'], message: string, progress?: number) => void;
    reset: () => void;
}

export const usePipelineStore = create<PipelineState>()(
    persist(
        (set) => ({
            status: 'idle',
            message: 'Sistem Hazır. İşlem başlatmak için belgenizi sürükleyin.',
            progress: 0,
            setStatus: (status, message, progress) =>
                set((state) => ({
                    status,
                    message,
                    progress: progress !== undefined ? progress : state.progress
                })),
            reset: () => set({ status: 'idle', message: 'Sistem Hazır.', progress: 0 })
        }),
        {
            name: 'pipeline-store',
        }
    )
)
