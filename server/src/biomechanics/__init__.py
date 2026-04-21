"""Utilitários de biomecânica derivados dos keypoints COCO.

Cada módulo aqui implementa um cálculo isolado e testável que será
acoplado ao pipeline de pose (`server.src.video_pipeline.run_pipeline`)
pelas histórias de cálculo (US-007 em diante).
"""

from server.src.biomechanics.cotovelo import (
    KP_COTOVELO_DIR,
    KP_COTOVELO_ESQ,
    KP_OMBRO_DIR,
    KP_OMBRO_ESQ,
    KP_PULSO_DIR,
    KP_PULSO_ESQ,
    AnguloCotoveloLado,
    AnguloCotoveloResultado,
    calcular_angulo_cotovelo,
)
from server.src.biomechanics.escala import (
    KP_NARIZ,
    KP_TORNOZELO_DIR,
    KP_TORNOZELO_ESQ,
    MSG_ALTURA_AUSENTE,
    MSG_SEM_FRAMES_VALIDOS,
    FatorEscala,
    calcular_fator_escala,
)
from server.src.biomechanics.joelho import (
    KP_JOELHO_DIR,
    KP_JOELHO_ESQ,
    KP_QUADRIL_DIR,
    KP_QUADRIL_ESQ,
    AnguloJoelhoContatoInicial,
    AnguloJoelhoLado,
    calcular_angulo_joelho_contato_inicial,
)

__all__ = [
    "KP_COTOVELO_DIR",
    "KP_COTOVELO_ESQ",
    "KP_JOELHO_DIR",
    "KP_JOELHO_ESQ",
    "KP_NARIZ",
    "KP_OMBRO_DIR",
    "KP_OMBRO_ESQ",
    "KP_PULSO_DIR",
    "KP_PULSO_ESQ",
    "KP_QUADRIL_DIR",
    "KP_QUADRIL_ESQ",
    "KP_TORNOZELO_DIR",
    "KP_TORNOZELO_ESQ",
    "MSG_ALTURA_AUSENTE",
    "MSG_SEM_FRAMES_VALIDOS",
    "AnguloCotoveloLado",
    "AnguloCotoveloResultado",
    "AnguloJoelhoContatoInicial",
    "AnguloJoelhoLado",
    "FatorEscala",
    "calcular_angulo_cotovelo",
    "calcular_angulo_joelho_contato_inicial",
    "calcular_fator_escala",
]
