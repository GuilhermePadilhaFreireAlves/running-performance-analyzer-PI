"""Utilitários de biomecânica derivados dos keypoints COCO.

Cada módulo aqui implementa um cálculo isolado e testável que será
acoplado ao pipeline de pose (`server.src.video_pipeline.run_pipeline`)
pelas histórias de cálculo (US-007 em diante).
"""

from server.src.biomechanics.cadencia import (
    MSG_FPS_INVALIDO,
    Cadencia,
    calcular_cadencia,
)
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
from server.src.biomechanics.oscilacao import (
    OscilacaoVertical,
    OscilacaoVerticalPorLado,
    calcular_oscilacao_vertical,
    calcular_oscilacao_vertical_por_lado,
)
from server.src.biomechanics.overstriding import (
    OverstridingLado,
    OverstridingResultado,
    calcular_overstriding,
)
from server.src.biomechanics.simetria import (
    SimetriaResultado,
    calcular_simetria,
    indice_simetria,
)
from server.src.biomechanics.tcs import (
    TcsLado,
    TcsResultado,
    calcular_tcs,
)
from server.src.biomechanics.tronco import (
    FLEXAO_APOIO_MEDIO_MAX_GRAUS,
    FLEXAO_APOIO_MEDIO_MIN_GRAUS,
    InclinacaoTronco,
    calcular_inclinacao_tronco,
)

__all__ = [
    "FLEXAO_APOIO_MEDIO_MAX_GRAUS",
    "FLEXAO_APOIO_MEDIO_MIN_GRAUS",
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
    "MSG_FPS_INVALIDO",
    "MSG_SEM_FRAMES_VALIDOS",
    "AnguloCotoveloLado",
    "AnguloCotoveloResultado",
    "AnguloJoelhoContatoInicial",
    "AnguloJoelhoLado",
    "Cadencia",
    "FatorEscala",
    "InclinacaoTronco",
    "OscilacaoVertical",
    "OscilacaoVerticalPorLado",
    "OverstridingLado",
    "OverstridingResultado",
    "SimetriaResultado",
    "TcsLado",
    "TcsResultado",
    "calcular_angulo_cotovelo",
    "calcular_angulo_joelho_contato_inicial",
    "calcular_cadencia",
    "calcular_fator_escala",
    "calcular_inclinacao_tronco",
    "calcular_oscilacao_vertical",
    "calcular_oscilacao_vertical_por_lado",
    "calcular_overstriding",
    "calcular_simetria",
    "calcular_tcs",
    "indice_simetria",
]
