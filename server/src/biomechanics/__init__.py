"""Utilitários de biomecânica derivados dos keypoints COCO.

Cada módulo aqui implementa um cálculo isolado e testável que será
acoplado ao pipeline de pose (`server.src.video_pipeline.run_pipeline`)
pelas histórias de cálculo (US-007 em diante).
"""

from server.src.biomechanics.escala import (
    KP_NARIZ,
    KP_TORNOZELO_DIR,
    KP_TORNOZELO_ESQ,
    MSG_ALTURA_AUSENTE,
    MSG_SEM_FRAMES_VALIDOS,
    FatorEscala,
    calcular_fator_escala,
)

__all__ = [
    "KP_NARIZ",
    "KP_TORNOZELO_DIR",
    "KP_TORNOZELO_ESQ",
    "MSG_ALTURA_AUSENTE",
    "MSG_SEM_FRAMES_VALIDOS",
    "FatorEscala",
    "calcular_fator_escala",
]
