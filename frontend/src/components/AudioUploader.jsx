import React, { useCallback } from 'react';
import { Upload, FileAudio } from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs) {
    return twMerge(clsx(inputs));
}

export function AudioUploader({ onFileSelect, isProcessing }) {
    const handleDrop = useCallback((e) => {
        e.preventDefault();
        if (isProcessing) return;

        const file = e.dataTransfer.files[0];
        if (file && file.type.startsWith('audio/')) {
            onFileSelect(file);
        }
    }, [onFileSelect, isProcessing]);

    const handleChange = useCallback((e) => {
        if (isProcessing) return;
        const file = e.target.files?.[0];
        if (file) {
            onFileSelect(file);
        }
    }, [onFileSelect, isProcessing]);

    return (
        <div
            onDrop={handleDrop}
            onDragOver={(e) => e.preventDefault()}
            className={cn(
                "border-2 border-dashed rounded-xl p-12 text-center transition-colors cursor-pointer",
                isProcessing ? "opacity-50 cursor-not-allowed border-gray-300" : "border-gray-300 hover:border-primary hover:bg-secondary/50"
            )}
        >
            <input
                type="file"
                accept="audio/*"
                onChange={handleChange}
                className="hidden"
                id="audio-upload"
                disabled={isProcessing}
            />
            <label htmlFor="audio-upload" className={cn("cursor-pointer flex flex-col items-center gap-4", isProcessing && "cursor-not-allowed")}>
                <div className="p-4 bg-primary/10 rounded-full text-primary">
                    <Upload size={32} />
                </div>
                <div>
                    <h3 className="text-lg font-semibold">Upload Audio File</h3>
                    <p className="text-muted-foreground mt-1">Drag & drop or click to browse</p>
                    <p className="text-xs text-muted-foreground mt-2">Supports MP3, WAV, M4A</p>
                </div>
            </label>
        </div>
    );
}
