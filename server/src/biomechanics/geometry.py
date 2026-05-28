"""Shared geometry helpers for biomechanics metrics."""

from __future__ import annotations

from math import acos, degrees, hypot

Point2D = tuple[float, float]


def angulo_interno(a: Point2D, b: Point2D, c: Point2D) -> float | None:
    """Angle at ``b`` between vectors ``b -> a`` and ``b -> c``, in degrees."""
    v1x, v1y = a[0] - b[0], a[1] - b[1]
    v2x, v2y = c[0] - b[0], c[1] - b[1]
    mag1 = hypot(v1x, v1y)
    mag2 = hypot(v2x, v2y)
    if mag1 == 0 or mag2 == 0:
        return None

    cos_theta = (v1x * v2x + v1y * v2y) / (mag1 * mag2)
    if cos_theta > 1.0:
        cos_theta = 1.0
    elif cos_theta < -1.0:
        cos_theta = -1.0

    return degrees(acos(cos_theta))
