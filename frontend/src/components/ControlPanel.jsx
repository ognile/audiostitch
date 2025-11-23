import React from 'react';
import { Settings2 } from 'lucide-react';

export function ControlPanel({ padding, setPadding, crossfade, setCrossfade, isProcessing }) {
    return (
        <div className="bg-card border rounded-xl p-6 space-y-6">
            <div className="flex items-center gap-2 mb-4">
                <Settings2 className="text-primary" size={20} />
                <h2 className="font-semibold text-lg">Processing Settings</h2>
            </div>

            <div className="space-y-4">
                <div>
                    <div className="flex justify-between mb-2">
                        <label className="text-sm font-medium">Padding (ms)</label>
                        <span className="text-sm text-muted-foreground">{padding}ms</span>
                    </div>
                    <input
                        type="range"
                        min="0"
                        max="500"
                        step="10"
                        value={padding}
                        onChange={(e) => setPadding(Number(e.target.value))}
                        disabled={isProcessing}
                        className="w-full h-2 bg-secondary rounded-lg appearance-none cursor-pointer accent-primary"
                    />
                    <p className="text-xs text-muted-foreground mt-1">
                        Silence to keep around speech
                    </p>
                </div>

                <div>
                    <div className="flex justify-between mb-2">
                        <label className="text-sm font-medium">Crossfade (ms)</label>
                        <span className="text-sm text-muted-foreground">{crossfade}ms</span>
                    </div>
                    <input
                        type="range"
                        min="0"
                        max="200"
                        step="10"
                        value={crossfade}
                        onChange={(e) => setCrossfade(Number(e.target.value))}
                        disabled={isProcessing}
                        className="w-full h-2 bg-secondary rounded-lg appearance-none cursor-pointer accent-primary"
                    />
                    <p className="text-xs text-muted-foreground mt-1">
                        Overlap duration between clips
                    </p>
                </div>
            </div>
        </div>
    );
}
