import math
import time
import numpy as np
import matplotlib.pyplot as plt
from ultralytics import YOLO

# Mapeamento de keypoints do COCO para índices
KEYPOINT_DICT = {
    'nose': 0, 'left_eye': 1, 'right_eye': 2, 'left_ear': 3, 'right_ear': 4,
    'left_shoulder': 5, 'right_shoulder': 6, 'left_elbow': 7, 'right_elbow': 8,
    'left_wrist': 9, 'right_wrist': 10, 'left_hip': 11, 'right_hip': 12,
    'left_knee': 13, 'right_knee': 14, 'left_ankle': 15, 'right_ankle': 16
}

def calcular_angulo(a, b, c):
    """Calcula o ângulo entre três pontos (em graus)."""
    angulo = math.degrees(math.atan2(c[1] - b[1], c[0] - b[0]) - math.atan2(a[1] - b[1], a[0] - b[0]))
    angulo = abs(angulo)
    if angulo > 180.0:
        angulo = 360.0 - angulo
    return angulo

def gerar_graficos(dados):
    """Gera e salva os gráficos da análise."""
    print("\nGerando gráficos da análise...")
    
    # Gráfico 1: Ângulo dos Joelhos ao Longo do Tempo
    plt.figure(figsize=(12, 6))
    plt.plot(dados['frames'], dados['angulo_joelho_d'], label='Joelho Direito', color='blue', alpha=0.7)
    plt.plot(dados['frames'], dados['angulo_joelho_e'], label='Joelho Esquerdo', color='red', alpha=0.7)
    plt.title('Ângulo dos Joelhos Durante a Corrida')
    plt.xlabel('Frame')
    plt.ylabel('Ângulo (graus)')
    plt.legend()
    plt.grid(True)
    plt.savefig('grafico_angulo_joelhos.png')
    plt.close()

    # Gráfico 2: Inclinação do Tronco ao Longo do Tempo
    plt.figure(figsize=(12, 6))
    plt.plot(dados['frames'], dados['inclinacao_tronco'], label='Inclinação do Tronco', color='green')
    plt.title('Inclinação do Tronco Durante a Corrida')
    plt.xlabel('Frame')
    plt.ylabel('Ângulo (graus)')
    plt.legend()
    plt.grid(True)
    plt.savefig('grafico_inclinacao_tronco.png')
    plt.close()

    # Gráfico 3: Médias dos Ângulos
    labels = ['Cotovelo D', 'Cotovelo E', 'Joelho D', 'Joelho E', 'Quadril D', 'Quadril E']
    medias = [
        np.nanmean(dados['angulo_cotovelo_d']),
        np.nanmean(dados['angulo_cotovelo_e']),
        np.nanmean(dados['angulo_joelho_d']),
        np.nanmean(dados['angulo_joelho_e']),
        np.nanmean(dados['angulo_quadril_d']),
        np.nanmean(dados['angulo_quadril_e'])
    ]
    plt.figure(figsize=(10, 6))
    plt.bar(labels, medias, color=['blue', 'red', 'blue', 'red', 'blue', 'red'])
    plt.title('Média dos Ângulos das Articulações')
    plt.ylabel('Ângulo Médio (graus)')
    plt.grid(axis='y')
    plt.savefig('grafico_media_angulos.png')
    plt.close()
    
    print("Gráficos salvos como 'grafico_*.png'")

# --- Estrutura para armazenar dados da análise ---
dados_analise = {
    "frames": [], "angulo_cotovelo_d": [], "angulo_cotovelo_e": [],
    "angulo_joelho_d": [], "angulo_joelho_e": [], "angulo_quadril_d": [],
    "angulo_quadril_e": [], "inclinacao_tronco": []
}

# Carrega o modelo YOLO
model = YOLO('yolo26x-pose.pt') 

# Executa a predição no vídeo
results = model.predict(source='./run/profissional.mp4', save=True, show=True, stream=True)

# --- Variáveis para cálculo de cadência ---
passos_contados = 0
perna_esquerda_em_flexao = False
perna_direita_em_flexao = False
ANGULO_FLEXAO_JOELHO_LIMIAR = 150
tempo_inicio = time.time()

