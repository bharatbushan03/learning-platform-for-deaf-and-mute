# learning-platform-for-deaf-and-mute

Real-time Indian Sign Language (ISL) recognition project for deaf and mute communication support.

## React UI

The production frontend lives in `frontend/` as a Vite + React application.

### Run the frontend

```bash
cd frontend
npm install
npm run dev
```

### Build for production

```bash
cd frontend
npm run build
```

The FastAPI backend serves the built app from `frontend/dist/` when present.

## Backend

```bash
uvicorn backend.main:app --reload
```

## Real-Time Prediction

The project provides standalone scripts for real-time ISL recognition via webcam.

## Existing scripts

- `python demo.py` → main OpenCV real-time prediction flow
- `python isl_realtime_prediction.py` → standalone webcam/hand-tracking entry point
