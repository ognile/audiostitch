import React, { useState } from 'react';
import axios from 'axios';
import { AudioUploader } from './components/AudioUploader';
import { WaveformVisualizer } from './components/WaveformVisualizer';
import { ControlPanel } from './components/ControlPanel';
import { Wand2, Loader2 } from 'lucide-react';

function App() {
  const [file, setFile] = useState(null);
  const [originalUrl, setOriginalUrl] = useState(null);
  const [processedUrl, setProcessedUrl] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [padding, setPadding] = useState(150);
  const [crossfade, setCrossfade] = useState(50);
  const [error, setError] = useState(null);

  const handleFileSelect = (selectedFile) => {
    setFile(selectedFile);
    setOriginalUrl(URL.createObjectURL(selectedFile));
    setProcessedUrl(null);
    setError(null);
  };

  const handleProcess = async () => {
    if (!file) return;

    setIsProcessing(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('padding', padding);
    formData.append('crossfade', crossfade);

    try {
      const response = await axios.post('http://localhost:8000/process', formData, {
        responseType: 'blob',
      });

      const url = URL.createObjectURL(response.data);
      setProcessedUrl(url);
    } catch (err) {
      console.error(err);
      setError('Failed to process audio. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDownload = () => {
    if (processedUrl) {
      const a = document.createElement('a');
      a.href = processedUrl;
      a.download = 'processed_audio.mp3';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    }
  };

  return (
    <div className="min-h-screen bg-background p-8 font-sans text-foreground">
      <div className="max-w-5xl mx-auto space-y-8">
        <header className="text-center space-y-2">
          <div className="inline-flex items-center justify-center p-3 bg-primary/10 rounded-2xl mb-4">
            <Wand2 className="w-8 h-8 text-primary" />
          </div>
          <h1 className="text-4xl font-bold tracking-tight">SmoothFlow</h1>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
            Intelligent silence removal with natural crossfading.
            Upload your audio and let AI handle the flow.
          </p>
        </header>

        <main className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-6">
            {!originalUrl ? (
              <AudioUploader onFileSelect={handleFileSelect} isProcessing={isProcessing} />
            ) : (
              <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                <WaveformVisualizer
                  audioUrl={originalUrl}
                  title="Original Audio"
                  color="#94a3b8"
                />

                {processedUrl && (
                  <WaveformVisualizer
                    audioUrl={processedUrl}
                    title="Processed Result"
                    color="#4f46e5"
                    onDownload={handleDownload}
                  />
                )}
              </div>
            )}
          </div>

          <div className="space-y-6">
            <ControlPanel
              padding={padding}
              setPadding={setPadding}
              crossfade={crossfade}
              setCrossfade={setCrossfade}
              isProcessing={isProcessing}
            />

            <button
              onClick={handleProcess}
              disabled={!file || isProcessing}
              className="w-full py-4 px-6 bg-primary text-primary-foreground rounded-xl font-semibold text-lg shadow-lg shadow-primary/25 hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
            >
              {isProcessing ? (
                <>
                  <Loader2 className="animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Wand2 size={20} />
                  Process Audio
                </>
              )}
            </button>

            {error && (
              <div className="p-4 bg-destructive/10 text-destructive rounded-xl text-sm text-center">
                {error}
              </div>
            )}

            {originalUrl && !processedUrl && !isProcessing && (
              <button
                onClick={() => {
                  setFile(null);
                  setOriginalUrl(null);
                  setProcessedUrl(null);
                }}
                className="w-full py-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                Upload different file
              </button>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
