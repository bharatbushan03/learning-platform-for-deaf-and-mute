const CONNECTIONS = [
  [0, 1], [1, 2], [2, 3], [3, 4],
  [0, 5], [5, 6], [6, 7], [7, 8],
  [0, 9], [9, 10], [10, 11], [11, 12],
  [0, 13], [13, 14], [14, 15], [15, 16],
  [0, 17], [17, 18], [18, 19], [19, 20],
  [5, 9], [9, 13], [13, 17],
];

export function clearSkeleton(canvas) {
  if (!canvas) {
    return;
  }
  const context = canvas.getContext('2d');
  context.clearRect(0, 0, canvas.width, canvas.height);
}

export function drawSkeleton(canvas, landmarks = []) {
  if (!canvas) {
    return;
  }

  const context = canvas.getContext('2d');
  const width = canvas.width;
  const height = canvas.height;

  context.clearRect(0, 0, width, height);

  if (!landmarks.length) {
    return;
  }

  const hands = Array.isArray(landmarks[0]?.points) ? landmarks : [{ handedness: 'Unknown', points: landmarks }];

  hands.forEach((hand) => {
    const handedness = String(hand.handedness || hand.points?.[0]?.hand || 'Right').toLowerCase();
    const isLeft = handedness.includes('left');
    const pointColor = isLeft ? '#1e88ff' : '#e63946';
    const lineColor = isLeft ? '#f472b6' : '#00bcd4';
    const points = hand.points || [];

    context.lineCap = 'round';
    context.lineJoin = 'round';
    context.lineWidth = 2.5;
    context.strokeStyle = lineColor;
    context.fillStyle = pointColor;

    CONNECTIONS.forEach(([startIndex, endIndex]) => {
      const start = points[startIndex];
      const end = points[endIndex];
      if (!start || !end) {
        return;
      }

      context.beginPath();
      context.moveTo(start.x, start.y);
      context.lineTo(end.x, end.y);
      context.stroke();
    });

    points.forEach((point, index) => {
      context.beginPath();
      context.arc(point.x, point.y, index === 0 ? 7 : 4, 0, Math.PI * 2);
      context.fillStyle = pointColor;
      context.fill();
      context.strokeStyle = '#ffffff';
      context.lineWidth = 1.5;
      context.stroke();
    });
  });
}

export { CONNECTIONS };