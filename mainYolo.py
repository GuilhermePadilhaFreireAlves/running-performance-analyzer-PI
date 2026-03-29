import math
import time
from ultralytics import YOLO

# Mapeamento de keypoints do COCO para índices
KEYPOINT_DICT = {
    'nose': 0,
    'left_eye': 1,
    'right_eye': 2,
    'left_ear': 3,
    'right_ear': 4,
    'left_shoulder': 5,
    'right_shoulder': 6,
    'left_elbow': 7,
    'right_elbow': 8,
    'left_wrist': 9,
    'right_wrist': 10,
    'left_hip': 11,
    'right_hip': 12,
    'left_knee': 13,
    'right_knee': 14,
    'left_ankle': 15,
    'right_ankle': 16
}

def calcular_angulo(a, b, c):
    """Calcula o ângulo entre três pontos (em graus)."""
    angulo = math.degrees(math.atan2(c[1] - b[1], c[0] - b[0]) - math.atan2(a[1] - b[1], a[0] - b[0]))
    angulo = abs(angulo)
    if angulo > 180.0:
        angulo = 360.0 - angulo
    return angulo

# Carrega o modelo YOLO
model = YOLO('yolo26x-pose.pt') 

# Executa a predição no vídeo
results = model.predict(source='./run/profissional.mp4', save=True, show=True, stream=True)

# --- Variáveis para cálculo de cadência ---
passos_contados = 0
perna_esquerda_em_flexao = False
perna_direita_em_flexao = False
ANGULO_FLEXAO_JOELHO_LIMIAR = 150  # Limiar em graus para considerar a perna flexionada
tempo_inicio = time.time()

# Itera sobre os frames do resultado
for frame_idx, r in enumerate(results):
    if r.keypoints and hasattr(r.keypoints, 'xy') and len(r.keypoints.xy) > 0 and r.keypoints.xy.shape[1] > 0:
        kpts = r.keypoints.xy[0]
        
        print(f"\n--- Frame {frame_idx} ---")

        # Extração de todos os pontos necessários
        pontos = {nome: kpts[idx].tolist() for nome, idx in KEYPOINT_DICT.items()}

        # --- Inicialização dos ângulos ---
        angulo_cotovelo_d, angulo_cotovelo_e = None, None
        angulo_joelho_d, angulo_joelho_e = None, None
        angulo_quadril_d, angulo_quadril_e = None, None

        # --- Cálculo dos Ângulos ---
        print("\n-- Ângulos das Articulações --")
        if all(pontos[p][0] > 0 for p in ['right_shoulder', 'right_elbow', 'right_wrist']):
            angulo_cotovelo_d = calcular_angulo(pontos['right_shoulder'], pontos['right_elbow'], pontos['right_wrist'])
            print(f"Cotovelo Direito: {angulo_cotovelo_d:.2f}°")

        if all(pontos[p][0] > 0 for p in ['left_shoulder', 'left_elbow', 'left_wrist']):
            angulo_cotovelo_e = calcular_angulo(pontos['left_shoulder'], pontos['left_elbow'], pontos['left_wrist'])
            print(f"Cotovelo Esquerdo: {angulo_cotovelo_e:.2f}°")

        if all(pontos[p][0] > 0 for p in ['right_hip', 'right_knee', 'right_ankle']):
            angulo_joelho_d = calcular_angulo(pontos['right_hip'], pontos['right_knee'], pontos['right_ankle'])
            print(f"Joelho Direito: {angulo_joelho_d:.2f}°")

        if all(pontos[p][0] > 0 for p in ['left_hip', 'left_knee', 'left_ankle']):
            angulo_joelho_e = calcular_angulo(pontos['left_hip'], pontos['left_knee'], pontos['left_ankle'])
            print(f"Joelho Esquerdo: {angulo_joelho_e:.2f}°")

        if all(pontos[p][0] > 0 for p in ['right_shoulder', 'right_hip', 'right_knee']):
            angulo_quadril_d = calcular_angulo(pontos['right_shoulder'], pontos['right_hip'], pontos['right_knee'])
            print(f"Quadril Direito: {angulo_quadril_d:.2f}°")

        if all(pontos[p][0] > 0 for p in ['left_shoulder', 'left_hip', 'left_knee']):
            angulo_quadril_e = calcular_angulo(pontos['left_shoulder'], pontos['left_hip'], pontos['left_knee'])
            print(f"Quadril Esquerdo: {angulo_quadril_e:.2f}°")

        # --- Análise de Postura do Tronco ---
        print("\n-- Postura e Simetria --")
        if all(pontos[p][0] > 0 for p in ['right_shoulder', 'left_shoulder', 'right_hip', 'left_hip']):
            ponto_medio_ombros = ((pontos['left_shoulder'][0] + pontos['right_shoulder'][0]) / 2, (pontos['left_shoulder'][1] + pontos['right_shoulder'][1]) / 2)
            ponto_medio_quadril = ((pontos['left_hip'][0] + pontos['right_hip'][0]) / 2, (pontos['left_hip'][1] + pontos['right_hip'][1]) / 2)
            ponto_vertical_imaginario = (ponto_medio_quadril[0], ponto_medio_quadril[1] - 50) # Ponto acima do quadril para definir a vertical
            
            inclinacao_tronco = calcular_angulo(ponto_vertical_imaginario, ponto_medio_quadril, ponto_medio_ombros)
            print(f"Inclinação do Tronco: {inclinacao_tronco:.2f}°")

        # --- Análise de Simetria ---
        if angulo_joelho_d is not None and angulo_joelho_e is not None:
            print(f"Diferença Simetria Joelhos: {abs(angulo_joelho_d - angulo_joelho_e):.2f}°")
        if angulo_cotovelo_d is not None and angulo_cotovelo_e is not None:
            print(f"Diferença Simetria Cotovelos: {abs(angulo_cotovelo_d - angulo_cotovelo_e):.2f}°")

        # --- Análise de Cadência ---
        if angulo_joelho_e is not None:
            if angulo_joelho_e < ANGULO_FLEXAO_JOELHO_LIMIAR and not perna_esquerda_em_flexao:
                perna_esquerda_em_flexao = True
                passos_contados += 1
            elif angulo_joelho_e >= ANGULO_FLEXAO_JOELHO_LIMIAR:
                perna_esquerda_em_flexao = False
        
        if angulo_joelho_d is not None:
            if angulo_joelho_d < ANGULO_FLEXAO_JOELHO_LIMIAR and not perna_direita_em_flexao:
                perna_direita_em_flexao = True
                passos_contados += 1
            elif angulo_joelho_d >= ANGULO_FLEXAO_JOELHO_LIMIAR:
                perna_direita_em_flexao = False

        tempo_decorrido = time.time() - tempo_inicio
        if tempo_decorrido > 1: # Começa a calcular após 1 segundo
            cadencia_atual = (passos_contados / tempo_decorrido) * 60
            print("\n-- Cadência --")
            print(f"Cadência Estimada: {cadencia_atual:.2f} passos/minuto")
            print(f"(Passos contados: {passos_contados})")

    else:
        print(f"--- Frame {frame_idx}: Sem keypoints detectados ---")

print("\n--- Análise Final ---")
tempo_total = time.time() - tempo_inicio
if tempo_total > 1:
    cadencia_final = (passos_contados / tempo_total) * 60
    print(f"Cadência Média Final: {cadencia_final:.2f} passos/minuto")
    print(f"Total de Passos Contados: {passos_contados}")
    print(f"Duração da Análise: {tempo_total:.2f} segundos")
