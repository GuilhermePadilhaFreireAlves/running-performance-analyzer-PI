from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable, Optional, Protocol

from sqlalchemy.orm import Session

from server.src.database import SessionLocal
from server.src.models.sessao_analise import SessaoAnalise

logger = logging.getLogger(__name__)

FPS_MINIMO = 60.0
PACE_MIN = 3.0
PACE_MAX = 12.0
RAZAO_LATERAL_MAXIMA = 0.30
PERSPECTIVA_FRAMES_AMOSTRA = 5

NUM_KEYPOINTS = 17
KEYPOINT_SCORE_THRESHOLD = 0.5
LOW_QUALITY_KP_THRESHOLD = NUM_KEYPOINTS // 2 + 1  # 9: maioria de 17
LOW_QUALITY_FRAME_RATIO_MAX = 0.5
MULTI_PERSON_FRAME_RATIO_MAX = 0.3
SMOOTHING_WINDOW = 5

MSG_FPS_INSUFICIENTE = (
    "FPS do vídeo insuficiente — grave com pelo menos 60 FPS para garantir "
    "precisão na análise"
)
MSG_PERSPECTIVA_INVALIDA = (
    "Perspectiva inválida — grave o vídeo de lado (perfil), perpendicular à "
    "direção da corrida"
)
MSG_PACE_INVALIDO = (
    "Pace fora do intervalo permitido — informe um valor entre 3:00 e 12:00 min/km"
)


Keypoint = Optional[tuple[float, float, float]]


@dataclass
class FrameKeypoints:
    """Keypoints de um único frame após filtragem por score.

    `keypoints[k]` é `None` quando o score do keypoint k ficou abaixo de
    `KEYPOINT_SCORE_THRESHOLD` (ou não foi detectado).
    """

    frame_idx: int
    person_count: int
    keypoints: list[Keypoint] = field(default_factory=list)


@dataclass
class PoseExtractionResult:
    fps: float
    total_frames: int
    frames: list[FrameKeypoints]
    low_quality_frames: int
    multi_person_frames: int


class VideoValidator(Protocol):
    def extract_fps(self, video_path: str) -> float: ...
    def is_lateral(self, video_path: str) -> bool: ...


class PoseExtractor(Protocol):
    def extract_keypoints(self, video_path: str) -> PoseExtractionResult: ...


