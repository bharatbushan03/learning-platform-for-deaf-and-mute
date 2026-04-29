import React from 'react';

function PredictionDisplay({ currentChar, sentence }) {
  return (
    <section className="panel prediction-panel">
      <div className="prediction-row">
        <span className="prediction-label">Character :</span>
        <span className={`prediction-value monospace ${currentChar ? 'pop' : 'empty'}`}>{currentChar || '—'}</span>
      </div>
      <div className="divider" />
      <div className="prediction-row">
        <span className="prediction-label">Sentence :</span>
        <span className={`sentence-value monospace ${sentence ? '' : 'empty'}`}>{sentence || '—'}</span>
      </div>
    </section>
  );
}

export default PredictionDisplay;