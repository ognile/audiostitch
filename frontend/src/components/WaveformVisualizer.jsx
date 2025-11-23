import React, { useEffect, useRef, useState } from 'react';
import WaveSurfer from 'wavesurfer.js';
import { Play, Pause, Download } from 'lucide-react';
import { cn } from './AudioUploader';

export function WaveformVisualizer({ audioUrl, title, color = '#4f46e5', onDownload }) {
    const containerRef = useRef(null);
    const wavesurfer = useRef(null);
    const [isPlaying, setIsPlaying] = useState(false);
    const [isReady, setIsReady] = useState(false);

    useEffect(() => {
        if (!containerRef.current || !audioUrl) return;

        wavesurfer.current = WaveSurfer.create({
            container: containerRef.current,
            waveColor: '#e2e8f0',
            progressColor: color,
            cursorColor: color,
            barWidth: 2,
            barGap: 3,
            height: 100,
            normalize: true,
        });

        wavesurfer.current.load(audioUrl);

        wavesurfer.current.on('ready', () => {
            setIsReady(true);
        });

        wavesurfer.current.on('finish', () => {
            setIsPlaying(false);
        });

        return () => {
            wavesurfer.current.destroy();
        };
    }, [audioUrl, color]);

    const togglePlay = () => {
        if (wavesurfer.current) {
            wavesurfer.current.playPause();
            setIsPlaying(!isPlaying);
        }
    };

    return (
        <div className="bg-card border rounded-xl p-6 shadow-sm">
            <div className="flex justify-between items-center mb-4">
                <h3 className="font-semibold text-lg">{title}</h3>
                <div className="flex gap-2">
                    <button
                        onClick={togglePlay}
                        disabled={!isReady}
                        className="p-2 rounded-full hover:bg-secondary transition-colors disabled:opacity-50"
                    >
                        {isPlaying ? <Pause size={20} /> : <Play size={20} />}
                    </button>
                    {onDownload && (
                        <button
                            onClick={onDownload}
                            disabled={!isReady}
                            className="p-2 rounded-full hover:bg-secondary transition-colors disabled:opacity-50"
                        >
                            <Download size={20} />
                        </button>
                    )}
                </div>
            </div>

            <div ref={containerRef} className={cn("w-full", !isReady && "opacity-50")} />

            {!isReady && audioUrl && (
                <div className="text-center text-sm text-muted-foreground mt-2">
                    Loading waveform...
                </div>
            )}
        </div>
    );
}
