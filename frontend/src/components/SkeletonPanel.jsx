import React from 'react';

function SkeletonPanel({ canvasRef, confidence, hasLandmarks }) {
  return (
    <section className="panel">
      <div className="panel-label">Hand Skeleton</div>
      <div className="skeleton-wrap">
        <canvas ref={canvasRef} className="skeleton-canvas" />
        {!hasLandmarks ? (
          <div className="skeleton-empty">
            <svg width="100" height="110" viewBox="0 0 100 110" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
              <path d="M50 90 C30 90 18 75 18 58 L18 38 C18 34 21 31 25 31 C29 31 32 34 32 38 L32 55" stroke="#1a1814" strokeWidth="3" strokeLinecap="round" />
              <path d="M32 38 L32 22 C32 18 35 15 39 15 C43 15 46 18 46 22 L46 38" stroke="#1a1814" strokeWidth="3" strokeLinecap="round" />
              <path d="M46 38 L46 18 C46 14 49 11 53 11 C57 11 60 14 60 18 L60 38" stroke="#1a1814" strokeWidth="3" strokeLinecap="round" />
              <path d="M60 38 L60 22 C60 18 63 15 67 15 C71 15 74 18 74 22 L74 38" stroke="#1a1814" strokeWidth="3" strokeLinecap="round" />
              <path d="M74 38 L74 34 C74 30 77 28 80 29 C83 30 84 33 84 37 L82 55" stroke="#1a1814" strokeWidth="3" strokeLinecap="round" />
              <path d="M18 58 C18 75 30 90 50 90 C70 90 82 75 82 55" stroke="#1a1814" strokeWidth="3" strokeLinecap="round" />
            </svg>
            <p>Waiting for hand detection...</p>
          </div>
        ) : null}
      </div>
      <div className="panel-footer skeleton-footer">
        <div className="confidence-track">
          <span>CONF</span>
          <div className="confidence-bar"><div className="confidence-fill" style={{ width: `${confidence}%` }} /></div>
          <span className="confidence-value">{hasLandmarks ? `${confidence}%` : '—'}</span>
        </div>
      </div>
    </section>
  );
}

export default SkeletonPanel;