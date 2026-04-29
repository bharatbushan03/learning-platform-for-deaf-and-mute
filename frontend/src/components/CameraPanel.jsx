import React from 'react';

function CameraPanel({ videoRef, isCameraOn, isDetecting, fps, toggleCamera, toggleDetection }) {
  return (
    <section className="panel camera-panel">
      <div className="panel-label">Live Feed</div>
      <div className="camera-wrap">
        <video ref={videoRef} autoPlay playsInline muted className="camera-video" style={{ display: isCameraOn ? 'block' : 'none' }} />
        <div className="camera-placeholder" style={{ display: isCameraOn ? 'none' : 'flex' }}>
          <div className="placeholder-icon">
            <svg viewBox="0 0 24 24" aria-hidden="true"><rect x="2" y="7" width="20" height="15" rx="2" /><path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2" /><circle cx="12" cy="14" r="3" /></svg>
          </div>
          <p>Press Start to activate the camera</p>
        </div>
      </div>
      <div className="panel-footer camera-footer">
        <button className={`btn btn-primary ${isCameraOn ? 'danger' : ''}`} type="button" onClick={toggleCamera}>
          {isCameraOn ? 'Stop' : 'Start'}
        </button>
        <button className={`btn btn-ghost ${isDetecting ? 'active' : ''}`} type="button" disabled={!isCameraOn} onClick={toggleDetection}>
          {isDetecting ? 'Detect On' : 'Detect Off'}
        </button>
        <span className="fps-label">{isCameraOn ? `${fps} fps` : '—'}</span>
      </div>
    </section>
  );
}

export default CameraPanel;