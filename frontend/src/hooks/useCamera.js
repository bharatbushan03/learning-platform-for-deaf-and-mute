import { useCallback, useEffect, useRef } from 'react';

function useCamera() {
  const videoRef = useRef(null);
  const captureCanvasRef = useRef(null);

  const startCamera = useCallback(async () => {
    if (!videoRef.current) {
      return;
    }

    const stream = await navigator.mediaDevices.getUserMedia({
      video: { width: 640, height: 480, facingMode: 'user' },
      audio: false,
    });

    videoRef.current.srcObject = stream;
    await videoRef.current.play();
  }, []);

  const stopCamera = useCallback(() => {
    const stream = videoRef.current?.srcObject;
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
  }, []);

  const captureFrame = useCallback(async () => {
    const video = videoRef.current;
    if (!video || !video.videoWidth || !video.videoHeight) {
      return null;
    }

    if (!captureCanvasRef.current) {
      captureCanvasRef.current = document.createElement('canvas');
    }

    const canvas = captureCanvasRef.current;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const context = canvas.getContext('2d');
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL('image/jpeg', 0.8).split(',')[1];
  }, []);

  useEffect(() => () => stopCamera(), [stopCamera]);

  return { videoRef, startCamera, stopCamera, captureFrame };
}

export default useCamera;