@dataclass
class DefaultVideoValidator:
    """Production validator using OpenCV (FPS) and YOLOv8-pose (perspective).

    The YOLO model is loaded lazily so that environments without model weights
    (e.g. unit tests that override this dependency) do not pay the import cost.
    """

    model_path: str | None = None

    def extract_fps(self, video_path: str) -> float:
        import cv2

        cap = cv2.VideoCapture(video_path)
        try:
            if not cap.isOpened():
                return 0.0
            fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
        finally:
            cap.release()
        return fps

    def is_lateral(self, video_path: str) -> bool:
        import cv2

        cap = cv2.VideoCapture(video_path)
        try:
            if not cap.isOpened():
                return False
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
            if total_frames <= 0:
                return False
            sample_indices = _sample_indices(total_frames, PERSPECTIVA_FRAMES_AMOSTRA)
            frames = []
            for idx in sample_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ok, frame = cap.read()
                if ok and frame is not None:
                    frames.append(frame)
        finally:
            cap.release()

        if not frames:
            return False

        model = _load_yolo_model(self.model_path)
        if model is None:
            return False

        ratios: list[float] = []
        for frame in frames:
            ratio = _shoulder_hip_ratio(model, frame)
            if ratio is not None:
                ratios.append(ratio)

        if not ratios:
            return False
        ratios.sort()
        median = ratios[len(ratios) // 2]
        return median < RAZAO_LATERAL_MAXIMA


@dataclass
class DefaultPoseExtractor:
    """Extrai keypoints COCO com YOLOv8-pose, frame a frame.

    cv2 e ultralytics são importados preguiçosamente para manter o módulo
    importável em ambientes sem essas dependências carregadas.
    """

    model_path: str | None = None

    def extract_keypoints(self, video_path: str) -> PoseExtractionResult:
        import cv2

        model = _load_yolo_model(self.model_path)
        if model is None:
            raise RuntimeError("Modelo YOLO-pose indisponível")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            cap.release()
            raise RuntimeError(f"Não foi possível abrir o vídeo: {video_path}")

        try:
            fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
            raw_frames: list[FrameKeypoints] = []
            frame_idx = 0
            while True:
                ok, frame = cap.read()
                if not ok or frame is None:
                    break
                raw_frames.append(_predict_frame_keypoints(model, frame, frame_idx))
                # libera o frame bruto imediatamente para evitar segurá-lo na memória
                del frame
                frame_idx += 1
        finally:
            cap.release()

        smoothed = smooth_frames(raw_frames, window=SMOOTHING_WINDOW)
        low_quality = sum(1 for f in smoothed if _frame_is_low_quality(f))
        multi_person = sum(1 for f in smoothed if f.person_count > 1)

        return PoseExtractionResult(
            fps=fps,
            total_frames=total_frames or len(smoothed),
            frames=smoothed,
            low_quality_frames=low_quality,
            multi_person_frames=multi_person,
        )


def _sample_indices(total: int, n: int) -> list[int]:
    if total <= n:
        return list(range(total))
    step = total / (n + 1)
    return [int(step * (i + 1)) for i in range(n)]


def _load_yolo_model(model_path: str | None) -> object | None:
    path = model_path or os.environ.get("YOLO_POSE_MODEL", "yolo26x-pose.pt")
    if not Path(path).exists():
        logger.warning("Modelo YOLO não encontrado em %s", path)
        return None
    try:
        from ultralytics import YOLO
    except ImportError:
        logger.warning("Ultralytics não instalado")
        return None
    return YOLO(path)


def _shoulder_hip_ratio(model: object, frame: object) -> float | None:
    """Retorna max(shoulder_width, hip_width) / torso_height para a pose no frame.

    Retorna None quando os keypoints requeridos estão ausentes. Razão mais baixa
    ⇒ mais próximo de uma tomada realmente lateral (perfil).
    """
    predict = getattr(model, "predict", None)
    if predict is None:
        return None
    results = predict(source=frame, verbose=False)
    if not results:
        return None
    kpts_obj = getattr(results[0], "keypoints", None)
    if kpts_obj is None:
        return None
    xy = getattr(kpts_obj, "xy", None)
    if xy is None or len(xy) == 0:
        return None
    pontos = xy[0]
    try:
        ls = pontos[5]
        rs = pontos[6]
        lh = pontos[11]
        rh = pontos[12]
    except (IndexError, KeyError):
        return None

    if min(float(ls[0]), float(rs[0]), float(lh[0]), float(rh[0])) <= 0:
        return None

    shoulder_width = abs(float(rs[0]) - float(ls[0]))
    hip_width = abs(float(rh[0]) - float(lh[0]))
    shoulder_mid_y = (float(ls[1]) + float(rs[1])) / 2
    hip_mid_y = (float(lh[1]) + float(rh[1])) / 2
    torso_height = abs(hip_mid_y - shoulder_mid_y)
    if torso_height <= 0:
        return None
    return max(shoulder_width, hip_width) / torso_height


def _predict_frame_keypoints(
    model: object, frame: object, frame_idx: int
) -> FrameKeypoints:
    """Roda YOLO-pose no frame e monta os 17 keypoints COCO filtrados por score."""
    predict = getattr(model, "predict", None)
    if predict is None:
        return FrameKeypoints(
            frame_idx=frame_idx,
            person_count=0,
            keypoints=[None] * NUM_KEYPOINTS,
        )
    results = predict(source=frame, verbose=False)
    if not results:
        return FrameKeypoints(
            frame_idx=frame_idx,
            person_count=0,
            keypoints=[None] * NUM_KEYPOINTS,
        )
    kpts_obj = getattr(results[0], "keypoints", None)
    if kpts_obj is None:
        return FrameKeypoints(
            frame_idx=frame_idx,
            person_count=0,
            keypoints=[None] * NUM_KEYPOINTS,
        )

    xy = getattr(kpts_obj, "xy", None)
    conf = getattr(kpts_obj, "conf", None)
    if xy is None or len(xy) == 0:
        return FrameKeypoints(
            frame_idx=frame_idx,
            person_count=0,
            keypoints=[None] * NUM_KEYPOINTS,
        )

    person_count = int(len(xy))
    pessoa_xy = xy[0]
    pessoa_conf = conf[0] if conf is not None and len(conf) > 0 else None

    keypoints: list[Keypoint] = []
    for k in range(NUM_KEYPOINTS):
        try:
            point = pessoa_xy[k]
            x = float(point[0])
            y = float(point[1])
        except (IndexError, TypeError, ValueError):
            keypoints.append(None)
            continue
        score = _coerce_score(pessoa_conf, k)
        if score is None or score < KEYPOINT_SCORE_THRESHOLD:
            keypoints.append(None)
        else:
            keypoints.append((x, y, score))
    return FrameKeypoints(
        frame_idx=frame_idx,
        person_count=person_count,
        keypoints=keypoints,
    )


def _coerce_score(conf_row: object, k: int) -> float | None:
    if conf_row is None:
        return None
    try:
        return float(conf_row[k])  # type: ignore[index]
    except (IndexError, TypeError, ValueError):
        return None


def smooth_frames(
    frames: list[FrameKeypoints], window: int = SMOOTHING_WINDOW
) -> list[FrameKeypoints]:
    """Aplica média móvel por keypoint nas coordenadas x,y ao longo dos frames.

    Keypoints cujo valor atual é None permanecem None (não interpolamos frames
    descartados). Para keypoints válidos, a coordenada suavizada é a média dos
    valores válidos dentro de uma janela de tamanho `window` centrada no frame.
    """
    n = len(frames)
    if n == 0 or window <= 1:
        return list(frames)
    half = window // 2
    out: list[FrameKeypoints] = []
    for i in range(n):
        cur_frame = frames[i]
        kp_out: list[Keypoint] = []
        for k in range(NUM_KEYPOINTS):
            cur = cur_frame.keypoints[k] if k < len(cur_frame.keypoints) else None
            if cur is None:
                kp_out.append(None)
                continue
            xs: list[float] = []
            ys: list[float] = []
            for j in range(max(0, i - half), min(n, i + half + 1)):
                neighbor = frames[j].keypoints[k] if k < len(frames[j].keypoints) else None
                if neighbor is not None:
                    xs.append(neighbor[0])
                    ys.append(neighbor[1])
            if xs:
                x = sum(xs) / len(xs)
                y = sum(ys) / len(ys)
                kp_out.append((x, y, cur[2]))
            else:
                kp_out.append(cur)
        out.append(
            FrameKeypoints(
                frame_idx=cur_frame.frame_idx,
                person_count=cur_frame.person_count,
                keypoints=kp_out,
            )
        )
    return out


def _frame_is_low_quality(frame: FrameKeypoints) -> bool:
    invalid = sum(1 for kp in frame.keypoints if kp is None)
    # completa com None quando faltam slots (defensivo)
    invalid += max(0, NUM_KEYPOINTS - len(frame.keypoints))
    return invalid >= LOW_QUALITY_KP_THRESHOLD


_default_validator: VideoValidator = DefaultVideoValidator()
_default_pose_extractor: PoseExtractor = DefaultPoseExtractor()


def get_video_validator() -> VideoValidator:
    return _default_validator


def get_pose_extractor() -> PoseExtractor:
    return _default_pose_extractor


def is_pace_valido(pace_min_km: float) -> bool:
    return PACE_MIN <= pace_min_km <= PACE_MAX


SessionFactory = Callable[[], Session]


def run_pipeline(
    sessao_id: int,
    video_path: str,
    *,
    extractor: PoseExtractor | None = None,
    session_factory: SessionFactory | None = None,
    delete_video: bool = True,
) -> None:
    """Pipeline de pose/biomecânica em background (US-006+).

    Etapas implementadas por US-006:
      1. status ← 'detectando_pose'
      2. Extrai keypoints frame a frame, filtra por score (<0.5 → None),
         aplica média móvel.
      3. Persiste FPS na sessão.
      4. Se >30% dos frames têm múltiplas pessoas → erro_multiplas_pessoas.
      5. Se >50% dos frames têm maioria de keypoints inválidos → erro_qualidade_keypoints.
      6. Caso contrário, status ← 'calculando_metricas' (etapas posteriores em
         histórias futuras).
    """
    pose_extractor = extractor or get_pose_extractor()
    factory: SessionFactory = session_factory or SessionLocal

    session: Session = factory()
    try:
        sessao = session.get(SessaoAnalise, sessao_id)
        if sessao is None:
            logger.warning("Sessão %s não encontrada; pipeline abortado.", sessao_id)
            return

        sessao.status = "detectando_pose"
        session.commit()

        try:
            result = pose_extractor.extract_keypoints(video_path)
        except Exception:
            logger.exception(
                "Falha na extração de keypoints para sessão %s", sessao_id
            )
            sessao.status = "erro_qualidade_keypoints"
            session.commit()
            return

        sessao.fps = result.fps

        total = len(result.frames)
        if total == 0:
            sessao.status = "erro_qualidade_keypoints"
            session.commit()
            return

        multi_ratio = result.multi_person_frames / total
        if multi_ratio > MULTI_PERSON_FRAME_RATIO_MAX:
            sessao.status = "erro_multiplas_pessoas"
            session.commit()
            return

        low_quality_ratio = result.low_quality_frames / total
        if low_quality_ratio > LOW_QUALITY_FRAME_RATIO_MAX:
            sessao.status = "erro_qualidade_keypoints"
            session.commit()
            return

        sessao.status = "calculando_metricas"
        session.commit()
        logger.info(
            "Pipeline US-006 OK para sessão %s (fps=%s, frames=%s).",
            sessao_id,
            result.fps,
            total,
        )

        _persistir_angulos_joelho(session, sessao_id, result.frames)
        _persistir_angulos_cotovelo(session, sessao_id, result.frames)
        _persistir_cadencia(session, sessao_id, result.frames, result.fps)
        _persistir_inclinacao_tronco(session, sessao_id, result.frames)
        altura_cm = (
            sessao.usuario.altura_cm if sessao.usuario is not None else None
        )
        _persistir_overstriding(session, sessao_id, result.frames, altura_cm)
        _persistir_tcs(session, sessao_id, result.frames, result.fps)
    finally:
        session.close()
        if delete_video:
            _safe_unlink(video_path)


def _persistir_angulos_joelho(
    session: Session, sessao_id: int, frames: list[FrameKeypoints]
) -> None:
    """Calcula e grava em METRICA o ângulo do joelho esq/dir no contato inicial.

    US-008: não grava o lado cujo cálculo não produz valor (nenhum ciclo
    com keypoints válidos). Não altera o status da sessão — a transição
    para `concluido` é responsabilidade de US-016 (gerador de recomendações).
    """
    from server.src.biomechanics.joelho import (
        calcular_angulo_joelho_contato_inicial,
    )
    from server.src.models.metrica import Metrica

    resultado = calcular_angulo_joelho_contato_inicial(frames)
    if resultado.esquerdo is not None:
        session.add(
            Metrica(
                sessao_id=sessao_id,
                tipo="angulo_joelho_esq",
                valor=resultado.esquerdo.angulo_medio_graus,
                unidade="graus",
                apenas_informativa=False,
            )
        )
    if resultado.direito is not None:
        session.add(
            Metrica(
                sessao_id=sessao_id,
                tipo="angulo_joelho_dir",
                valor=resultado.direito.angulo_medio_graus,
                unidade="graus",
                apenas_informativa=False,
            )
        )
    session.commit()


def _persistir_angulos_cotovelo(
    session: Session, sessao_id: int, frames: list[FrameKeypoints]
) -> None:
    """Calcula e grava em METRICA o ângulo médio do cotovelo esq/dir.

    US-009: média sobre todos os frames válidos do vídeo. Não grava o lado
    cujo cálculo não produz valor (nenhum frame com os três keypoints do
    lado em questão). Não altera o status da sessão — a transição para
    `concluido` é responsabilidade de US-016.
    """
    from server.src.biomechanics.cotovelo import calcular_angulo_cotovelo
    from server.src.models.metrica import Metrica

    resultado = calcular_angulo_cotovelo(frames)
    if resultado.esquerdo is not None:
        session.add(
            Metrica(
                sessao_id=sessao_id,
                tipo="angulo_cotovelo_esq",
                valor=resultado.esquerdo.angulo_medio_graus,
                unidade="graus",
                apenas_informativa=False,
            )
        )
    if resultado.direito is not None:
        session.add(
            Metrica(
                sessao_id=sessao_id,
                tipo="angulo_cotovelo_dir",
                valor=resultado.direito.angulo_medio_graus,
                unidade="graus",
                apenas_informativa=False,
            )
        )
    session.commit()


def _persistir_cadencia(
    session: Session,
    sessao_id: int,
    frames: list[FrameKeypoints],
    fps: float,
) -> None:
    """Calcula e grava em METRICA a cadência (spm) do corredor.

    US-010: marcada como `apenas_informativa=True` — a cadência varia
    diretamente com o pace e, conforme o PRD, não deve penalizar a nota
    geral. Não grava quando o cálculo não produz valor (sem contatos
    detectados) e é no-op silenciosamente quando `fps <= 0`. Não altera
    o status da sessão — a transição para `concluido` é responsabilidade
    de US-016.
    """
    from server.src.biomechanics.cadencia import calcular_cadencia
    from server.src.models.metrica import Metrica

    if fps <= 0:
        return
    resultado = calcular_cadencia(frames, fps)
    if resultado is None:
        return
    session.add(
        Metrica(
            sessao_id=sessao_id,
            tipo="cadencia",
            valor=resultado.cadencia_spm,
            unidade="spm",
            apenas_informativa=True,
        )
    )
    session.commit()


def _persistir_inclinacao_tronco(
    session: Session, sessao_id: int, frames: list[FrameKeypoints]
) -> None:
    """Calcula e grava em METRICA a inclinação anterior do tronco.

    US-011: média sobre frames em fase de apoio médio (algum joelho com
    flexão em [40°, 45°]). Não grava nada quando não há frames qualificados.
    Não altera o status da sessão — a transição para `concluido` é
    responsabilidade de US-016.
    """
    from server.src.biomechanics.tronco import calcular_inclinacao_tronco
    from server.src.models.metrica import Metrica

    resultado = calcular_inclinacao_tronco(frames)
    if resultado is None:
        return
    session.add(
        Metrica(
            sessao_id=sessao_id,
            tipo="inclinacao_tronco",
            valor=resultado.inclinacao_media_graus,
            unidade="graus",
            apenas_informativa=False,
        )
    )
    session.commit()


def _persistir_overstriding(
    session: Session,
    sessao_id: int,
    frames: list[FrameKeypoints],
    altura_cm: float | None,
) -> None:
    """Calcula e grava em METRICA o overstriding (cm) esq/dir no contato inicial.

    US-012: converte `overstriding_px = tornozelo_X - CoM_X` para cm via
    `fator_escala` do usuário (US-007). `altura_cm` é a altura cadastrada
    do corredor (`Usuario.altura_cm`) e já é `NOT NULL` no modelo; o guard
    defensivo evita falhar o pipeline caso a coluna chegue aqui como `None`
    (testes, dados legados). Em qualquer falha do fator de escala
    (altura ausente ou nenhum frame válido para a altura em pixels) o passo
    é silencioso — o pipeline segue sem persistir overstriding. Não altera o
    status da sessão — transição para `concluido` é responsabilidade de
    US-016.
    """
    from server.src.biomechanics.escala import calcular_fator_escala
    from server.src.biomechanics.overstriding import calcular_overstriding
    from server.src.models.metrica import Metrica

    if altura_cm is None or altura_cm <= 0:
        return
    try:
        fator = calcular_fator_escala(frames, altura_cm).fator_escala
    except ValueError:
        return
    resultado = calcular_overstriding(frames, fator)
    if resultado.esquerdo is not None:
        session.add(
            Metrica(
                sessao_id=sessao_id,
                tipo="overstriding_esq",
                valor=resultado.esquerdo.overstriding_medio_cm,
                unidade="cm",
                apenas_informativa=False,
            )
        )
    if resultado.direito is not None:
        session.add(
            Metrica(
                sessao_id=sessao_id,
                tipo="overstriding_dir",
                valor=resultado.direito.overstriding_medio_cm,
                unidade="cm",
                apenas_informativa=False,
            )
        )
    session.commit()


def _persistir_tcs(
    session: Session,
    sessao_id: int,
    frames: list[FrameKeypoints],
    fps: float,
) -> None:
    """Calcula e grava em METRICA o TCS (ms) esq/dir do corredor.

    US-013: marcada como ``apenas_informativa=True`` — o valor absoluto de
    TCS varia com o pace e, conforme o PRD, não deve penalizar a nota
    geral (apenas a simetria penaliza). No-op silencioso para ``fps <= 0``
    ou para o lado sem ciclos de contato detectados. Não altera o status
    da sessão — a transição para ``concluido`` pertence a US-016.
    """
    from server.src.biomechanics.tcs import calcular_tcs
    from server.src.models.metrica import Metrica

    if fps <= 0:
        return
    resultado = calcular_tcs(frames, fps)
    if resultado.esquerdo is not None:
        session.add(
            Metrica(
                sessao_id=sessao_id,
                tipo="tcs_esq",
                valor=resultado.esquerdo.tcs_medio_ms,
                unidade="ms",
                apenas_informativa=True,
            )
        )
    if resultado.direito is not None:
        session.add(
            Metrica(
                sessao_id=sessao_id,
                tipo="tcs_dir",
                valor=resultado.direito.tcs_medio_ms,
                unidade="ms",
                apenas_informativa=True,
            )
        )
    session.commit()


def _safe_unlink(path: str) -> None:
    try:
        Path(path).unlink(missing_ok=True)
    except OSError:
        logger.debug("Não foi possível remover %s", path)


def iter_valid_keypoints(
    frames: Iterable[FrameKeypoints], keypoint_index: int
) -> Iterable[tuple[int, float, float]]:
    """Helper reutilizável: itera (frame_idx, x, y) pulando keypoints None."""
    for frame in frames:
        if keypoint_index >= len(frame.keypoints):
            continue
        kp = frame.keypoints[keypoint_index]
        if kp is None:
            continue
        yield frame.frame_idx, kp[0], kp[1]
