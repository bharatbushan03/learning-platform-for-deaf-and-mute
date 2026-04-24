# learning-platform-for-deaf-and-mute

Real-time Indian Sign Language (ISL) recognition project for deaf and mute communication support.

## UI (Gradio)

A web UI is available via `app.py` for image/webcam-based sign prediction.

### Run

```bash
python app.py
```

Then open the local Gradio URL in your browser.

## Existing scripts

- `python demo.py` → webcam hand landmark tracking demo (landmark visualization only)
- `python isl_realtime_prediction.py` → OpenCV real-time ISL prediction with buffering and confidence
