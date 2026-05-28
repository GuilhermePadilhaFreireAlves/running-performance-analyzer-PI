"""Shared initial-contact detection helpers."""

from __future__ import annotations

from typing import Sequence

from server.src.video_pipeline import FrameKeypoints


def ankle_y(frame: FrameKeypoints, idx: int) -> float | None:
    if idx >= len(frame.keypoints):
        return None

    keypoint = frame.keypoints[idx]
    if keypoint is None:
        return None

    return keypoint[1]


def find_initial_contact_indices(
    frames: Sequence[FrameKeypoints],
    tornozelo_idx: int,
) -> list[int]:
    """Find strict local Y peaks for an ankle keypoint, ignoring border frames."""
    peaks: list[int] = []
    for i in range(1, len(frames) - 1):
        cur = ankle_y(frames[i], tornozelo_idx)
        prev_ = ankle_y(frames[i - 1], tornozelo_idx)
        nxt = ankle_y(frames[i + 1], tornozelo_idx)

        if cur is None or prev_ is None or nxt is None:
            continue

        if cur > prev_ and cur > nxt:
            peaks.append(i)

    return peaks
