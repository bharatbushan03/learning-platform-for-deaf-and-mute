import React from 'react';

function Header({ connectionStatus }) {
  return (
    <header className="hero-header">
      <div>
        <p className="eyebrow">Indian Sign Language</p>
        <h1>Real-time recognition for accessible communication</h1>
        <p className="hero-copy">Live webcam inference with WebSocket streaming, gesture stability tracking, and sentence building.</p>
      </div>
      <div className="status-pill">
        <span className="status-dot live" />
        <span>{connectionStatus}</span>
      </div>
    </header>
  );
}

export default Header;