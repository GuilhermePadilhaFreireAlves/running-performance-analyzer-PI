import { describe, expect, it } from 'vitest'
import {
  METRIC_CONFIGS,
  SEVERIDADE_ATENCAO,
  SEVERIDADE_CRITICO,
  SEVERIDADE_INFORMATIVO,
  buildGaugeGeometry,
  buildMetricasVisuais,
  formatNota,
  groupBySeveridade,
  notaClassName,
  severidadeDisplay,
} from './analysisDisplay'

describe('formatNota', () => {
  it('formata nota numérica com uma casa decimal', () => {
    expect(formatNota(7.24)).toBe('7.2')
    expect(formatNota(10)).toBe('10.0')
    expect(formatNota(0)).toBe('0.0')
  })

  it('retorna placeholder para null ou NaN', () => {
    expect(formatNota(null)).toBe('—')
    expect(formatNota(Number.NaN)).toBe('—')
  })
})

describe('notaClassName', () => {
  it('mapeia faixas de nota para classes de cor', () => {
    expect(notaClassName(9)).toBe('nota-good')
    expect(notaClassName(7)).toBe('nota-good')
    expect(notaClassName(5)).toBe('nota-ok')
    expect(notaClassName(4)).toBe('nota-ok')
    expect(notaClassName(2)).toBe('nota-bad')
    expect(notaClassName(0)).toBe('nota-bad')
  })

  it('retorna neutra para null/NaN', () => {
    expect(notaClassName(null)).toBe('nota-neutral')
    expect(notaClassName(Number.NaN)).toBe('nota-neutral')
  })
})

describe('severidadeDisplay', () => {
  it('mapeia as três severidades do backend para label e classe', () => {
    expect(severidadeDisplay(SEVERIDADE_CRITICO)).toEqual({
      className: 'severity-critico',
      label: 'Crítico',
    })
    expect(severidadeDisplay(SEVERIDADE_ATENCAO)).toEqual({
      className: 'severity-atencao',
      label: 'Atenção',
    })
    expect(severidadeDisplay(SEVERIDADE_INFORMATIVO)).toEqual({
      className: 'severity-informativo',
      label: 'Dentro do ideal',
    })
  })

  it('fallback preserva o valor recebido como label', () => {
    const out = severidadeDisplay('desconhecido')
    expect(out.label).toBe('desconhecido')
    expect(out.className).toBe('severity-default')
  })
})

describe('buildGaugeGeometry', () => {
  it('posiciona marcador no meio e zona ideal proporcional', () => {
    const config = METRIC_CONFIGS.angulo_cotovelo_esq
    const g = buildGaugeGeometry(config, 90)
    // chartMin=30, chartMax=180 ⇒ range=150; (90-30)/150 = 40%
    expect(g.markerPct).toBeCloseTo(40, 5)
    // ideal 70..110 ⇒ left 40/150 = 26.666%, width 40/150 = 26.666%
    expect(g.idealLeftPct).toBeCloseTo((40 / 150) * 100, 5)
    expect(g.idealWidthPct).toBeCloseTo((40 / 150) * 100, 5)
    expect(g.displayValue).toBe('90.0 °')
  })

  it('clamp do marker quando o valor excede o range do chart', () => {
    const config = METRIC_CONFIGS.angulo_cotovelo_esq
    expect(buildGaugeGeometry(config, 10).markerPct).toBe(0)
    expect(buildGaugeGeometry(config, 999).markerPct).toBe(100)
  })

  it('aplica transform de flexão = 180 - interno no joelho', () => {
    const config = METRIC_CONFIGS.angulo_joelho_esq
    // interno=160 ⇒ flexão=20; chartMax=60 ⇒ marker = 20/60 = 33.33%
    const g = buildGaugeGeometry(config, 160)
    expect(g.markerPct).toBeCloseTo((20 / 60) * 100, 5)
    expect(g.displayValue).toBe('20.0 °')
  })

  it('overstriding usa abs para posicionar mas preserva sinal no texto', () => {
    const config = METRIC_CONFIGS.overstriding_esq
    // valor = -10 ⇒ |v|=10, chartMin=0 chartMax=25 ⇒ marker = 40%
    const g = buildGaugeGeometry(config, -10)
    expect(g.markerPct).toBeCloseTo(40, 5)
    expect(g.displayValue).toBe('-10.0 cm')
  })

  it('formatter custom (cadência) arredonda para inteiro', () => {
    const config = METRIC_CONFIGS.cadencia
    const g = buildGaugeGeometry(config, 175.7)
    expect(g.displayValue).toBe('176 spm')
  })
})

describe('groupBySeveridade', () => {
  it('agrupa por severidade mantendo ordem de inserção dentro do grupo', () => {
    const recs = [
      { categoria: 'A', descricao: '', severidade: SEVERIDADE_ATENCAO },
      { categoria: 'B', descricao: '', severidade: SEVERIDADE_CRITICO },
      { categoria: 'C', descricao: '', severidade: SEVERIDADE_ATENCAO },
      { categoria: 'D', descricao: '', severidade: SEVERIDADE_INFORMATIVO },
    ]
    const grupos = groupBySeveridade(recs)
    expect(grupos[SEVERIDADE_CRITICO].map((r) => r.categoria)).toEqual(['B'])
    expect(grupos[SEVERIDADE_ATENCAO].map((r) => r.categoria)).toEqual(['A', 'C'])
    expect(grupos[SEVERIDADE_INFORMATIVO].map((r) => r.categoria)).toEqual(['D'])
  })

  it('cria bucket para severidade desconhecida sem perder itens', () => {
    const recs = [
      { categoria: 'X', descricao: '', severidade: 'raro' },
    ]
    const grupos = groupBySeveridade(recs)
    expect(grupos['raro']).toHaveLength(1)
  })
})

describe('buildMetricasVisuais', () => {
  it('ignora tipos desconhecidos e valores nulos, respeitando a ordem', () => {
    const metricas = [
      { tipo: 'cadencia', valor: 180, unidade: 'spm' },
      { tipo: 'angulo_joelho_esq', valor: 160, unidade: 'graus' },
      { tipo: 'tipo_fantasma', valor: 1, unidade: null },
      { tipo: 'angulo_cotovelo_esq', valor: null, unidade: 'graus' },
    ]
    const visuais = buildMetricasVisuais(metricas)
    const tipos = visuais.map((v) => v.tipo)
    // Ordem definida pela METRIC_DISPLAY_ORDER: joelho antes de cadência
    expect(tipos).toEqual(['angulo_joelho_esq', 'cadencia'])
  })

  it('gera gauge com geometria válida para cada métrica retornada', () => {
    const visuais = buildMetricasVisuais([
      { tipo: 'inclinacao_tronco', valor: 6, unidade: 'graus' },
    ])
    expect(visuais).toHaveLength(1)
    const g = visuais[0].gauge
    // chartMin=-5, chartMax=20 ⇒ range=25; (6-(-5))/25 = 44%
    expect(g.markerPct).toBeCloseTo(44, 5)
    // ideal 4..8 ⇒ left=(4+5)/25=36%, width=4/25=16%
    expect(g.idealLeftPct).toBeCloseTo(36, 5)
    expect(g.idealWidthPct).toBeCloseTo(16, 5)
  })
})
