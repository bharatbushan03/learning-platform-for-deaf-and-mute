import { useCallback } from 'react';

function useSpeech() {
  const speak = useCallback((text) => {
    if (!('speechSynthesis' in window)) {
      return false;
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'en-IN';
    utterance.rate = 0.92;
    window.speechSynthesis.speak(utterance);
    return true;
  }, []);

  return { speak };
}

export default useSpeech;