# Itera sobre os frames do resultado
for frame_idx, r in enumerate(results):
    dados_analise['frames'].append(frame_idx)
    # Inicializa todos os valores do frame como NaN
    for key in dados_analise:
        if key != 'frames' and len(dados_analise[key]) < len(dados_analise['frames']):
            dados_analise[key].append(np.nan)

    if r.keypoints and hasattr(r.keypoints, 'xy') and len(r.keypoints.xy) > 0 and r.keypoints.xy.shape[1] > 0:
        kpts = r.keypoints.xy[0]
        print(f"\n--- Frame {frame_idx} ---")
        pontos = {nome: kpts[idx].tolist() for nome, idx in KEYPOINT_DICT.items()}

        # --- Cálculo e Armazenamento dos Ângulos ---
        if all(pontos[p][0] > 0 for p in ['right_shoulder', 'right_elbow', 'right_wrist']):
            dados_analise['angulo_cotovelo_d'][-1] = calcular_angulo(pontos['right_shoulder'], pontos['right_elbow'], pontos['right_wrist'])
        if all(pontos[p][0] > 0 for p in ['left_shoulder', 'left_elbow', 'left_wrist']):
            dados_analise['angulo_cotovelo_e'][-1] = calcular_angulo(pontos['left_shoulder'], pontos['left_elbow'], pontos['left_wrist'])
        if all(pontos[p][0] > 0 for p in ['right_hip', 'right_knee', 'right_ankle']):
            dados_analise['angulo_joelho_d'][-1] = calcular_angulo(pontos['right_hip'], pontos['right_knee'], pontos['right_ankle'])
        if all(pontos[p][0] > 0 for p in ['left_hip', 'left_knee', 'left_ankle']):
            dados_analise['angulo_joelho_e'][-1] = calcular_angulo(pontos['left_hip'], pontos['left_knee'], pontos['left_ankle'])
        if all(pontos[p][0] > 0 for p in ['right_shoulder', 'right_hip', 'right_knee']):
            dados_analise['angulo_quadril_d'][-1] = calcular_angulo(pontos['right_shoulder'], pontos['right_hip'], pontos['right_knee'])
        if all(pontos[p][0] > 0 for p in ['left_shoulder', 'left_hip', 'left_knee']):
            dados_analise['angulo_quadril_e'][-1] = calcular_angulo(pontos['left_shoulder'], pontos['left_hip'], pontos['left_knee'])

        # --- Análise de Postura do Tronco ---
        if all(pontos[p][0] > 0 for p in ['right_shoulder', 'left_shoulder', 'right_hip', 'left_hip']):
            ponto_medio_ombros = ((pontos['left_shoulder'][0] + pontos['right_shoulder'][0]) / 2, (pontos['left_shoulder'][1] + pontos['right_shoulder'][1]) / 2)
            ponto_medio_quadril = ((pontos['left_hip'][0] + pontos['right_hip'][0]) / 2, (pontos['left_hip'][1] + pontos['right_hip'][1]) / 2)
            ponto_vertical_imaginario = (ponto_medio_quadril[0], ponto_medio_quadril[1] - 50)
            dados_analise['inclinacao_tronco'][-1] = calcular_angulo(ponto_vertical_imaginario, ponto_medio_quadril, ponto_medio_ombros)

        # --- Análise de Cadência ---
        angulo_joelho_e_atual = dados_analise['angulo_joelho_e'][-1]
        if not np.isnan(angulo_joelho_e_atual):
            if angulo_joelho_e_atual < ANGULO_FLEXAO_JOELHO_LIMIAR and not perna_esquerda_em_flexao:
                perna_esquerda_em_flexao = True
                passos_contados += 1
            elif angulo_joelho_e_atual >= ANGULO_FLEXAO_JOELHO_LIMIAR:
                perna_esquerda_em_flexao = False
        
        angulo_joelho_d_atual = dados_analise['angulo_joelho_d'][-1]
        if not np.isnan(angulo_joelho_d_atual):
            if angulo_joelho_d_atual < ANGULO_FLEXAO_JOELHO_LIMIAR and not perna_direita_em_flexao:
                perna_direita_em_flexao = True
                passos_contados += 1
            elif angulo_joelho_d_atual >= ANGULO_FLEXAO_JOELHO_LIMIAR:
                perna_direita_em_flexao = False
    else:
        print(f"--- Frame {frame_idx}: Sem keypoints detectados ---")

# --- Finalização e Geração de Gráficos ---
print("\n--- Análise Final ---")
tempo_total = time.time() - tempo_inicio
if tempo_total > 1:
    cadencia_final = (passos_contados / tempo_total) * 60
    print(f"Cadência Média Final: {cadencia_final:.2f} passos/minuto")
    print(f"Total de Passos Contados: {passos_contados}")
    print(f"Duração da Análise: {tempo_total:.2f} segundos")

# Gera os gráficos com os dados coletados
gerar_graficos(dados_analise)
