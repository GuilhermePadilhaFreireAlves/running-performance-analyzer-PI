import { describe, expect, it } from 'vitest'
import {
  ASYMMETRY_ROWS_META,
  CHART_SPECS,
  asymmetryBarPct,
  asymmetryStatus,
  buildAsymmetryRows,
  buildCsv,
  buildCsvFilename,
  buildFramePoints,
  flexaoFromInterno,
  formatAsymmetry,
  formatChartValue,
  isFrameOutOfRange,
  isValueOutOfRange,
} from './rawAnalysis'
import type { FramePoint } from './rawAnalysis'
import type { RawFrame, SimetriaRawResponse } from '../api/analysis'

function frame(overrides: Partial<RawFrame>): RawFrame {
  return {
    frame_idx: 0,
    keypoints: [],
    angulo_joelho_esq: null,
    angulo_joelho_dir: null,
    angulo_cotovelo_esq: null,
    angulo_cotovelo_dir: null,
    inclinacao_tronco: null,
    y_com: null,
    ...overrides,
  }
}

describe('flexaoFromInterno', () => {
  it('converte ângulo interno em flexão: 180 - interno', () => {
    expect(flexaoFromInterno(180)).toBe(0)
    expect(flexaoFromInterno(160)).toBe(20)
    expect(flexaoFromInterno(90)).toBe(90)
  })
})

describe('buildFramePoints', () => {
  it('aplica transform de flexão para o joelho e preserva demais campos', () => {
    const frames: RawFrame[] = [
      frame({
        frame_idx: 0,
        angulo_joelho_esq: 160,
        angulo_joelho_dir: 155,
        angulo_cotovelo_esq: 90,
        angulo_cotovelo_dir: 95,
        inclinacao_tronco: 6,
        y_com: 500,
      }),
      frame({
        frame_idx: 1,
        angulo_joelho_esq: 150,
        angulo_joelho_dir: 145,
        angulo_cotovelo_esq: 110,
        angulo_cotovelo_dir: 115,
        inclinacao_tronco: 7,
        y_com: 510,
      }),
    ]
    const pts = buildFramePoints(frames)
    expect(pts).toHaveLength(2)
    expect(pts[0]?.frame_idx).toBe(0)
    expect(pts[0]?.['angulo_joelho_esq']).toBe(20)
    expect(pts[0]?.['angulo_joelho_dir']).toBe(25)
    expect(pts[0]?.['angulo_cotovelo_esq']).toBe(90)
    expect(pts[0]?.['inclinacao_tronco']).toBe(6)
    expect(pts[0]?.['y_com']).toBe(500)
    expect(pts[1]?.['angulo_joelho_esq']).toBe(30)
  })

  it('propaga null para keypoints/ângulos ausentes sem interpolar', () => {
    const frames: RawFrame[] = [
      frame({
        frame_idx: 5,
        angulo_joelho_esq: null,
        angulo_cotovelo_esq: null,
        inclinacao_tronco: null,
        y_com: null,
      }),
    ]
    const pts = buildFramePoints(frames)
    expect(pts[0]?.['angulo_joelho_esq']).toBeNull()
    expect(pts[0]?.['angulo_cotovelo_esq']).toBeNull()
    expect(pts[0]?.['inclinacao_tronco']).toBeNull()
    expect(pts[0]?.['y_com']).toBeNull()
  })

  it('lida com lista vazia de frames', () => {
    expect(buildFramePoints([])).toEqual([])
  })

  it('normaliza NaN para null', () => {
    const frames: RawFrame[] = [
      frame({ frame_idx: 0, inclinacao_tronco: Number.NaN }),
    ]
    expect(buildFramePoints(frames)[0]?.['inclinacao_tronco']).toBeNull()
  })
})

describe('CHART_SPECS', () => {
  it('cobre todos os 4 gráficos requeridos pela US-026', () => {
    expect(CHART_SPECS).toHaveLength(4)
    const titulos = CHART_SPECS.map((c) => c.title)
    expect(titulos.some((t) => t.includes('joelho'))).toBe(true)
    expect(titulos.some((t) => t.includes('cotovelo'))).toBe(true)
    expect(titulos.some((t) => t.includes('tronco'))).toBe(true)
    expect(titulos.some((t) => t.toLowerCase().includes('centro de massa'))).toBe(true)
  })

  it('séries têm key/label/color não-vazios', () => {
    for (const chart of CHART_SPECS) {
      for (const serie of chart.series) {
        expect(serie.key.length).toBeGreaterThan(0)
        expect(serie.label.length).toBeGreaterThan(0)
        expect(serie.color.length).toBeGreaterThan(0)
      }
    }
  })
})

