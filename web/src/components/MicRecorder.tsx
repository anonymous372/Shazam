"use client";

import React, { useState, useRef } from 'react';
import WaveformVisualizer from './WaveformVisualizer';

interface MicRecorderProps {
  onResult: (result: any) => void;
  onError: (error: string) => void;
}

export default function MicRecorder({ onResult, onError }: MicRecorderProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [timeLeft, setTimeLeft] = useState(15);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const startRecording = async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      setStream(mediaStream);
      
      const mediaRecorder = new MediaRecorder(mediaStream);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };

      mediaRecorder.onstop = async () => {
        setIsProcessing(true);
        const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' });
        await sendToBackend(audioBlob);
        
        // Cleanup stream
        mediaStream.getTracks().forEach(track => track.stop());
        setStream(null);
      };

      mediaRecorder.start();
      setIsRecording(true);
      setTimeLeft(15);

      // 15 second timer
      timerRef.current = setInterval(() => {
        setTimeLeft((prev) => {
          if (prev <= 1) {
            stopRecording();
            return 0;
          }
          return prev - 1;
        });
      }, 1000);

    } catch (err) {
      onError("Microphone access denied or not available.");
      console.error(err);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      if (timerRef.current) clearInterval(timerRef.current);
    }
  };

  const sendToBackend = async (blob: Blob) => {
    const formData = new FormData();
    formData.append("audio", blob, "humming.webm");

    try {
      // In production, this should point to your deployed FastAPI backend
      const response = await fetch("http://localhost:8000/api/identify", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Backend processing failed");
      }

      const data = await response.json();
      onResult(data);
    } catch (err: any) {
      onError(err.message || "Failed to identify song.");
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center w-full">
      <WaveformVisualizer stream={stream} isRecording={isRecording} />
      
      <div className="mt-8 relative flex flex-col items-center">
        {isRecording ? (
          <div className="flex flex-col items-center animate-in fade-in zoom-in duration-300">
            <div className="text-pink-500 font-bold text-2xl mb-4 animate-pulse">
              Listening... {timeLeft}s
            </div>
            <button 
              onClick={stopRecording}
              className="w-20 h-20 bg-red-500 hover:bg-red-600 rounded-full flex items-center justify-center shadow-[0_0_30px_rgba(239,68,68,0.5)] transition-all transform hover:scale-105 active:scale-95"
            >
              <div className="w-6 h-6 bg-white rounded-sm"></div>
            </button>
          </div>
        ) : (
          <div className="flex flex-col items-center">
            {isProcessing ? (
              <div className="flex flex-col items-center animate-in fade-in duration-300">
                <div className="w-16 h-16 border-4 border-violet-500 border-t-transparent rounded-full animate-spin mb-4"></div>
                <p className="text-white font-medium">Analyzing Melody...</p>
              </div>
            ) : (
              <button 
                onClick={startRecording}
                className="group relative w-24 h-24 bg-gradient-to-tr from-pink-500 to-violet-500 rounded-full flex items-center justify-center shadow-[0_0_40px_rgba(139,92,246,0.6)] transition-all hover:scale-105 active:scale-95"
              >
                <div className="absolute inset-0 rounded-full bg-white opacity-0 group-hover:opacity-20 transition-opacity"></div>
                <svg className="w-10 h-10 text-white ml-1" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 14c1.66 0 2.99-1.34 2.99-3L15 5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm5.3-3c0 3-2.54 5.1-5.3 5.1S6.7 14 6.7 11H5c0 3.41 2.72 6.23 6 6.72V21h2v-3.28c3.28-.48 6-3.3 6-6.72h-1.7z"/>
                </svg>
              </button>
            )}
            <p className="mt-6 text-white/60 font-medium">Tap to hum a 15s melody</p>
          </div>
        )}
      </div>
    </div>
  );
}
