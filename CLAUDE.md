# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project purpose

Video-based running gait analyzer. A YOLO pose model extracts COCO keypoints from a runner's video; the scripts derive joint angles (elbows, knees, hips), trunk inclination, and cadence (step count / elapsed time).

The codebase is early-stage — several files (`calculator.py`, `pose_detector.py`, `processing/data/__init__.py`) are empty stubs reserved for future refactoring. Real logic currently lives only in `processing/src/mainYolo.py` and `processing/src/mainGraph.py`, and the FastAPI `server/` is a hello-world stub.

## Commands

Setup (from repo root):
```
python -m venv venv
venv\Scripts\activate        # Windows (this is the primary dev platform)
source venv/bin/activate     # Linux/macOS
pip install -r requirements.txt
```

Run the analyzer (scripts must be launched from repo root — paths are relative to CWD):
```
python processing/src/mainYolo.py    # console output only
python processing/src/mainGraph.py   # console + saves grafico_*.png in CWD
```

Run the API stub:
```
uvicorn server.src.main:app --reload
```

There are no tests, linter config, or build step yet.

## Required runtime assets (not in git)

Both analysis scripts hardcode two paths that must exist relative to the working directory when launched:

- `yolo26x-pose.pt` — Ultralytics YOLO pose weights (~126 MB). Present at repo root locally but untracked; do not commit.
- `./run/profissional.mp4` — input video. The `run/` directory is not checked in; create it and drop a video named `profissional.mp4` before running, or edit the `source=` argument.

`yolo26n.pt` is also present at the root but unused by the current scripts.

## Architecture notes

**Two scripts, one pipeline, duplicated.** `mainYolo.py` and `mainGraph.py` share the same structure: `KEYPOINT_DICT` (COCO index map), `calcular_angulo(a, b, c)` (signed-to-unsigned angle via `atan2` difference), a YOLO streaming predict loop, per-frame angle extraction, and cadence counting. `mainGraph.py` additionally accumulates per-frame values into `dados_analise` and emits three matplotlib PNGs at the end. When changing the biomechanics logic, edit **both** files or the scripts will diverge.

**Knee flexion convention.** The scripts compute the *internal* hip–knee–ankle angle, then report `180 - internal` as "flexão". A straight leg reports ~0°, a bent leg a larger positive number. This is deliberate (see commit `9d3350c fix: recalculating knee angles`) — don't "fix" it back to the raw internal angle.

**Cadence state machine.** Each leg has a `perna_*_em_flexao` boolean. A step is counted on the rising edge when the knee flexion crosses `ANGULO_FLEXAO_JOELHO_LIMIAR = 30°`; the flag resets when it drops back under. Cadence = `passos_contados / elapsed_seconds * 60`. Note `tempo_inicio` is wall-clock from script start, which includes YOLO model load time — the reported cadence is approximate, not precise BPM.

**Keypoint validity check.** The scripts gate every calculation on `pontos[name][0] > 0` (x-coordinate non-zero) as a proxy for "keypoint detected." Ultralytics returns `(0, 0)` for missing keypoints, so this is the intended guard — keep it when adding new derived metrics.

**Language.** Variable names, comments, and print output are in Portuguese (`angulo`, `joelho`, `quadril`, `passos`, `cadencia`). Match that style when extending these files.
