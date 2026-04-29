import React, { useEffect, useMemo, useRef, useState } from 'react';
import { NavLink, Navigate, Route, Routes, useLocation } from 'react-router-dom';
import Header from './components/Header';
import CameraPanel from './components/CameraPanel';
import SkeletonPanel from './components/SkeletonPanel';
import PredictionDisplay from './components/PredictionDisplay';
import ActionButtons from './components/ActionButtons';
import SuggestionsRow from './components/SuggestionsRow';
import Toast from './components/Toast';
import Home from './pages/Home';
import About from './pages/About';
import History from './pages/History';
import useCamera from './hooks/useCamera';
import useSpeech from './hooks/useSpeech';
import useWebSocket from './hooks/useWebSocket';
import { WORD_BANK } from './utils/wordBank';

export const HISTORY_STORAGE_KEY = 'isl-prediction-history';

function getHistory() {
  try {
    const parsed = JSON.parse(localStorage.getItem(HISTORY_STORAGE_KEY) || '[]');
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function pushHistoryEntry(entry) {
  const next = [entry, ...getHistory()].slice(0, 50);
  localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(next));
  return next;
}

function AppShell() {
  const [toasts, setToasts] = useState([]);
  const [, setPredictionHistory] = useState(() => getHistory());
  const [currentChar, setCurrentChar] = useState('');
  const [sentence, setSentence] = useState('');
  const [fps, setFps] = useState(0);
  const [confidence, setConfidence] = useState(0);
  const [landmarks, setLandmarks] = useState([]);
  const [stableCount, setStableCount] = useState(0);
  const [isDetecting, setIsDetecting] = useState(false);
  const [isCameraOn, setIsCameraOn] = useState(false);

  const camera = useCamera();
  const speech = useSpeech();
  const socket = useWebSocket({
    enabled: isCameraOn && isDetecting,
    onOpen: () => addToast('Backend connected'),
    onClose: () => addToast('Backend disconnected'),
  });

  const frameTimerRef = useRef(null);
  const fpsTimerRef = useRef(null);
  const frameCountRef = useRef(0);
  const sentenceSnapshot = useRef('');
  const lastPredictionRef = useRef('');
  const lastCommittedRef = useRef('');

  const connectionStatus = socket.isConnected ? 'Connected' : socket.isConnecting ? 'Connecting...' : 'Disconnected';

  function addToast(message) {
    const id = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
    setToasts((items) => [...items, { id, message }]);
  }

  function removeToast(id) {
    setToasts((items) => items.filter((item) => item.id !== id));
  }

  function commitPrediction(prediction, predictionConfidence) {
    if (!prediction) {
      return;
    }

    if (prediction === 'SPACE' || prediction === 'NEXT') {
      setSentence((value) => `${value.replace(/\s+$/g, '')} `);
      setCurrentChar('');
      lastCommittedRef.current = prediction;
      addToast('Word captured');
      return;
    }

    const normalized = prediction.toUpperCase();
    setSentence((value) => `${value}${normalized}`);
    setCurrentChar('');
    lastCommittedRef.current = normalized;
    setPredictionHistory((items) => {
      const next = pushHistoryEntry({
        prediction: normalized,
        confidence: Math.round(predictionConfidence),
        timestamp: new Date().toISOString(),
      });
      return next;
    });
    addToast('Word captured');
  }

  function handlePrediction(payload) {
    const nextPrediction = payload?.prediction ? String(payload.prediction).toUpperCase() : '';
    const nextConfidence = Number(payload?.confidence || 0);
    const handDetected = Boolean(payload?.hand_detected);
    const nextLandmarks = Array.isArray(payload?.landmarks) ? payload.landmarks : [];

    setConfidence(nextConfidence);
    setLandmarks(nextLandmarks);

    if (!handDetected || !nextPrediction) {
      setStableCount(0);
      lastPredictionRef.current = '';
      setCurrentChar('');
      return;
    }

    setCurrentChar(nextPrediction);

    setStableCount((current) => {
      const previousPrediction = lastPredictionRef.current;
      const nextCount = nextPrediction === previousPrediction ? current + 1 : 1;
      if (nextPrediction !== previousPrediction) {
        lastPredictionRef.current = nextPrediction;
      }

      if (nextCount >= 15 && nextPrediction !== lastCommittedRef.current) {
        commitPrediction(nextPrediction, nextConfidence);
        return 0;
      }

      return nextCount;
    });
  }

  useEffect(() => {
    if (!socket.message) {
      return;
    }
    handlePrediction(socket.message);
  }, [socket.message]);

  useEffect(() => {
    if (!isCameraOn || !isDetecting) {
      if (frameTimerRef.current) {
        clearInterval(frameTimerRef.current);
        frameTimerRef.current = null;
      }
      if (fpsTimerRef.current) {
        clearInterval(fpsTimerRef.current);
        fpsTimerRef.current = null;
      }
      frameCountRef.current = 0;
      setFps(0);
      return;
    }

    if (!fpsTimerRef.current) {
      fpsTimerRef.current = setInterval(() => {
        setFps(frameCountRef.current);
        frameCountRef.current = 0;
      }, 1000);
    }

    frameTimerRef.current = setInterval(async () => {
      const frame = await camera.captureFrame();
      if (frame) {
        socket.send(JSON.stringify({ frame }));
        frameCountRef.current += 1;
      }
    }, 100);

    return () => {
      if (frameTimerRef.current) {
        clearInterval(frameTimerRef.current);
        frameTimerRef.current = null;
      }
      if (fpsTimerRef.current) {
        clearInterval(fpsTimerRef.current);
        fpsTimerRef.current = null;
      }
    };
  }, [isCameraOn, isDetecting, camera, socket]);

  useEffect(() => {
    sentenceSnapshot.current = sentence;
  }, [sentence]);

  useEffect(() => {
    const onKeyDown = (event) => {
      if (event.target && ['INPUT', 'TEXTAREA'].includes(event.target.tagName)) {
        return;
      }
      if (event.code === 'Space') {
        event.preventDefault();
        clearAll();
      }
      if (event.key?.toLowerCase() === 's') {
        speakSentence();
      }
    };

    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, []);

  async function startCamera() {
    try {
      await camera.startCamera();
      setIsCameraOn(true);
      addToast('Camera started');
    } catch {
      addToast('Camera access denied');
    }
  }

  function stopCamera() {
    camera.stopCamera();
    setIsCameraOn(false);
    setIsDetecting(false);
    setCurrentChar('');
    setStableCount(0);
    lastPredictionRef.current = '';
    lastCommittedRef.current = '';
    setLandmarks([]);
    setConfidence(0);
    addToast('Camera stopped');
  }

  function toggleCamera() {
    if (isCameraOn) {
      stopCamera();
      return;
    }
    startCamera();
  }

  function toggleDetection() {
    if (!isCameraOn) {
      addToast('Start the camera first');
      return;
    }
    setIsDetecting((value) => !value);
  }

  function clearAll() {
    setCurrentChar('');
    setSentence('');
    setStableCount(0);
    lastPredictionRef.current = '';
    lastCommittedRef.current = '';
    setConfidence(0);
    setLandmarks([]);
    addToast('Cleared');
  }

  function speakSentence() {
    const text = `${sentenceSnapshot.current}${currentChar}`.trim();
    if (!text) {
      addToast('Nothing to speak');
      return;
    }
    speech.speak(text);
    addToast('Speaking');
  }

  function backspace() {
    if (currentChar) {
      setCurrentChar('');
      return;
    }
    setSentence((value) => value.slice(0, -1));
  }

  function applySuggestion(word) {
    setSentence((value) => {
      const trimmed = `${value}${currentChar}`.trimEnd();
      const parts = trimmed ? trimmed.split(/\s+/) : [];
      if (parts.length) {
        parts.pop();
      }
      parts.push(word);
      return `${parts.join(' ')} `;
    });
    setCurrentChar('');
    addToast(`Applied ${word}`);
  }

  const prefix = useMemo(() => {
    const combined = `${sentence}${currentChar}`.trimEnd();
    if (!combined) {
      return '';
    }
    const parts = combined.split(/\s+/);
    return parts[parts.length - 1].toUpperCase();
  }, [sentence, currentChar]);

  const suggestions = useMemo(() => {
    if (!prefix) {
      return [];
    }
    return WORD_BANK.filter((word) => word.startsWith(prefix) && word !== prefix).slice(0, 4);
  }, [prefix]);

  const sentenceDisplay = `${sentence}${currentChar}`.trim();

  return (
    <div className="app-shell">
      <Header connectionStatus={connectionStatus} />
      <main className="app-grid">
        <Routes>
          <Route
            path="/"
            element={(
              <Home
                cameraRef={camera.videoRef}
                isCameraOn={isCameraOn}
                isDetecting={isDetecting}
                connectionStatus={connectionStatus}
                confidence={confidence}
                currentChar={currentChar}
                sentence={sentenceDisplay}
                landmarks={landmarks}
                fps={fps}
                toggleCamera={toggleCamera}
                toggleDetection={toggleDetection}
                speakSentence={speakSentence}
                clearAll={clearAll}
                backspace={backspace}
                suggestions={suggestions}
                applySuggestion={applySuggestion}
                stableCount={stableCount}
                onCaptureHistory={setPredictionHistory}
                onToast={addToast}
                onPrediction={handlePrediction}
              />
            )}
          />
          <Route path="/about" element={<About />} />
          <Route path="/history" element={<History />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
      <Toast items={toasts} onDismiss={removeToast} />
    </div>
  );
}

export default function App() {
  const location = useLocation();

  return (
    <div className="layout-root">
      <nav className="top-nav">
        <NavLink to="/" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>Home</NavLink>
        <NavLink to="/about" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>About</NavLink>
        <NavLink to="/history" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>History</NavLink>
      </nav>
      <AppShell key={location.pathname} />
    </div>
  );
}