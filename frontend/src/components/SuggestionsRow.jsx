import React from 'react';

function SuggestionsRow({ suggestions, prefix, onApplySuggestion, onBackspace }) {
  return (
    <section className="panel suggestions-panel">
      <div className="suggestions-head">
        <span className="suggestions-title">Suggestions :</span>
        <button type="button" className="chip backspace" onClick={onBackspace}>⌫ Back</button>
      </div>
      <div className="suggestions-list">
        {suggestions.length ? suggestions.map((word) => (
          <button key={word} type="button" className="chip" onClick={() => onApplySuggestion(word)}>
            {word}
          </button>
        )) : <span className="chip ghost">{prefix ? `${prefix}?` : '—'}</span>}
      </div>
    </section>
  );
}

export default SuggestionsRow;