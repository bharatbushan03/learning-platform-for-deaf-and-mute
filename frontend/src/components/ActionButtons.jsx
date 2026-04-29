import React from 'react';

function ActionButtons({ speakSentence, clearAll }) {
  return (
    <section className="panel action-panel">
      <button type="button" className="btn btn-primary" onClick={speakSentence}>Speak</button>
      <button type="button" className="btn btn-ghost" onClick={clearAll}>Clear</button>
    </section>
  );
}

export default ActionButtons;