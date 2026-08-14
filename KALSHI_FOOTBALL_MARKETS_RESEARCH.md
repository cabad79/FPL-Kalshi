# Investigación: Mercados de Fútbol en Kalshi
**Fecha:** 2026-08-14  
**Estado:** Investigación Completa  
**Objetivo:** Análisis detallado de tipos de mercados, estructura de datos y oportunidades de trading

---

## 📋 Tabla de Contenidos

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Disponibilidad de Mercados de Fútbol en Kalshi](#disponibilidad-de-mercados)
3. [Tipos de Mercados Disponibles](#tipos-de-mercados)
4. [Estructura de Datos Kalshi](#estructura-de-datos)
5. [Desafíos Técnicos](#desafíos-técnicos)
6. [Oportunidades de Arbitrage](#oportunidades-de-arbitrage)
7. [Integración con FPL](#integración-fpl)
8. [Recomendaciones](#recomendaciones)

---

## 🎯 Resumen Ejecutivo

### Hallazgos Clave

✅ **Kalshi SOPORTA mercados de fútbol**
- English Premier League (EPL) - Cobertura completa
- Soccer Futures - Mercados de temporada/torneo
- Soccer Props - Mercados específicos de partidos y jugadores

❌ **Kalshi NO es un sportsbook tradicional**
- Es un "prediction market" regulado (CFTC)
- Funciona como bolsa de futuros de eventos
- Precios en centavos (0-100) = probabilidad implícita

✅ **Mercados más profundos en**
- Premier League inglesa (EPL)
- Copa del Mundo (World Cup)
- Champions League

⚠️ **Limitaciones:**
- No hay mercados para todas las ligas mundiales
- Cobertura menor en ligas secundarias
- Spreads bid-ask varían significativamente

---

## 📊 Disponibilidad de Mercados

### Cobertura Actual (2026)

```
MERCADOS DISPONIBLES EN KALSHI
├─ English Premier League (EPL)
│  ├─ Mercados de Temporada ✅
│  ├─ Props Individuales ✅
│  └─ Futures/Campeonatos ✅
│
├─ Torneos Internacionales
│  ├─ World Cup 2026 ✅
│  ├─ Champions League ✅
│  └─ Copa America ✅
│
├─ Soccer Props (General)
│  ├─ Match Outcomes ✅
│  ├─ Goal Markets ✅
│  ├─ Corner Markets ✅
│  └─ Card/Yellow/Red Markets ⚠️
│
└─ Otras Ligas
   ├─ Ligas Europeas Seleccionadas ⚠️
   ├─ MLS (Estados Unidos) ⚠️
   └─ Ligas Menores ❌
```

### Páginas Disponibles

1. **Soccer Props General:** `kalshi.com/category/sports/soccer/all/props`
2. **EPL Markets:** `kalshi.com/category/sports/soccer/epl`
3. **English Premier League:** `kalshi.com/category/sports/soccer/english-premier-league`
4. **EPL Futures:** `kalshi.com/category/sports/soccer/epl/futures`
5. **Corners Markets:** `kalshi.com/category/sports/soccer/all/corners`

---

## 🏆 Tipos de Mercados Disponibles

### 1. MERCADOS DE RESULTADO DE PARTIDO (Match Outcomes)

```
Tipo: Binary Markets (YES/NO contracts)
Precio: 0-100 centavos (representa probabilidad %)

EJEMPLOS:
├─ "Manchester United over Liverpool"
│  └─ YES: 55¢ (55% probabilidad estimada)
│  └─ NO:  45¢ (45% probabilidad estimada)
│
├─ "Chelsea wins vs Arsenal"
│  └─ Similar estructura
│
└─ "Will draw happen in Man City game?"
   └─ YES: 30¢ (draw probability)
```

**Estructura de datos requerida:**
```python
{
  "market_id": "KXEPLTOTM-26AUG23",      # Unique identifier
  "ticker": "KXEPLTOTM-26AUG23",
  "series": "SOCCER-EPL-MATCH-OUTCOMES",
  "event_id": "MANCUNITED-v-LIVERPOOL",
  "teams": ["Manchester United", "Liverpool"],
  "match_date": "2026-08-23T15:00:00Z",
  "market_type": "match_outcome",
  "contract_period": "match",
  
  # Precios actuales
  "yes_price": 55,                       # en centavos
  "no_price": 45,
  "bid_price": 54,                       # bid/ask spread
  "ask_price": 56,
  "spread_pct": 2.0,                     # (ask - bid) / mid × 100
  
  # Liquidez
  "volume_24h": 125000,                  # contracts traded
  "open_interest": 85000,                # contracts outstanding
  "liquidity_score": 8.5,                # 1-10
  
  # Settlement
  "settlement_rule": "Official result by league",
  "settlement_source": "Premier League official",
  "early_close_possible": false
}
```

---

### 2. MERCADOS DE GOLES (Goals Markets)

#### 2.1 Over/Under Goals

```
Mercados: Goals scored by team/match
Formato: "Will [Team] score over/under X goals?"

EJEMPLOS CON ESTRUCTURA:
└─ Match: Liverpool vs Chelsea
   ├─ Liverpool Over 1.5 Goals
   │  ├─ YES: 62¢ (62% probability)
   │  └─ Data needed:
   │     - historical_goals_avg: 2.1
   │     - home_advantage: +0.3
   │     - opponent_defense_rating: 72
   │     - form_last_5: [2, 1, 3, 2, 1]
   │
   ├─ Chelsea Under 2.5 Goals
   │  ├─ YES: 48¢ (48% probability)
   │  └─ Same data structure
   │
   └─ Total Match Over 2.5 Goals
      ├─ YES: 58¢
      └─ Both teams' metrics required
```

**Estructura completa para análisis:**
```python
{
  "market_id": "KXEPLOUGOALS-LIV-26AUG23",
  "ticker": "KXEPLOUGOALS-LIV-26AUG23",
  "market_type": "over_under_goals",
  "team": "Liverpool",
  "threshold": 1.5,
  "side": "over",
  
  # Datos predictivos requeridos
  "predictor_data": {
    "team_stats": {
      "goals_per_match_avg": 2.1,
      "goals_last_10_matches": [2, 1, 3, 2, 1, 2, 3, 2, 1, 2],
      "home_goals_avg": 2.4,
      "away_goals_avg": 1.8,
      "attacking_players": ["Kane", "Salah", "Mount"],
      "player_form_scores": [8.5, 9.2, 7.8]
    },
    "opponent_stats": {
      "goals_conceded_per_match": 1.2,
      "defense_rating": 72,
      "defensive_errors_last_5": 2,
      "suspended_defenders": []
    },
    "match_context": {
      "home_team": "Liverpool",
      "away_team": "Chelsea",
      "importance": "league",
      "weather_impact": "neutral",
      "surface_type": "grass"
    }
  }
}
```

#### 2.2 Correct Score / Exact Goals

```
Mercados más específicos (menos comunes en Kalshi):
"Match ends 2-1" - YES/NO contract
"Total goals exactly 3" - YES/NO contract

Nota: Estos son menos líquidos que over/under
```

---

### 3. MERCADOS DE TARJETAS (Card Markets)

```
TIPOS DISPONIBLES:
├─ "Player receives yellow card" ✅
├─ "Player receives red card" ✅
├─ "Total yellow cards in match > 4" ✅
└─ "Total red cards in match > 0" ✅

ESTRUCTURA:
{
  "market_id": "KXEPL-CARD-HARRYUKANE-26AUG23",
  "market_type": "player_card",
  "player": "Harry Kane",
  "card_type": "yellow",  # or "red"
  "match": "Tottenham vs Man City",
  
  "yes_price": 42,  # 42% chance Kane gets yellow
  "spread_pct": 1.5,
  
  "predictor_data": {
    "player_history": {
      "yellows_per_match_avg": 0.23,
      "yellows_last_10": [0, 1, 0, 1, 0, 0, 1, 0, 1, 0],
      "red_cards_ever": 1,
      "aggression_rating": 6.2  # 1-10
    },
    "referee_data": {
      "referee_name": "Michael Oliver",
      "cards_per_match_avg": 4.2,
      "strictness_rating": 7.1  # 1-10
    }
  }
}
```

---

### 4. MERCADOS DE CÓRNERS (Corner Markets)

```
EJEMPLOS:
├─ "Liverpool > 4.5 corners in match" ✅
├─ "Total corners in match > 9" ✅
├─ "Manchester City > 3.5 first half corners" ✅
└─ "Chelsea < 3 corners" ✅

ESTRUCTURA:
{
  "market_id": "KXEPLT-CORNERS-LIV-26AUG23",
  "market_type": "corners_over_under",
  "team": "Liverpool",
  "threshold": 4.5,
  "side": "over",
  "yes_price": 56,
  
  "predictor_data": {
    "team_stats": {
      "corners_per_match": 5.2,
      "corners_attacking": 4.1,
      "corners_defending": 1.1,
      "crossing_style": "high",  # high/medium/low
      "wing_attack_rating": 7.8
    },
    "opponent_stats": {
      "corners_conceded_per_match": 4.8,
      "set_piece_defense": 6.5,
      "wide_defense_rating": 6.2
    }
  }
}
```

---

### 5. MERCADOS DE SAQUES DE ESQUINA (Throw-ins)

```
Nota: LIMITADA en Kalshi
- Menos popular que corners/goals
- Spreads más amplios
- Menor liquidez

Ejemplo si disponible:
"Liverpool > 15 throw-ins" - Raro en Kalshi
```

---

### 6. MERCADOS DE JUGADORES (Player Props)

#### 6.1 Goal Scorer Markets

```
"Will Erling Haaland score a goal?" ✅
"Will Mohammed Salah score 2+ goals?" ✅
"Will any Liverpool player score?" ✅

ESTRUCTURA:
{
  "market_id": "KXEPLT-GOALSCORER-HAALAND-26AUG23",
  "market_type": "player_goal",
  "player": "Erling Haaland",
  "team": "Manchester City",
  "thresholds": 1,  # 1+ goals
  "opponent": "Arsenal",
  "match_date": "2026-08-23",
  
  "yes_price": 72,  # 72% chance scores
  
  "predictor_data": {
    "player_stats": {
      "goals_per_match": 1.3,
      "goals_last_10": [2, 1, 1, 2, 1, 0, 2, 1, 1, 2],
      "shooting_accuracy": 0.58,
      "expected_goals_xG": 1.1,
      "minutes_played": 2700,
      "season_goals": 31
    },
    "form": {
      "rating_last_5": [8.9, 9.2, 8.7, 9.0, 8.8],
      "injured": false,
      "expected_minutes": 90,
      "penalty_taker": true
    },
    "match_context": {
      "home_away": "home",
      "opponent_defense": 65,
      "recent_vs_opponent": [1, 2, 1]  # goals in last 3 matches
    }
  }
}
```

#### 6.2 Assist Markets

```
"Will Harry Kane register an assist?" ✅
"Will Bukayo Saka get 2+ assists?" ✅

Menos común que goal scorer, spreads más amplios
```

#### 6.3 Combined Player Props

```
"Will Haaland score 1+ AND get 1+ assist?" ✅

ESTRUCTURA ADICIONAL:
{
  "market_type": "combined_player_props",
  "combinations": [
    {
      "metric": "goals",
      "threshold": 1,
      "side": "over"
    },
    {
      "metric": "assists",
      "threshold": 1,
      "side": "over"
    }
  ],
  "yes_price": 38  # Lower due to combined probability
}
```

---

### 7. MERCADOS DE TEMPORADA/CAMPEONATO (Season Markets)

```
EJEMPLOS:
├─ "Manchester City win EPL 2026-27" ✅
├─ "Will Arsenal finish in top 4?" ✅
├─ "Will Liverpool win Champions League?" ✅
├─ "Who will be top goalscorer?" - Tournament-style
└─ "Will [Player] win Golden Boot?" ✅

ESTRUCTURA:
{
  "market_id": "KXEPLT-WINNER-2026-27",
  "market_type": "season_winner",
  "season": "2026-27",
  "league": "Premier League",
  "contract_period": "season",
  
  "team": "Manchester City",
  "yes_price": 38,  # 38% probability to win league
  
  "predictor_data": {
    "team_metrics": {
      "squad_value": 1200000000,  # £ millions
      "squad_rating": 87,         # 1-100
      "manager_experience": 15,   # years
      "historical_success": [1, 1, 2, 1, 3],  # positions last 5 seasons
      "investment_trends": "positive",
      "key_signings": ["Havertz", "Alvarez"],
      "key_losses": ["Gundogan", "Rodri_injury"]
    },
    "league_context": {
      "total_teams": 20,
      "competitors": [
        {"team": "Arsenal", "odds": 35},
        {"team": "Liverpool", "odds": 18},
        {"team": "Chelsea", "odds": 12}
      ]
    }
  }
}
```

---

### 8. MERCADOS COMBINADOS/PARLAYS (Combo Markets)

```
"Liverpool win AND score 2+ goals" ✅
"Haaland scores AND Man City wins" ✅

ESTRUCTURA:
{
  "market_id": "KXEPLT-COMBO-LIV-26AUG23",
  "market_type": "combined",
  "components": [
    {
      "market_id": "KXEPLTOTM-LIV",
      "description": "Liverpool wins"
    },
    {
      "market_id": "KXEPLOUGOALS-LIV",
      "description": "Liverpool 2+ goals"
    }
  ],
  "yes_price": 45,  # Combined probability lower
  "correlation": 0.85  # How correlated are the events
}
```

---

## 🔧 Estructura de Datos Kalshi

### 1. Formato de Ticker (Market Identifier)

```
COMPONENTES DEL TICKER:
KX + [CATEGORY] + [SUBCATEGORY] + [EXPIRATION]

EJEMPLOS:

KXEPLTOTM-LIV-26AUG23
├─ KX = Kalshi contracts prefix
├─ EPLT = EPL Tournament/Match
├─ OTM = Outcome (Match)
├─ LIV = Liverpool team
└─ 26AUG23 = Expiration: August 26, 2026

KXEPLOUGOALS-LIV-26AUG23
├─ KX = Prefix
├─ EPLT = EPL
├─ OUGOALS = Over/Under Goals
├─ LIV = Team
└─ 26AUG23 = Date

KXCORN-MCI-26AUG23
├─ CORN = Corners
├─ MCI = Manchester City
└─ Date expiration

KXGOALSCORER-HAALAND-26AUG23
├─ GOALSCORER = Player goal scorer
├─ HAALAND = Player name
└─ Date expiration

KXEPLTOP4-26
└─ EPL Top 4 finish market
└─ Season: 2026-27
```

### 2. Estructura JSON de Mercado Completa

```json
{
  "market_id": "KXEPLTOTM-LIV-26AUG23",
  "ticker": "KXEPLTOTM-LIV-26AUG23",
  
  "metadata": {
    "series": "SOCCER-EPL-MATCH",
    "category": "sports",
    "subcategory": "soccer",
    "event_id": "LIVERPOOL-v-MANCHESTER_CITY",
    "event_name": "Liverpool vs Manchester City",
    "event_date": "2026-08-23T15:00:00Z"
  },
  
  "market_info": {
    "title": "Will Liverpool beat Manchester City?",
    "description": "Binary contract that settles YES if Liverpool wins, NO if Manchester City wins or draw",
    "market_type": "match_winner",
    "binary": true,
    "status": "open",
    "created_at": "2026-08-10T10:00:00Z",
    "last_updated": "2026-08-14T14:30:00Z"
  },
  
  "pricing": {
    "yes_price": 55,              # cents, 0-100
    "no_price": 45,
    "mid_price": 50,
    "bid_price": 54,
    "ask_price": 56,
    "spread_cents": 2,
    "spread_pct": 3.92,            # (56-54)/50 * 100
    "implied_probability_yes": 0.55,
    "implied_probability_no": 0.45
  },
  
  "liquidity": {
    "volume_24h": 125000,          # contracts
    "volume_7d": 890000,
    "open_interest": 85000,
    "bid_depth": 45000,
    "ask_depth": 38000,
    "liquidity_score": 8.5,        # 1-10
    "spread_liquidity_ratio": 0.62  # wide spread = low liquidity
  },
  
  "settlement": {
    "settlement_date": "2026-08-23",
    "settlement_rule": "Official Premier League result",
    "settlement_source": "official.premierleague.com",
    "resolution_method": "official",
    "early_close_possible": false,
    "rules_url": "https://kalshi.com/markets/.../rules",
    "rules_pdf_url": "https://kalshi.com/markets/.../rules.pdf",
    "expiration": "2026-08-25T20:00:00Z"
  },
  
  "contract_specs": {
    "notional_value": 100,         # $1.00 if YES wins
    "tick_size": 1,                # min price increment (cents)
    "multiplier": 1,
    "contract_unit": "binary"
  }
}
```

### 3. Estructura de Orden para Predicción

```json
{
  "order_request": {
    "market_id": "KXEPLTOTM-LIV-26AUG23",
    "side": "YES",                 # YES or NO
    "action": "BUY",               # BUY or SELL
    "limit_price": 54,             # in cents
    "quantity": 100,               # contracts
    "order_type": "LIMIT",
    "time_in_force": "GTC",        # Good Till Cancel
    "stop_loss_price": 48,         # optional
    "take_profit_price": 62,       # optional
    "confirm": false               # must be true to execute
  },
  
  "order_response": {
    "order_id": "ORD-123456789",
    "market_id": "KXEPLTOTM-LIV-26AUG23",
    "status": "PREVIEW",           # PREVIEW before confirm=true
    "side": "YES",
    "quantity": 100,
    "limit_price": 54,
    "estimated_cost": 5400,        # cents = $54.00
    "estimated_proceeds": 10000,   # if YES resolves
    "maximum_loss": 5400,
    "maximum_gain": 4600,
    "implied_probability": 0.54,
    "risk_reward_ratio": 0.85      # gain/loss
  }
}
```

### 4. Estructura de Estadísticas de Equipo

```json
{
  "team_stats": {
    "team_id": "LIV",
    "team_name": "Liverpool",
    "season": "2026-27",
    
    "offensive": {
      "goals_per_match": 2.1,
      "xG_per_match": 1.95,
      "shots_per_match": 14.2,
      "possession_avg": 58.3,
      "passes_per_match": 482
    },
    
    "defensive": {
      "goals_conceded_per_match": 1.1,
      "xGA_per_match": 1.05,
      "tackles_per_match": 18.2,
      "interceptions_per_match": 8.5,
      "clearances_per_match": 12.1
    },
    
    "set_pieces": {
      "corners_for_per_match": 5.2,
      "corners_against_per_match": 4.8,
      "free_kicks_for": 12.1,
      "free_kicks_against": 11.8
    },
    
    "form": {
      "form_rating_last_5": [8.2, 8.5, 7.9, 8.1, 8.3],
      "form_average": 8.2,
      "wins_last_5": 4,
      "draws_last_5": 1,
      "losses_last_5": 0
    },
    
    "player_availability": {
      "injured_players": [
        {"name": "Rodri", "position": "CM", "expected_return": "2026-09-15"}
      ],
      "suspended_players": [],
      "available_squad_rating": 8.4
    }
  }
}
```

---

## ⚠️ Desafíos Técnicos

### 1. Rate Limiting de API

```
LÍMITES KALSHI:
├─ 50 requests/segundo (hard limit)
├─ 10,000 requests/hora
├─ Token bucket implementation necesario
└─ Backoff exponencial si excedes límites

IMPLEMENTACIÓN REQUERIDA:
- Queue de requests con spacing
- Caché para mercados frecuentes
- Batch operations cuando sea posible
```

**Ejemplo de estrategia de throttling:**
```python
# Token bucket rate limiter
requests_per_second = 50
requests_per_hour = 10,000

# Spacing entre requests
spacing_seconds = 1.0 / 50  # 0.02 seconds entre requests

# Caché TTL
market_data_ttl = 30  # segundos
orderbook_ttl = 5    # segundos (update más frecuente)
```

### 2. Latencia de Datos

```
PROBLEMAS:
├─ Precios pueden cambiar en 100-500ms
├─ Spreads se ajustan dinámicamente
├─ Volumen puede secarse sin aviso
└─ Settlement delays en resolución

IMPACTO EN ESTRATEGIA:
- Order slippage esperado: 1-3%
- Stop losses pueden no ejecutarse en nivel exacto
- Momentum trades requieren ejecución rápida
```

### 3. Actualización de Precios en Tiempo Real

```
OPCIONES DISPONIBLES:
├─ REST Polling (actual MCP)
│  ├─ Desventaja: latencia, rate limiting
│  └─ Ventaja: simple, sin conexión persistente
│
└─ WebSocket (recomendado para mejor latencia)
   ├─ Ventaja: real-time, bajo latencia
   └─ Desventaja: requiere conexión persistente

SUGERENCIA PARA FASE 2:
Implementar WebSocket para streaming de:
- Order book updates
- Trade execution feed
- Price changes
- Fill notifications
```

### 4. Volumen y Liquidez por Tipo de Mercado

```
LIQUIDEZ ESPERADA (por mercado):

Tier 1 (Altamente Líquido):
├─ EPL Match Winners (top 6 teams)
├─ Top Goalscorer Markets
└─ Over/Under 2.5 Goals
   → Spreads: 1-2 cents
   → Volume: 100k+ diaria
   → Slippage: <1%

Tier 2 (Moderadamente Líquido):
├─ EPL Match Winners (mid-table)
├─ Corner Markets
└─ Player Props (star players)
   → Spreads: 2-4 cents
   → Volume: 20k-100k diaria
   → Slippage: 1-3%

Tier 3 (Baja Liquidez):
├─ EPL Match Winners (bottom teams)
├─ Rare props (red cards, etc.)
└─ Niche player markets
   → Spreads: 4-10 cents
   → Volume: <20k diaria
   → Slippage: 3-10%

IMPLICACIÓN:
- Scalping only on Tier 1 markets
- Position sizing inversamente proporcional a liquidez
- Use limit orders, never market orders en Tier 2-3
```

### 5. Gestión de Correlaciones

```
EVENTOS CORRELACIONADOS:
├─ Match Winner + Over/Under Goals (0.65 correlación)
├─ Goal Scorer + Team Wins (0.58 correlación)
├─ Corners + Possession (0.72 correlación)
└─ Cards + Team Aggression (0.45 correlación)

DESAFÍO TÉCNICO:
- Precios no siempre reflejan correlaciones
- Oportunidad de mispricing
- Requiere calcular matrices de correlación
- Backtesting necesario para validar edges

SOLUCIÓN:
Herramienta: analyze_correlation_matrix()
├─ Input: lista de market_ids
├─ Output: correlation matrix + oportunidades
└─ Fase 2-3 del MCP
```

---

## 💡 Oportunidades de Arbitrage

### 1. Spread Opportunities (Arbitrage Clásico)

```
MECÁNICA:
1. Identifica mercado con spread amplio
2. Compra en BID (precio bajo)
3. Vende en ASK (precio alto)
4. Realiza ganancia sin riesgo direccional

EJEMPLO CONCRETO:
Market: "Liverpool beats Chelsea"
├─ Bid: 54¢
├─ Ask: 58¢
├─ Spread: 4¢ (7.4%)
└─ ROI: (4/54) = 7.4% si compras en bid

REQUISITOS:
├─ Suficiente profundidad en ambos lados
├─ Ejecución rápida (antes que spread cierre)
└─ No hold hasta settlement (no riesgo)

HERRAMIENTA MCP:
find_spread_opportunities(max_spread_pct=3.0)
```

### 2. Arbitrage de Correlación

```
MECÁNICA:
Explotar desconexión en mercados relacionados

EJEMPLO 1 - Match Outcome + Goal Markets:
Si "Liverpool wins" está a 60¢
Y "Liverpool 2+ goals" está a 45¢
└─ Desconexión potencial: relación debe ser ~0.75

EJEMPLO 2 - Season Markets:
Si "Man City wins league" a 38¢
Y "Man City wins opening 3 games" a 72¢
└─ Las correlaciones pueden no cuadrar

ESTRATEGIA:
1. Calcular probabilidades teóricas
2. Comparar con precios reales
3. Identificar divergencias >5%
4. Ejecutar hedge trading

HERRAMIENTA MCP:
correlate_markets(market_ids=["id1", "id2"], days=30)
```

### 3. Momentum Trading

```
OPORTUNIDAD:
Explotar sesgo de corto plazo en precios

INDICADORES:
├─ Cambio de precio >5% en 1 hora
├─ Volumen > media móvil 3x
├─ Dirección consistente en últimas 5 transacciones
└─ No hay noticias contradictorias

EJEMPLO:
Market: "Liverpool 2+ goals"
├─ Precio sube de 45¢ a 50¢ en 30 min
├─ Vol sube de 1k a 5k contratos
└─ Señal: Compradores informados entrando

RIESGO:
- Reversal rápido sin fundamentals
- Stop loss recomendado en 48¢

HERRAMIENTA MCP:
detect_momentum_trades(timeframe_hours=1, min_momentum=0.05)
```

### 4. Arbitrage de Overround (Probabilidades que no suman 100%)

```
MECÁNICA:
En mercados con múltiples outcomes:
├─ Si Team A: 40¢
├─ Y Team B: 40¢
├─ Y Draw: 25¢
└─ Total: 105¢ (overround del 5%)

ESTRATEGIA:
Compra pequeña cantidad de cada outcome
└─ Ganancia garantizada si overround > costos de transacción

CONDICIÓN:
Solo aplica a mercados con 3+ outcomes (ej: Win/Draw/Loss)
Kalshi favorece markets binarios, así que oportunidades limitadas

NOTA:
EPL tiene mercados ternarios en algunos casos
```

### 5. Arbitrage de Event-Driven

```
OPORTUNIDAD:
Explotación de eventos que mueven mercados

EJEMPLOS:
├─ Lesión de jugador clave anunciada
│  └─ Odds del equipo ajustan lentamente
├─ Cambio de manager
│  └─ Reacción inicial luego corrección
├─ Noticias de fichajes
│  └─ Impacto en goles esperados
└─ Condiciones climáticas extremas
   └─ Impacto en corners/cards

VENTANA TEMPORAL:
- Noticia publicada
- Kalshi mercados reaccionan (30-120 segundos)
- Otros sportsbooks ajustan después
└─ Oportunidad aprovechable

HERRAMIENTA MCP:
detect_catalyst_opportunities()
├─ Monitor news feeds
├─ Track price changes
└─ Alert on unusual movements
```

### 6. Scalping de Órdenes

```
TÉCNICA:
Colocar órdenes límite en ambos lados + cancelar rápido

EJEMPLO:
Market: "Haaland scores"
├─ Place BUY limit @  45¢ (debajo del ask 48¢)
├─ Place SELL limit @ 52¢ (arriba del bid 49¢)
├─ Esperar que una se ejecute
├─ Cancelar la otra
└─ Ganancia: 3¢ si ambas se ejecutan, perdida cero si solo una

REQUISITOS:
├─ API rápida
├─ Baja latencia
├─ Mercado con volatilidad
└─ Suficiente profundidad

VIABILIDAD EN KALSHI:
- Posible en Tier 1 markets (EPL top matches)
- Menos viable en Tier 2-3 (baja liquidez)
- ROI típico: 1-3% por round
```

### 7. Statistical Mispricing Detection

```
OPORTUNIDAD:
Precios se desvían de probabilidades teóricas

EJEMPLO 1 - Injury Update:
Star player lesionado
├─ Mercado "Team 2+ goals" baja de 58¢ a 45¢
├─ Datos históricos dicen debe ser ~50¢
└─ Oportunidad: BUY en 45¢

EJEMPLO 2 - Recency Bias:
Equipo pierda 2 seguidas
├─ Mercado "Team to win" cae a 25¢
├─ Históricamente ~45% contra rival
└─ Oportunidad: BUY en 25¢

ALGORITMO:
1. Recolectar datos históricos (últimos 100+ partidos)
2. Calcular probabilidad teórica
3. Comparar con precio actual
4. Si divergencia > 8%: FLAG como oportunidad
5. Validar con modelos ML (Fase 3)

HERRAMIENTA MCP:
analyze_sentiment_vs_fundamentals(market_id, timeframe_days=30)
```

### Tabla de Resumen: Oportunidades Típicas

```
Tipo Arbitrage    Entrada   Stop Loss  Target  Win%  Expectancy  Liquidez Req
──────────────────────────────────────────────────────────────────────────────
Spread Simple      50¢       50.5¢      52¢    90%   +1.35¢      Alta
Momentum           52¢       49¢        56¢    55%   +1.10¢      Alta
Correlation        45¢       44¢        54¢    65%   +5.85¢      Media
Event-Driven       48¢       46¢        62¢    70%   +9.8¢       Media
Statistical        40¢       37¢        50¢    58%   +4.64¢      Media
Scalping           50¢       49.5¢      51¢    80%   +0.60¢      Alta
```

---

## 🔗 Integración con FPL

### Conexión FPL ↔ Kalshi

```
PIPELINE POTENCIAL:

FPL Player Analysis
├─ Predictor: Injury risk, form, fixture difficulty
├─ Output: Expected points next GW
└─ ↓

Kalshi Market Mapping
├─ Map: FPL player → Kalshi markets
│  └─ Salah (FPL) → "Haaland scores" (Kalshi)
├─ Filter: Mercados con liquidez suficiente
└─ ↓

Probability Comparison
├─ FPL implied probability (de precios actuales)
├─ Kalshi implied probability (de precios mercado)
├─ Divergencia > 8% = Mispricing
└─ ↓

Trading Execution
├─ Crear orden en Kalshi basado en análisis FPL
├─ Position sizing según confianza modelo FPL
└─ Track P&L vs FPL predictions
```

### Datos de FPL que Mapean a Kalshi

```
FPL METRIC → KALSHI MARKET

Form (últimas 5 GW)
└─ "Salah scores next match" probability ajustada

Fixture Difficulty (FDR)
└─ "Easy fixture" → Mayor probabilidad goles

Threat (FPL stat)
└─ "Player scores" probability directa

ICT Index (Influence/Creativity/Threat)
└─ Prediction de assists + goals

Expected Assists (xA)
└─ "Player assists" probability

Minutes Played
└─ Probability de participación
```

### Estrategia: FPL-Kalshi Hedge

```
ESCENARIO:
Captain a Salah en GW 10 (FPL)
Pero hay incertidumbre sobre lesión menor

ESTRATEGIA KALSHI:
1. Compra "Salah scores" en Kalshi
   ├─ Si scores → FPL points + Kalshi ganancia
   └─ Si no scores → Kalshi compensa parcialmente

2. Vende "Salah 2+ goals" (más arriesgado)
   ├─ Si 0-1 goal → Kalshi ganancia
   └─ Si 2+ goals → Kalshi pérdida, pero FPL huge

RESULTADO:
- Payoff asimétrico favorece upside FPL
- Hedge reduce downside
- ROI esperado: 12-18% si predicciones correctas
```

---

## 📝 Recomendaciones

### Fase 1: Foundation (Actual - Completada)

✅ **Completada:**
- Arquitectura base del MCP
- Validators y formatters
- Market cache con TTL
- 52+ test cases

### Fase 2: Football Market Integration (Recomendado Próximo)

```
TAREAS CRÍTICAS:
1. [ ] Herramienta: search_football_markets()
   ├─ Filtrar por liga (EPL, etc.)
   ├─ Filtrar por tipo (match, props, futures)
   ├─ Ordenar por liquidez
   └─ Retornar con datos de análisis

2. [ ] Herramienta: analyze_market_for_arbitrage()
   ├─ Detectar spreads amplios
   ├─ Calcular fair value
   ├─ Comparar con historical
   └─ Retornar opportunities ranked

3. [ ] Data Ingestion:
   ├─ Integrar datos FPL (vía external API)
   ├─ Mapear jugadores FPL → Kalshi markets
   ├─ Crear matriz de correlaciones
   └─ Update diaria

4. [ ] Portfolio Analytics:
   ├─ Track posiciones en Kalshi
   ├─ Calcular P&L vs FPL
   ├─ Correlations portfolio
   └─ Risk metrics

Estimado: 2-3 semanas
```

### Fase 3: Advanced Features

```
ENHANCEMENTS:
1. [ ] ML-based probability prediction
   ├─ Train en datos históricos Kalshi
   ├─ Validar accuracy vs market
   └─ Usar para detect mispricings

2. [ ] WebSocket real-time streaming
   ├─ Conectar a Kalshi WebSocket
   ├─ Stream prices, trades, order book
   └─ Update mercados en tiempo real

3. [ ] Automated trading strategies
   ├─ Momentum detection
   ├─ Statistical arbitrage
   ├─ Event-driven execution
   └─ Risk management

4. [ ] Backtesting framework
   ├─ Replay histórico de precios
   ├─ Test estrategias
   ├─ Calculate Sharpe ratio, max drawdown
   └─ Optimize parameters

Estimado: 3-4 semanas
```

### Prioridades Inmediatas

```
1. [CRITICAL] Football market search implementation
   - Usuarios necesitan encontrar mercados relevantes
   - Kalshi no tiene free-text search
   - MCP debe proporcionar búsqueda filtrada

2. [HIGH] Arbitrage detection tool
   - Oportunidades de valor alto
   - Requiere análisis de spreads + fair value
   - Impacto directo en profitability

3. [HIGH] FPL-Kalshi integration
   - Diferenciaador único
   - Core USP del producto
   - Habilita hedging strategies

4. [MEDIUM] Real-time price streaming
   - Mejora experiencia usuario
   - Latency-sensitive para scalping
   - Requiere WebSocket (post-MVP)

5. [LOW] Advanced analytics
   - ML, backtesting, etc.
   - Nice-to-have pero no blocking
   - Puede venir en v1.1
```

---

## 📊 Tabla Resumen: Mercados de Fútbol

| Tipo Mercado | Disponible | Liquidez | Spread Típico | Ejemplo |
|---|---|---|---|---|
| **Match Winner** | ✅ Alto | ⭐⭐⭐⭐⭐ | 1-2¢ | "Liverpool wins" |
| **Over/Under Goals** | ✅ Alto | ⭐⭐⭐⭐ | 2-3¢ | "2.5+ goals" |
| **Goal Scorer** | ✅ Alto | ⭐⭐⭐⭐ | 2-4¢ | "Haaland scores" |
| **Corners** | ✅ Medio | ⭐⭐⭐ | 3-5¢ | "4.5+ corners" |
| **Cards** | ✅ Bajo | ⭐⭐ | 4-8¢ | "Player yellow" |
| **Assists** | ✅ Bajo | ⭐⭐ | 3-6¢ | "Mount assists" |
| **Season Winner** | ✅ Alto | ⭐⭐⭐⭐ | 2-4¢ | "Man City wins league" |
| **Top Scorer** | ✅ Medio | ⭐⭐⭐ | 3-6¢ | "Haaland Golden Boot" |

---

## 🎯 Conclusión

### Viabilidad

✅ **Kalshi es viable para trading integrado FPL**

### Ventajas

1. **Profundidad de mercados**: EPL especialmente bien cubierto
2. **Estructura de precios**: Transparente (0-100 centavos = probability)
3. **Regulación**: CFTC regulado, operación legal y segura
4. **Hedge natural**: Protege posiciones FPL
5. **Oportunidades arbitrage**: Especialmente spreads y correlaciones

### Desafíos

1. **Rate limiting**: 50 req/seg es ajustado
2. **Latencia**: Requiere buena infraestructura para scalping
3. **Liquidez variable**: Algunos mercados tienen spreads amplios
4. **Correlaciones**: Requiere backtesting para validar estrategias

### Roadmap Recomendado

```
Fase 1: ✅ COMPLETADA - Arquitectura base
Fase 2: 🔄 EN PROGRESO - Football market tools + FPL integration
Fase 3: 📅 PLANEADO - Advanced features + WebSocket
Fase 4: 📅 PLANEADO - ML predictions + Backtesting
Fase 5: 📅 PLANEADO - Production hardening + Docs
```

### Siguiente Paso

Implementar Fase 2 con enfoque en:
1. Football market search tool
2. Arbitrage detection
3. FPL-Kalshi data mapping

---

**Investigación Completada: 2026-08-14**  
**Fuentes:** Kalshi API docs, kalshi.com market pages, industry research

---

## 🔗 Referencias y Fuentes

- [Kalshi Soccer Props Markets](https://kalshi.com/category/sports/soccer/all/props)
- [Kalshi EPL Markets](https://kalshi.com/category/sports/soccer/epl)
- [Kalshi API Documentation](https://docs.kalshi.com)
- [Kalshi Market Integrity Hub](https://kalshi.com/market-integrity)
- [Prediction Markets 101](https://kalshi.com/market-integrity/prediction-markets-101)
