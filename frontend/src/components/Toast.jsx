import React, { useEffect } from 'react';

function Toast({ items, onDismiss }) {
  useEffect(() => {
    if (!items.length) {
      return undefined;
    }

    const timers = items.map((item) => setTimeout(() => onDismiss(item.id), 2400));
    return () => timers.forEach(clearTimeout);
  }, [items, onDismiss]);

  return (
    <div className="toast-stack" aria-live="polite" aria-atomic="true">
      {items.map((item) => (
        <div key={item.id} className="toast-item">{item.message}</div>
      ))}
    </div>
  );
}

export default Toast;