describe('buildAsymmetryRows', () => {
  it('monta três linhas na ordem PRD (TCS, joelho, oscilação)', () => {
    const simetria: SimetriaRawResponse = { tcs: 3.2, joelho: 7.5, oscilacao: 12.0 }
    const rows = buildAsymmetryRows(simetria)
    expect(rows).toHaveLength(3)
    expect(rows[0]?.key).toBe('tcs')
    expect(rows[0]?.valor).toBe(3.2)
    expect(rows[1]?.key).toBe('joelho')
    expect(rows[1]?.valor).toBe(7.5)
    expect(rows[2]?.key).toBe('oscilacao')
    expect(rows[2]?.valor).toBe(12.0)
  })

  it('propaga null quando a simetria correspondente não foi calculada', () => {
    const simetria: SimetriaRawResponse = { tcs: null, joelho: 4.0, oscilacao: null }
    const rows = buildAsymmetryRows(simetria)
    expect(rows[0]?.valor).toBeNull()
    expect(rows[1]?.valor).toBe(4.0)
    expect(rows[2]?.valor).toBeNull()
  })

  it('meta cobre exatamente tcs/joelho/oscilacao', () => {
    const keys = ASYMMETRY_ROWS_META.map((r) => r.key)
    expect(new Set(keys)).toEqual(new Set(['tcs', 'joelho', 'oscilacao']))
  })
})

describe('asymmetryBarPct', () => {
  it('escala valor absoluto para barra de 0–100% (teto em 30%)', () => {
    expect(asymmetryBarPct(0)).toBe(0)
    expect(asymmetryBarPct(15)).toBe(50)
    expect(asymmetryBarPct(30)).toBe(100)
    expect(asymmetryBarPct(60)).toBe(100) // clamp superior
    expect(asymmetryBarPct(-10)).toBeCloseTo(33.33, 1) // usa |valor|
  })

  it('retorna 0 para null/NaN', () => {
    expect(asymmetryBarPct(null)).toBe(0)
    expect(asymmetryBarPct(Number.NaN)).toBe(0)
  })
})

describe('asymmetryStatus', () => {
  it('classifica como ok quando |valor| <= 10%, alerta caso contrário', () => {
    expect(asymmetryStatus(0)).toBe('ok')
    expect(asymmetryStatus(9.9)).toBe('ok')
    expect(asymmetryStatus(10)).toBe('ok')
    expect(asymmetryStatus(10.1)).toBe('alerta')
    expect(asymmetryStatus(25)).toBe('alerta')
  })

  it("retorna 'nd' para null/NaN", () => {
    expect(asymmetryStatus(null)).toBe('nd')
    expect(asymmetryStatus(Number.NaN)).toBe('nd')
  })
})

describe('formatAsymmetry', () => {
  it('formata percentual com uma casa decimal', () => {
    expect(formatAsymmetry(3.14159)).toBe('3.1%')
    expect(formatAsymmetry(0)).toBe('0.0%')
  })

  it('retorna placeholder para valor ausente', () => {
    expect(formatAsymmetry(null)).toBe('não disponível')
    expect(formatAsymmetry(Number.NaN)).toBe('não disponível')
  })
})

describe('formatChartValue', () => {
  it('formata valor numérico com unidade', () => {
    expect(formatChartValue(42.375, '°')).toBe('42.4 °')
    expect(formatChartValue(0, 'cm')).toBe('0.0 cm')
  })

  it('aceita string numérica e converte', () => {
    expect(formatChartValue('7.1', '°')).toBe('7.1 °')
  })

  it('retorna — para null/undefined/NaN/strings inválidas', () => {
    expect(formatChartValue(null, '°')).toBe('—')
    expect(formatChartValue(undefined, '°')).toBe('—')
    expect(formatChartValue(Number.NaN, '°')).toBe('—')
    expect(formatChartValue('abc', '°')).toBe('—')
  })
})

