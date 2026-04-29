import React from 'react';

function About() {
  return (
    <div className="page page-info">
      <section className="panel info-panel">
        <p className="eyebrow">About the project</p>
        <h2>What is Indian Sign Language?</h2>
        <p>
          Indian Sign Language is a visual language used by the Deaf community across India.
          This application focuses on translating hand gestures into readable text in real time.
        </p>
      </section>

      <section className="panel info-panel">
        <p className="eyebrow">How it works</p>
        <ol className="flow-list">
          <li>The browser captures webcam frames from the user.</li>
          <li>Frames are encoded as JPEG and sent to the FastAPI WebSocket every 100 ms.</li>
          <li>The backend extracts MediaPipe hand landmarks and predicts the gesture label.</li>
          <li>The UI applies a 15-frame stability threshold before committing the sign.</li>
          <li>The committed text appears in the sentence buffer and can be spoken aloud.</li>
        </ol>
      </section>

      <section className="panel info-panel">
        <p className="eyebrow">Tech stack</p>
        <ul className="pill-list">
          <li>React 18</li>
          <li>Vite</li>
          <li>React Router v6</li>
          <li>FastAPI</li>
          <li>MediaPipe</li>
          <li>Web Speech API</li>
        </ul>
      </section>
    </div>
  );
}

export default About;