# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A real-time Indian Sign Language (ISL) recognition platform that uses computer vision and machine learning to translate hand gestures into text. The system captures hand landmarks via MediaPipe, classifies gestures using a trained model, and displays recognized signs in real-time.

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│   Webcam    │ ──> │ MediaPipe Hands  │ ──> │ 63 features │
│   (OpenCV)  │     │ (Landmark Detect)│     │ (x,y,z x21) │
└─────────────┘     └──────────────────┘     └──────┬──────┘
                                                    │
                                                    ▼
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│  Display    │ <── │  Label Encoder   │ <── │  ISL Model  │
│  (OpenCV)   │     │  (Decode output) │     │  (sklearn)  │
└─────────────┘     └──────────────────┘     └─────────────┘
```

## Key Components

- **demo.py** - Main real-time prediction script using webcam feed
- **data-generation.py** - Extracts hand landmarks from dataset images to build training data
- **isl_realtime_prediction.py** - Standalone prediction script (alternative entry point)
- **models/** - Contains trained ML model (`isl-model.pkl`), label encoder (`label-encoder.pkl`), and MediaPipe task file (`hand_landmarker.task`)
- **Indian/** - Dataset folder with sign language images organized by label subdirectories

## Commands

**Run real-time prediction:**
```bash
python demo.py
```
- Requires webcam access
- Controls: `SPACE` = clear buffer, `Q` = quit
- Displays detected signs with confidence scores and stability tracking

**Generate training dataset:**
```bash
python data-generation.py
```
- Processes images in `Indian/` folder
- Outputs `data.csv` with 63 landmark features per image

**Test webcam/hand tracking only:**
```bash
python isl_realtime_prediction.py
```
- Downloads MediaPipe model if missing
- Visualizes hand landmarks without classification

## Dependencies

Core stack: `opencv-python`, `mediapipe`, `numpy`, `scikit-learn` (pickle-compatible)

Model files are version-sensitive - ensure `.pkl` files match the scikit-learn version used during training.

## Data Flow

1. **Landmark extraction**: 21 hand landmarks × 3 coordinates (x, y, z) = 63 features per frame
2. **Classification**: sklearn model predicts encoded label from 63-feature vector
3. **Decoding**: LabelEncoder transforms prediction back to sign name
4. **Stability filter**: Sign must be consistent for 15 frames before adding to output buffer