describe('isValueOutOfRange', () => {
  it('classifica flexão do joelho na faixa ideal 15–25°', () => {
    expect(isValueOutOfRange(14.9, 'angulo_joelho_esq')).toBe(true)
    expect(isValueOutOfRange(15, 'angulo_joelho_esq')).toBe(false)
    expect(isValueOutOfRange(20, 'angulo_joelho_dir')).toBe(false)
    expect(isValueOutOfRange(25, 'angulo_joelho_esq')).toBe(false)
    expect(isValueOutOfRange(25.1, 'angulo_joelho_esq')).toBe(true)
  })

  it('classifica cotovelo fora de 70–110°', () => {
    expect(isValueOutOfRange(90, 'angulo_cotovelo_esq')).toBe(false)
    expect(isValueOutOfRange(50, 'angulo_cotovelo_dir')).toBe(true)
    expect(isValueOutOfRange(130, 'angulo_cotovelo_esq')).toBe(true)
  })

  it('classifica tronco fora de 4–8°', () => {
    expect(isValueOutOfRange(5, 'inclinacao_tronco')).toBe(false)
    expect(isValueOutOfRange(0, 'inclinacao_tronco')).toBe(true)
    expect(isValueOutOfRange(12, 'inclinacao_tronco')).toBe(true)
  })

  it('null/undefined/NaN nunca destacam', () => {
    expect(isValueOutOfRange(null, 'angulo_joelho_esq')).toBe(false)
    expect(isValueOutOfRange(undefined, 'angulo_joelho_esq')).toBe(false)
    expect(isValueOutOfRange(Number.NaN, 'angulo_joelho_esq')).toBe(false)
  })
})

describe('isFrameOutOfRange', () => {
  function point(overrides: Partial<FramePoint> = {}): FramePoint {
    return {
      frame_idx: 0,
      angulo_joelho_esq: 20,
      angulo_joelho_dir: 20,
      angulo_cotovelo_esq: 90,
      angulo_cotovelo_dir: 90,
      inclinacao_tronco: 6,
      y_com: 500,
      ...overrides,
    }
  }

  it('retorna false quando todas as métricas estão na faixa ideal', () => {
    expect(isFrameOutOfRange(point())).toBe(false)
  })

  it('retorna true se qualquer métrica está fora', () => {
    expect(isFrameOutOfRange(point({ angulo_joelho_esq: 40 }))).toBe(true)
    expect(isFrameOutOfRange(point({ inclinacao_tronco: 20 }))).toBe(true)
    expect(isFrameOutOfRange(point({ angulo_cotovelo_dir: 50 }))).toBe(true)
  })

  it('ignora y_com (métrica sem faixa ideal visual)', () => {
    expect(isFrameOutOfRange(point({ y_com: 99999 }))).toBe(false)
  })
})

describe('buildCsv', () => {
  it('gera header + linhas com decimais apropriados', () => {
    const pts: FramePoint[] = [
      {
        frame_idx: 0,
        angulo_joelho_esq: 20.12345,
        angulo_joelho_dir: 22.7,
        angulo_cotovelo_esq: 90,
        angulo_cotovelo_dir: 95,
        inclinacao_tronco: 6.3,
        y_com: 500.4,
      },
    ]
    const csv = buildCsv(pts)
    const lines = csv.split('\n')
    expect(lines).toHaveLength(2)
    expect(lines[0]).toBe(
      'frame_idx,flexao_joelho_esq_graus,flexao_joelho_dir_graus,angulo_cotovelo_esq_graus,angulo_cotovelo_dir_graus,inclinacao_tronco_graus,y_com_px',
    )
    expect(lines[1]).toBe('0,20.1,22.7,90.0,95.0,6.3,500.4')
  })

  it('null/NaN viram células vazias, frame_idx sem decimais', () => {
    const pts: FramePoint[] = [
      {
        frame_idx: 7,
        angulo_joelho_esq: null,
        angulo_joelho_dir: Number.NaN,
        angulo_cotovelo_esq: undefined,
        angulo_cotovelo_dir: 100,
        inclinacao_tronco: null,
        y_com: null,
      },
    ]
    const csv = buildCsv(pts)
    expect(csv.split('\n')[1]).toBe('7,,,,100.0,,')
  })

  it('retorna apenas header quando não há pontos', () => {
    expect(buildCsv([]).split('\n')).toHaveLength(1)
  })
})

describe('buildCsvFilename', () => {
  it('compoõe nome do arquivo com o id da sessão', () => {
    expect(buildCsvFilename(42)).toBe('stride-analise-42-frames.csv')
    expect(buildCsvFilename('abc')).toBe('stride-analise-abc-frames.csv')
  })
})
