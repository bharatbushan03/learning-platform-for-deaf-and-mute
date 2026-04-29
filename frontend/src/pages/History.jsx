import React, { useEffect, useMemo, useState } from 'react';
import { HISTORY_STORAGE_KEY } from '../App';

function History() {
  const [items, setItems] = useState([]);

  useEffect(() => {
    try {
      const parsed = JSON.parse(localStorage.getItem(HISTORY_STORAGE_KEY) || '[]');
      setItems(Array.isArray(parsed) ? parsed : []);
    } catch {
      setItems([]);
    }
  }, []);

  const formattedItems = useMemo(() => items.slice(0, 50), [items]);

  function clearHistory() {
    localStorage.removeItem(HISTORY_STORAGE_KEY);
    setItems([]);
  }

  return (
    <div className="page page-info">
      <section className="panel info-panel history-header">
        <div>
          <p className="eyebrow">Prediction history</p>
          <h2>Last 50 committed predictions</h2>
        </div>
        <button type="button" className="btn btn-ghost danger" onClick={clearHistory}>Clear history</button>
      </section>

      <section className="panel history-panel">
        {formattedItems.length ? (
          <div className="history-list">
            {formattedItems.map((item, index) => (
              <article key={`${item.timestamp}-${index}`} className="history-item">
                <div>
                  <p className="history-prediction">{item.prediction}</p>
                  <p className="history-meta">Confidence: {item.confidence}%</p>
                </div>
                <time className="history-time">{new Date(item.timestamp).toLocaleString()}</time>
              </article>
            ))}
          </div>
        ) : (
          <div className="empty-state">
            <h3>No predictions yet</h3>
            <p>Committed gestures will appear here after the stability threshold is reached.</p>
          </div>
        )}
      </section>
    </div>
  );
}

export default History;