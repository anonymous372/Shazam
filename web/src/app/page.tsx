"use client";

import React, { useState, useEffect } from 'react';
import MicRecorder from '@/components/MicRecorder';

export default function Home() {
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [availableSongs, setAvailableSongs] = useState<string[]>([]);

  useEffect(() => {
    fetch('http://localhost:8000/api/songs')
      .then(res => res.json())
      .then(data => setAvailableSongs(data.songs || []))
      .catch(err => console.error("Failed to load songs", err));
  }, []);

  const formatTime = (secondsStr: string | number) => {
    const totalSeconds = typeof secondsStr === 'string' ? parseFloat(secondsStr) : secondsStr;
    if (isNaN(totalSeconds)) return "0:00";
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = Math.floor(totalSeconds % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  const handleResult = (data: any) => {
    setResult(data);
    setError(null);
  };

  const handleError = (msg: string) => {
    setError(msg);
    setResult(null);
  };

  const reset = () => {
    setResult(null);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-4 sm:p-8 font-sans overflow-hidden relative">
      {/* Dynamic Background Gradients */}
      <div className="absolute top-[-10%] left-[-10%] w-96 h-96 bg-pink-500/20 rounded-full blur-[120px] pointer-events-none mix-blend-screen animate-pulse duration-[5000ms]"></div>
      <div className="absolute bottom-[-10%] right-[-10%] w-[30rem] h-[30rem] bg-violet-600/20 rounded-full blur-[150px] pointer-events-none mix-blend-screen"></div>

      <main className="w-full max-w-2xl mx-auto z-10 flex flex-col items-center">
        
        {/* Header */}
        <div className="text-center mb-12 animate-in slide-in-from-bottom-4 fade-in duration-700">
          <div className="inline-block p-1 px-3 mb-4 rounded-full bg-white/10 border border-white/20 backdrop-blur-md">
            <span className="bg-gradient-to-r from-pink-400 to-violet-400 text-transparent bg-clip-text font-semibold text-sm tracking-wide uppercase">
              AI Powered Music Discovery
            </span>
          </div>
          <h1 className="text-5xl sm:text-7xl font-extrabold text-white tracking-tight mb-4">
            Shazam for <br />
            <span className="bg-gradient-to-r from-pink-500 to-violet-500 text-transparent bg-clip-text">
              Kishore Kumar
            </span>
          </h1>
          <p className="text-slate-400 text-lg sm:text-xl font-medium max-w-lg mx-auto">
            Hum the melody of any classic Kishore Kumar song, and our AI will identify it instantly.
          </p>
        </div>

        {/* Interactive Area */}
        <div className="w-full flex flex-col items-center animate-in slide-in-from-bottom-8 fade-in duration-1000 delay-150">
          {!result && !error && (
            <MicRecorder onResult={handleResult} onError={handleError} />
          )}

          {/* Results Area */}
          {result && (
            <div className="w-full bg-white/10 backdrop-blur-2xl border border-white/20 rounded-3xl p-8 shadow-2xl text-center animate-in zoom-in-95 duration-500">
              <h2 className="text-slate-300 font-medium text-lg mb-2">We found a match!</h2>
              <div className="text-4xl sm:text-5xl font-bold text-white mb-6">
                {result.song !== "No match found" 
                  ? result.song.split('｜')[0].split('-')[0].split('：')[0].replace('.webm', '').trim() 
                  : "No Match Found"}
              </div>
              
              {result.song !== "No match found" && (
                <div className="text-slate-400 text-sm mb-6 bg-white/5 rounded-xl p-4 border border-white/10 text-left">
                  <div className="mb-2">⏱️ You started humming at <strong>{formatTime(result.query_start_time)}</strong> into the recording.</div>
                  <div>🎵 That perfectly matched the original song at the <strong>{formatTime(result.target_start_time)}</strong> mark!</div>
                </div>
              )}
              
              {result.song !== "No match found" && result.top_matches && (
                <div className="flex flex-col items-center gap-3 mb-8 w-full max-w-sm mx-auto">
                  <h3 className="text-slate-400 text-xs font-semibold uppercase tracking-wider mb-1 w-full text-left">Top 3 Matches</h3>
                  {result.top_matches.map((match: any, index: number) => (
                    <div key={index} className={`w-full flex justify-between items-center rounded-xl p-3 border ${index === 0 ? 'bg-emerald-500/10 border-emerald-500/30' : 'bg-white/5 border-white/10'}`}>
                      <div className="flex flex-col text-left">
                        <span className="text-slate-200 font-medium text-sm">
                          {index + 1}. {match.song.split('｜')[0].split('-')[0].split('：')[0].replace('.webm', '').trim()}
                        </span>
                        {index > 0 && <span className="text-slate-500 text-xs">Matched at {formatTime(match.target_start_time)}</span>}
                      </div>
                      <span className={`${index === 0 ? 'text-emerald-400 font-bold' : 'text-amber-400 font-semibold'} text-sm`}>
                        {Math.round(match.confidence)}%
                      </span>
                    </div>
                  ))}
                </div>
              )}

              <button 
                onClick={reset}
                className="px-8 py-4 bg-white/10 hover:bg-white/20 text-white rounded-full font-semibold transition-colors border border-white/10"
              >
                Try Another Song
              </button>
            </div>
          )}

          {/* Error State */}
          {error && (
            <div className="w-full bg-red-500/10 border border-red-500/30 rounded-3xl p-8 text-center animate-in zoom-in-95 duration-300">
              <svg className="w-12 h-12 text-red-400 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <h2 className="text-xl font-bold text-red-400 mb-2">Oops! Something went wrong</h2>
              <p className="text-red-200 mb-6">{error}</p>
              <button 
                onClick={reset}
                className="px-6 py-3 bg-red-500/20 hover:bg-red-500/30 text-red-300 rounded-full font-semibold transition-colors border border-red-500/20"
              >
                Try Again
              </button>
            </div>
          )}
        </div>

        {/* Available Songs List */}
        {availableSongs.length > 0 && (
          <div className="w-full mt-16 animate-in slide-in-from-bottom-12 fade-in duration-1000 delay-300">
            <h3 className="text-slate-400 font-medium text-sm uppercase tracking-widest text-center mb-6">
              Songs in Database
            </h3>
            <div className="flex flex-wrap justify-center gap-3">
              {availableSongs.map((song, i) => {
                // Keep the display name short if it's very long (splitting by common YouTube title delimiters)
                let displayName = song.split('｜')[0].split('-')[0].split('：')[0].trim();
                if (displayName.length > 40) displayName = displayName.substring(0, 40) + '...';
                return (
                  <div key={i} className="px-4 py-2 rounded-full bg-white/5 border border-white/10 text-slate-300 text-sm hover:bg-white/10 hover:border-white/20 transition-all cursor-default">
                    {displayName}
                  </div>
                );
              })}
            </div>
          </div>
        )}

      </main>
    </div>
  );
}
