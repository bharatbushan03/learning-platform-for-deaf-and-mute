import React, { useEffect, useMemo, useRef, useState } from 'react';
import CameraPanel from '../components/CameraPanel';
import SkeletonPanel from '../components/SkeletonPanel';
import PredictionDisplay from '../components/PredictionDisplay';
import ActionButtons from '../components/ActionButtons';
import SuggestionsRow from '../components/SuggestionsRow';
import { drawSkeleton, clearSkeleton } from '../utils/drawSkeleton';

function Home({
  cameraRef,
  cameraCanvasRef,
  isCameraOn,
  isDetecting,
  connectionStatus,
  confidence,
  currentChar,
  sentence,
  landmarks,
  fps,
  toggleCamera,
  toggleDetection,
  speakSentence,
  clearAll,
  backspace,
  suggestions,
  applySuggestion,
  stableCount,
  onCaptureHistory,
  onToast,
  onPrediction,
}) {
  const skeletonCanvasRef = useRef(null);
  const resizeObserverRef = useRef(null);

  useEffect(() => {
    const canvas = skeletonCanvasRef.current;
    if (!canvas) {
      return undefined;
    }

    const resizeCanvas = () => {
      const parent = canvas.parentElement;
      if (!parent) {
        return;
      }
      canvas.width = parent.clientWidth;
      canvas.height = parent.clientHeight;
      drawSkeleton(canvas, landmarks);
    };

    resizeCanvas();
    resizeObserverRef.current = new ResizeObserver(resizeCanvas);
    resizeObserverRef.current.observe(canvas.parentElement);

    return () => {
      resizeObserverRef.current?.disconnect();
      resizeObserverRef.current = null;
    };
  }, [landmarks]);

  useEffect(() => {
    drawSkeleton(skeletonCanvasRef.current, landmarks);
  }, [landmarks]);

  useEffect(() => {
    if (!landmarks.length) {
      clearSkeleton(skeletonCanvasRef.current);
    }
  }, [landmarks]);

  const prefix = useMemo(() => {
    const combined = `${sentence}${currentChar}`.trimEnd();
    if (!combined) {
      return '';
    }
    return combined.split(/\s+/).at(-1)?.toUpperCase() || '';
  }, [sentence, currentChar]);

  const statusMessage = stableCount >= 15 ? 'Stable prediction ready' : connectionStatus;

  return (
    <div className="page page-home">
      <div className="hero-banner">
        <div>
          <p className="eyebrow">Real-time ISL recognition</p>
          <h2>Translate hand gestures into text with live stability filtering.</h2>
        </div>
        <div className="live-badges">
          <span className={`status-chip ${isCameraOn ? 'on' : ''}`}>{isCameraOn ? 'Camera On' : 'Camera Off'}</span>
          <span className={`status-chip ${isDetecting ? 'on' : ''}`}>{isDetecting ? 'Detecting' : 'Detect Off'}</span>
          <span className="status-chip on">{statusMessage}</span>
        </div>
      </div>

      <div className="grid-two">
        <CameraPanel
          videoRef={cameraRef}
          isCameraOn={isCameraOn}
          isDetecting={isDetecting}
          fps={fps}
          toggleCamera={toggleCamera}
          toggleDetection={toggleDetection}
        />
        <SkeletonPanel canvasRef={skeletonCanvasRef} confidence={confidence} hasLandmarks={landmarks.length > 0} />
      </div>

      <div className="grid-two bottom-grid">
        <PredictionDisplay currentChar={currentChar} sentence={sentence} />
        <ActionButtons speakSentence={speakSentence} clearAll={clearAll} />
      </div>

      <SuggestionsRow
        suggestions={suggestions}
        prefix={prefix}
        onApplySuggestion={applySuggestion}
        onBackspace={backspace}
      />
    </div>
  );
}

export default Home;