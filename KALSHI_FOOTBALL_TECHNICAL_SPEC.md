# Especificación Técnica: Integración Kalshi Football Markets
**Fecha:** 2026-08-14  
**Versión:** 1.0  
**Status:** Listo para Implementación (Fase 2)

---

## 📋 Contenidos

1. [Models de Datos](#models-de-datos)
2. [Herramientas MCP Requeridas](#herramientas-mcp-requeridas)
3. [Ejemplos de Código](#ejemplos-de-código)
4. [Workflows de Usuario](#workflows-de-usuario)
5. [Validación y Testing](#validación-y-testing)

---

## 🏗️ Models de Datos

### Pydantic Models para Football Markets

```python
# models/football_markets.py

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from decimal import Decimal

class FootballMarketType(str, Enum):
    """Tipos de mercados disponibles"""
    MATCH_WINNER = "match_winner"           # 1X2
    OVER_UNDER_GOALS = "over_under_goals"   # O/U totales
    PLAYER_GOALS = "player_goals"           # Goleador
    PLAYER_ASSISTS = "player_assists"       # Asistencias
    PLAYER_CARDS = "player_cards"           # Tarjetas
    CORNERS = "corners"                     # Córners
    DOUBLE_CHANCE = "double_chance"         # 1X, X2, 12
    BOTH_TEAMS_SCORE = "both_teams_score"   # BTTS
    CORRECT_SCORE = "correct_score"         # Resultado exacto
    SEASON_WINNER = "season_winner"         # Ganador temporada
    TOP_GOALSCORER = "top_goalscorer"       # Máximo goleador


class FootballMarket(BaseModel):
    """Representación de un mercado de fútbol en Kalshi"""
    
    # Identificadores
    market_id: str = Field(..., description="ID único de Kalshi")
    ticker: str = Field(..., description="Ticker format KXEPLT...")
    series_id: str = Field(..., description="ID de la serie")
    
    # Información del evento
    event_id: str
    event_name: str = Field(..., description="ej: 'Liverpool vs Manchester City'")
    event_date: datetime
    league: str = Field(..., description="ej: 'EPL', 'Champions League'")
    
    # Detalles del mercado
    market_type: FootballMarketType
    title: str = Field(..., description="Título del mercado")
    description: str
    
    # Componentes específicos (varían por tipo)
    home_team: Optional[str] = None
    away_team: Optional[str] = None
    player_name: Optional[str] = None        # Para player props
    threshold: Optional[float] = None         # Para O/U (ej: 2.5)
    
    # Pricing
    yes_price: int = Field(..., ge=0, le=100, description="Precio en centavos")
    no_price: int = Field(..., ge=0, le=100)
    bid_price: int
    ask_price: int
    spread_pct: float = Field(..., description="Spread como porcentaje")
    implied_probability_yes: float = Field(..., ge=0, le=1)
    
    # Liquidez
    volume_24h: float = Field(default=0, description="Volumen últimas 24h")
    open_interest: float = Field(default=0, description="Contratos abiertos")
    liquidity_score: float = Field(..., ge=1, le=10, description="1-10 scale")
    
    # Settlement
    settlement_date: datetime
    settlement_rule: str
    expiration: datetime
    status: str = Field(default="open", description="open, paused, closed, resolved")
    
    # Metadata
    created_at: datetime
    last_updated: datetime
    rules_url: Optional[str] = None
    

class FootballTeamStats(BaseModel):
    """Estadísticas de equipo para análisis predictivo"""
    
    team_id: str
    team_name: str
    season: str
    
    # Ofensiva
    goals_per_match: float
    xG_per_match: float
    shots_per_match: float
    possession_avg: float
    
    # Defensa
    goals_conceded_per_match: float
    xGA_per_match: float
    tackles_per_match: float
    
    # Set pieces
    corners_per_match: float
    free_kicks_per_match: float
    
    # Forma
    form_rating_last_5: List[float]
    wins_last_5: int
    draws_last_5: int
    losses_last_5: int
    
    # Disponibilidad
    injured_players: List[dict] = Field(default_factory=list)
    suspended_players: List[dict] = Field(default_factory=list)
    

class FootballPlayerStats(BaseModel):
    """Estadísticas de jugador para props"""
    
    player_id: str
    player_name: str
    team_id: str
    position: str  # FW, MF, DF, GK
    
    # Goles
    goals_per_match: float
    goals_last_10: List[int]
    xG_per_match: float
    shot_accuracy: float
    
    # Asistencias
    assists_per_match: float
    assists_last_10: List[int]
    xA_per_match: float
    
    # Disciplina
    yellow_cards_per_match: float
    red_cards_total: int
    
    # Disponibilidad
    injured: bool = False
    expected_return: Optional[datetime] = None
    form_last_5: List[float]
    

class ArbitrageOpportunity(BaseModel):
    """Oportunidad de arbitrage detectada"""
    
    opportunity_id: str
    market_id: str
    market_type: str
    
    # Descripción
    title: str
    description: str
    opportunity_type: str  # "spread", "correlation", "statistical", etc.
    
    # Análisis
    thesis: str
    confidence_score: float = Field(..., ge=0, le=10)
    expected_roi_pct: float
    
    # Precios
    entry_price: int  # centavos
    target_price: int
    stop_loss_price: int
    position_size: int  # contratos
    
    # Riesgo/Reward
    max_gain_cents: int
    max_loss_cents: int
    risk_reward_ratio: float
    win_probability: float = Field(..., ge=0, le=1)
    
    # Ejecución
    recommended_action: str  # BUY, SELL
    recommended_side: str    # YES, NO
    liquidation_concerns: Optional[str] = None
    
    # Metadata
    detected_at: datetime
    expires_at: datetime  # Oportunidad tiene ventana temporal
```

---

## 🔧 Herramientas MCP Requeridas

### Fase 2: Football Market Tools (6 herramientas)

#### 1. `search_football_markets()`

```python
# tools/football_markets.py

class SearchFootballMarketsInput(BaseModel):
    league: Optional[str] = Field(
        None, 
        description="Filtro por liga: 'EPL', 'Champions League', etc."
    )
    match_team: Optional[str] = Field(
        None,
        description="Filtro por equipo (ej: 'Liverpool')"
    )
    market_type: Optional[str] = Field(
        None,
        description="Tipo de mercado: 'match_winner', 'goals', 'player_props'"
    )
    min_liquidity: int = Field(
        default=1000,
        description="Score de liquidez mínimo (1-10)"
    )
    max_spread_pct: float = Field(
        default=10.0,
        description="Máximo spread aceptable (%)"
    )
    only_active: bool = Field(
        default=True,
        description="Solo mercados abiertos"
    )
    limit: int = Field(
        default=10,
        description="Número máximo de resultados"
    )


async def search_football_markets(
    input: SearchFootballMarketsInput
) -> dict:
    """
    Busca mercados de fútbol con filtros avanzados
    
    Returns:
    {
        "total_found": 45,
        "filtered_results": 12,
        "markets": [
            {
                "market_id": "KXEPLTOTM-LIV-26AUG23",
                "event": "Liverpool vs Manchester City",
                "type": "match_winner",
                "yes_price": 55,
                "liquidity_score": 9.2,
                "spread_pct": 1.8
            },
            ...
        ],
        "recommendations": [
            "EPL markets have best liquidity",
            "3 opportunities with spread < 2%"
        ]
    }
    """
```

#### 2. `get_football_market_analysis()`

```python
class GetFootballMarketAnalysisInput(BaseModel):
    market_id: str = Field(..., description="Market ID to analyze")
    include_historical: bool = Field(default=True)
    include_correlation: bool = Field(default=True)
    days_back: int = Field(default=30)


async def get_football_market_analysis(
    input: GetFootballMarketAnalysisInput
) -> dict:
    """
    Análisis profundo de un mercado
    
    Returns:
    {
        "market_info": {...},
        "pricing_analysis": {
            "fair_value_estimate": 52,
            "deviation_from_fair": 3,  # centavos
            "mispricing_confidence": 7.5,
            "why_mispriced": "Team's form improved 20%, market hasn't adjusted"
        },
        "sentiment_analysis": {
            "market_consensus": 55,  # implied probability
            "historical_accuracy": 0.58,
            "latest_trades": [55, 54, 55, 56]
        },
        "volume_analysis": {
            "volume_trend": "up",
            "buyers_pressure": 0.62,  # % of buying vs selling
            "institutional_activity": "likely"
        },
        "risk_assessment": {
            "liquidity_risk": 2,  # 1-10
            "execution_slippage": 1.2,  # centavos esperados
            "settlement_risk": "low"
        }
    }
    """
```

#### 3. `detect_football_arbitrage()`

```python
class DetectFootballArbitrageInput(BaseModel):
    league: Optional[str] = Field(None)
    lookback_hours: int = Field(default=24)
    min_roi_pct: float = Field(default=2.0)
    min_liquidity: float = Field(default=3.0)


async def detect_football_arbitrage(
    input: DetectFootballArbitrageInput
) -> dict:
    """
    Detecta oportunidades de arbitrage
    
    Returns:
    {
        "scan_time": "2026-08-14T14:30:00Z",
        "opportunities_found": 3,
        "total_markets_scanned": 156,
        "opportunities": [
            {
                "rank": 1,
                "type": "spread_arbitrage",
                "market_id": "KXEPLTOTM-LIV-26AUG23",
                "market": "Liverpool vs Manchester City",
                "entry": 54,
                "target": 58,
                "position_size": 100,
                "expected_roi_pct": 7.4,
                "liquidity_score": 9.1,
                "confidence": 8.5,
                "reason": "Wide 4¢ spread with deep liquidity",
                "expires_in_minutes": 180
            },
            {
                "rank": 2,
                "type": "correlation_arbitrage",
                "markets": ["KXEPLTOTM-LIV", "KXEPLOUGOALS-LIV"],
                "thesis": "Liverpool win probability should imply 2+ goals",
                "current_divergence": 8.2,
                "expected_roi_pct": 5.8,
                "confidence": 7.2
            },
            {
                "rank": 3,
                "type": "statistical_mispricing",
                "market": "Haaland scores",
                "fair_value": 75,
                "market_price": 68,
                "upside_pct": 10.3,
                "confidence": 6.8,
                "reason": "Form improved but market not reflecting"
            }
        ],
        "portfolio_exposure": {
            "total_capital_available": 100000,
            "recommended_allocation": 45000,
            "concentration_risk": "low"
        }
    }
    """
```

#### 4. `get_player_props_markets()`

```python
class GetPlayerPropsInput(BaseModel):
    player_name: str
    league: str = "EPL"
    market_types: Optional[List[str]] = Field(
        None,
        description="['goals', 'assists', 'cards']"
    )
    include_stats: bool = Field(default=True)
    next_n_matches: int = Field(default=3)


async def get_player_props_markets(
    input: GetPlayerPropsInput
) -> dict:
    """
    Obtiene todos los props markets para un jugador
    
    Returns:
    {
        "player": {
            "name": "Erling Haaland",
            "team": "Manchester City",
            "position": "FW",
            "stats": {
                "goals_per_match": 1.3,
                "assists_per_match": 0.25,
                "form_last_5": [1, 2, 1, 2, 1]
            }
        },
        "markets": [
            {
                "market_id": "KXEPLT-GOALS-HAALAND-26AUG23",
                "type": "player_goals",
                "title": "Will Erling Haaland score?",
                "yes_price": 72,
                "spread_pct": 1.8,
                "match": "Man City vs Arsenal",
                "match_date": "2026-08-23"
            },
            {
                "market_id": "KXEPLT-ASSIST-HAALAND-26AUG23",
                "type": "player_assists",
                "title": "Will Erling Haaland assist?",
                "yes_price": 38,
                "spread_pct": 2.4
            }
        ],
        "analysis": {
            "form_trend": "positive",
            "fixture_difficulty": "medium",
            "vs_opponent_history": [1, 2, 1],
            "recommended_markets": [
                "Goals (YES at 72) - Strong form, easy fixture"
            ]
        }
    }
    """
```

#### 5. `analyze_team_performance()`

```python
class AnalyzeTeamPerformanceInput(BaseModel):
    team_name: str
    league: str = "EPL"
    lookback_matches: int = Field(default=10)
    include_upcoming: bool = Field(default=True)


async def analyze_team_performance(
    input: AnalyzeTeamPerformanceInput
) -> dict:
    """
    Análisis completo de desempeño de equipo
    
    Returns:
    {
        "team": "Liverpool",
        "season": "2026-27",
        "recent_form": {
            "last_5_results": ["W", "W", "D", "W", "L"],
            "points_per_game": 2.2,
            "trend": "positive",
            "rating": 8.1
        },
        "offensive": {
            "goals_per_match": 2.1,
            "xG_per_match": 1.95,
            "top_scorers": [
                {"player": "Salah", "goals": 8},
                {"player": "Jota", "goals": 5}
            ],
            "corner_conversion": 0.12
        },
        "defensive": {
            "goals_conceded_per_match": 1.1,
            "xGA_per_match": 1.05,
            "clean_sheets": 4,
            "error_rate": 0.15
        },
        "upcoming_fixtures": [
            {
                "opponent": "Manchester City",
                "difficulty": 9,
                "home_away": "away",
                "date": "2026-08-23",
                "expected_goals": 1.8,
                "expected_goals_conceded": 1.2
            }
        ],
        "market_implications": {
            "over_2_5_goals_probability": 0.62,
            "team_to_win_probability": 0.48,
            "recommended_markets": ["Over 1.5 goals at 62¢"]
        }
    }
    """
```

#### 6. `compare_fpl_kalshi_opportunities()`

```python
class CompareFPLKalshiInput(BaseModel):
    fpl_position: str  # "captain_pick", "differential", "asset"
    player_name: str
    gameweek: int


async def compare_fpl_kalshi_opportunities(
    input: CompareFPLKalshiInput
) -> dict:
    """
    Compara oportunidad FPL con precios Kalshi
    
    Returns:
    {
        "fpl_analysis": {
            "player": "Erling Haaland",
            "position": "FW",
            "expected_fpl_points": 8.2,
            "injury_risk": 0.15,
            "fixture_difficulty": 3,
            "ownership": 28.5,
            "form": "excellent"
        },
        "kalshi_markets": {
            "player_goals": {
                "market_id": "KXEPLT-GOALS-HAALAND-26AUG23",
                "price": 72,
                "fair_value_estimate": 74,
                "implied_probability": 0.72,
                "recommendation": "HOLD"
            },
            "team_goals": {
                "market_id": "KXEPLT-GOALS-MCI-26AUG23",
                "price": 65,
                "correlation_with_player": 0.68
            }
        },
        "hedging_strategy": {
            "captain_haaland_fpl": true,
            "hedge_option_1": {
                "action": "BUY 100 'Haaland scores' at 72¢",
                "reason": "Hedge downside if non-performance",
                "cost": 7200,
                "payoff_if_scores": 10000,
                "payoff_if_not_scores": 0,
                "net_fpl_impact": "upside capture + downside protection"
            },
            "hedge_option_2": {
                "action": "SELL 50 'Haaland assists' at 38¢",
                "reason": "Less likely, captures premium",
                "expected_profit": 1900,
                "risk": "capped at 1900"
            }
        },
        "summary": "FPL position is strong. Light hedge recommended to reduce variance."
    }
    """
```

---

## 💻 Ejemplos de Código

### Ejemplo 1: Búsqueda y Filtrado de Mercados

```python
# examples/football_market_search.py

from mcp_server_kalshi.tools.football_markets import search_football_markets

async def find_epl_opportunities():
    """Busca oportunidades de trading en EPL"""
    
    # Búsqueda 1: Todos los mercados match winners con baja liquidez
    input1 = SearchFootballMarketsInput(
        league="EPL",
        market_type="match_winner",
        min_liquidity=7.0,
        max_spread_pct=3.0,
        limit=20
    )
    results1 = await search_football_markets(input1)
    
    for market in results1["markets"]:
        print(f"Market: {market['event']}")
        print(f"  Type: {market['type']}")
        print(f"  Price YES: {market['yes_price']}¢")
        print(f"  Spread: {market['spread_pct']}%")
        print(f"  Liquidity: {market['liquidity_score']}/10")
        print()
    
    # Búsqueda 2: Player props para top scorers
    input2 = SearchFootballMarketsInput(
        league="EPL",
        market_type="player_props",
        match_team="Manchester City",
        min_liquidity=6.0,
        limit=15
    )
    results2 = await search_football_markets(input2)
    
    # Análisis de oportunidades
    opportunities = []
    for market in results2["markets"]:
        if market["spread_pct"] < 3.0 and market["liquidity_score"] > 7.0:
            opportunities.append({
                "market_id": market["market_id"],
                "spread_pct": market["spread_pct"],
                "quality_score": market["liquidity_score"] / market["spread_pct"]
            })
    
    # Ordenar por score de calidad
    opportunities.sort(key=lambda x: x["quality_score"], reverse=True)
    
    print("Top 5 Oportunidades:")
    for i, opp in enumerate(opportunities[:5], 1):
        print(f"{i}. {opp['market_id']} - Spread: {opp['spread_pct']}%")


if __name__ == "__main__":
    import asyncio
    asyncio.run(find_epl_opportunities())
```

### Ejemplo 2: Detección de Arbitrage

```python
# examples/arbitrage_detection.py

from mcp_server_kalshi.tools.football_markets import detect_football_arbitrage

async def find_and_execute_arbitrage():
    """Detecta y ejecuta arbitrage de spreads"""
    
    # Escanear todas las ligas por oportunidades
    input_data = DetectFootballArbitrageInput(
        league=None,  # Todas las ligas
        lookback_hours=6,
        min_roi_pct=2.5,
        min_liquidity=5.0
    )
    
    opportunities = await detect_football_arbitrage(input_data)
    
    print(f"Oportunidades encontradas: {opportunities['opportunities_found']}")
    print(f"Mercados escaneados: {opportunities['total_markets_scanned']}")
    print()
    
    for opp in opportunities["opportunities"]:
        print(f"Rank {opp['rank']}: {opp['type'].upper()}")
        print(f"  Market: {opp['market']}")
        print(f"  Entry: {opp['entry']}¢")
        print(f"  Target: {opp['target']}¢")
        print(f"  Expected ROI: {opp['expected_roi_pct']}%")
        print(f"  Confidence: {opp['confidence']}/10")
        print(f"  Reason: {opp['reason']}")
        print(f"  Expires in: {opp['expires_in_minutes']} minutes")
        print()
        
        # Estrategia de ejecución
        if opp["type"] == "spread_arbitrage":
            print(f"  STRATEGY: BUY {opp['position_size']} contracts at {opp['entry']}¢")
            print(f"           SELL {opp['position_size']} contracts at {opp['target']}¢")
            print(f"           Est. Profit: ${(opp['target'] - opp['entry']) * opp['position_size'] / 100:.2f}")
            print()


if __name__ == "__main__":
    import asyncio
    asyncio.run(find_and_execute_arbitrage())
```

### Ejemplo 3: Análisis FPL-Kalshi

```python
# examples/fpl_kalshi_integration.py

from mcp_server_kalshi.tools.football_markets import (
    compare_fpl_kalshi_opportunities,
    get_player_props_markets
)

async def hedge_fpl_captain():
    """Cubre posición de capitán en FPL con trading Kalshi"""
    
    # Análisis del capitán elegido en FPL
    captain_analysis = await compare_fpl_kalshi_opportunities(
        CompareFPLKalshiInput(
            fpl_position="captain_pick",
            player_name="Erling Haaland",
            gameweek=1
        )
    )
    
    print(f"FPL Captain: {captain_analysis['fpl_analysis']['player']}")
    print(f"Expected Points: {captain_analysis['fpl_analysis']['expected_fpl_points']}")
    print(f"Injury Risk: {captain_analysis['fpl_analysis']['injury_risk'] * 100:.1f}%")
    print(f"Form: {captain_analysis['fpl_analysis']['form']}")
    print()
    
    # Estrategia de cobertura
    print("HEDGING STRATEGY:")
    for i, option in enumerate([
        captain_analysis['hedging_strategy']['hedge_option_1'],
        captain_analysis['hedging_strategy']['hedge_option_2']
    ], 1):
        print(f"\nOption {i}:")
        print(f"  Action: {option['action']}")
        print(f"  Reason: {option['reason']}")
        if "cost" in option:
            print(f"  Cost: ${option['cost']/100:.2f}")
        if "expected_profit" in option:
            print(f"  Expected Profit: ${option['expected_profit']/100:.2f}")
    
    print(f"\nSummary: {captain_analysis['summary']}")


async def analyze_player_props():
    """Análisis profundo de player props"""
    
    player_analysis = await get_player_props_markets(
        GetPlayerPropsInput(
            player_name="Mohamed Salah",
            league="EPL",
            include_stats=True
        )
    )
    
    print(f"Player: {player_analysis['player']['name']}")
    print(f"Team: {player_analysis['player']['team']}")
    print(f"Form (last 5): {player_analysis['player']['stats']['form_last_5']}")
    print(f"Goals/Match: {player_analysis['player']['stats']['goals_per_match']}")
    print()
    
    print("Available Markets:")
    for market in player_analysis['markets']:
        print(f"  {market['type'].upper()}: {market['yes_price']}¢ (spread {market['spread_pct']}%)")
    
    print(f"\nRecommendations:")
    for rec in player_analysis['analysis']['recommended_markets']:
        print(f"  - {rec}")


if __name__ == "__main__":
    import asyncio
    
    print("=" * 60)
    print("FPL CAPTAIN HEDGE ANALYSIS")
    print("=" * 60)
    asyncio.run(hedge_fpl_captain())
    
    print("\n" + "=" * 60)
    print("PLAYER PROPS ANALYSIS")
    print("=" * 60)
    asyncio.run(analyze_player_props())
```

---

## 🔄 Workflows de Usuario

### Workflow 1: Buscar y Ejecutar Trade

```
User: "search_football_markets(league='EPL', market_type='match_winner')"
  ↓
Tool: Busca 150+ mercados EPL
  ├─ Filtra por liquidez
  ├─ Calcula spreads
  └─ Ordena por calidad
  ↓
Tool Return: Top 10 mercados con detalles
  ├─ "Liverpool vs Manchester City" - 55¢ (spread 1.8%)
  ├─ "Arsenal vs Chelsea" - 48¢ (spread 2.1%)
  └─ ...
  ↓
User: "get_football_market_analysis(market_id='KXEPLTOTM-LIV')"
  ↓
Tool: Análisis profundo
  ├─ Pricing analysis (fair value)
  ├─ Sentiment analysis (trading activity)
  ├─ Volume trends
  └─ Risk assessment
  ↓
Tool Return: Análisis detallado con recomendación
  ├─ Fair value: 52¢ vs market 55¢
  ├─ Mispriced por: 3 centavos (5.8%)
  ├─ Confidence: 7.5/10
  └─ Recomendación: PASS (no suficiente margin)
  ↓
User: "detect_football_arbitrage()"
  ↓
Tool: Identifica 3 oportunidades de alto score
  ├─ Spread arbitrage en top match
  ├─ Correlation arbitrage entre related markets
  └─ Statistical mispricing en player props
  ↓
Tool Return: Top opportunities ranked
  ├─ #1: Spread arbitrage - 7.4% ROI
  ├─ #2: Correlation arb - 5.8% ROI
  └─ #3: Statistical - 3.2% ROI
  ↓
User: "create_order(market_id='...', side='YES', price=54, quantity=100)"
  ↓
Tool: Preview de orden
  ├─ Mostrar costo estimado: $54
  ├─ Mostrar ganancia potencial: $46 si wins
  └─ Pedir confirmación
  ↓
User: "create_order(..., confirm=true)"
  ↓
Tool: Ejecuta orden
  ├─ Submite a Kalshi API
  └─ Retorna confirmación: Order ID, status
```

### Workflow 2: FPL Captain Hedging

```
User: "compare_fpl_kalshi_opportunities(player='Haaland', position='captain')"
  ↓
Tool: Análisis cruzado FPL-Kalshi
  ├─ FPL: expected points 8.2, injury risk 15%, form excellent
  ├─ Kalshi: "Haaland scores" at 72¢ (implied 72% probability)
  ├─ Compare FPL expected vs Kalshi pricing
  └─ Genera hedge recommendations
  ↓
Tool Return: Hedging strategy
  ├─ "Captain Haaland is strong pick"
  ├─ "Kalshi 'scores' market fairly valued at 72¢"
  ├─ "Light hedge recommended: buy 50-100 contracts"
  └─ "Expected net impact: +2.3 FPL points if Haaland underperforms"
  ↓
User: "create_order(market_id='HAALAND-GOALS', side='YES', price=72, quantity=75)"
  ↓
Tool: Hedge execution
  ├─ Costo: $54
  ├─ Payoff si scores: +$25 (plus FPL captain bonus)
  ├─ Payoff si no scores: -$54 (partially offsets FPL loss)
  └─ Ask for confirmation
```

---

## ✅ Validación y Testing

### Unit Tests para Football Markets

```python
# tests/unit/test_football_markets.py

import pytest
from datetime import datetime, timedelta
from mcp_server_kalshi.models.football_markets import (
    FootballMarket,
    FootballMarketType,
    ArbitrageOpportunity
)

class TestFootballMarketModel:
    """Test Pydantic models"""
    
    def test_market_creation(self):
        """Test creación de mercado válido"""
        market = FootballMarket(
            market_id="KXEPLTOTM-LIV-26AUG23",
            ticker="KXEPLTOTM-LIV-26AUG23",
            series_id="EPL-MATCHES",
            event_id="LIV-v-MCI",
            event_name="Liverpool vs Manchester City",
            event_date=datetime.now() + timedelta(days=10),
            league="EPL",
            market_type=FootballMarketType.MATCH_WINNER,
            title="Will Liverpool beat Manchester City?",
            description="Market for Liverpool match winner",
            home_team="Liverpool",
            away_team="Manchester City",
            yes_price=55,
            no_price=45,
            bid_price=54,
            ask_price=56,
            spread_pct=3.7,
            implied_probability_yes=0.55,
            volume_24h=125000,
            open_interest=85000,
            liquidity_score=8.5,
            settlement_date=datetime.now() + timedelta(days=10),
            settlement_rule="Official result",
            expiration=datetime.now() + timedelta(days=11),
            created_at=datetime.now(),
            last_updated=datetime.now()
        )
        
        assert market.market_id == "KXEPLTOTM-LIV-26AUG23"
        assert market.yes_price == 55
        assert market.spread_pct == 3.7
    
    def test_price_validation(self):
        """Test validación de precios (0-100)"""
        with pytest.raises(ValueError):
            FootballMarket(
                # ... other fields ...
                yes_price=105,  # Invalid: > 100
            )
    
    def test_arbitrage_opportunity(self):
        """Test creación de oportunidad de arbitrage"""
        opp = ArbitrageOpportunity(
            opportunity_id="ARB-001",
            market_id="KXEPLTOTM-LIV-26AUG23",
            market_type="match_winner",
            title="Spread arbitrage in LIV match",
            description="Wide bid-ask spread provides arbitrage",
            opportunity_type="spread",
            thesis="Market inefficiency due to low volume",
            confidence_score=8.5,
            expected_roi_pct=7.4,
            entry_price=54,
            target_price=58,
            stop_loss_price=52,
            position_size=100,
            max_gain_cents=400,
            max_loss_cents=200,
            risk_reward_ratio=2.0,
            win_probability=0.9,
            recommended_action="BUY",
            recommended_side="YES",
            detected_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=4)
        )
        
        assert opp.risk_reward_ratio == 2.0
        assert opp.win_probability == 0.9


class TestSearchFootballMarkets:
    """Test search functionality"""
    
    @pytest.mark.asyncio
    async def test_search_by_league(self):
        """Test búsqueda por liga"""
        input_data = SearchFootballMarketsInput(
            league="EPL",
            limit=20
        )
        result = await search_football_markets(input_data)
        
        assert "markets" in result
        assert len(result["markets"]) <= 20
        # Todos deben ser de EPL
        # assert all(m["league"] == "EPL" for m in result["markets"])
    
    @pytest.mark.asyncio
    async def test_spread_filtering(self):
        """Test filtrado por spread máximo"""
        input_data = SearchFootballMarketsInput(
            league="EPL",
            max_spread_pct=2.0,
            limit=50
        )
        result = await search_football_markets(input_data)
        
        # Todos deben tener spread <= 2%
        for market in result["markets"]:
            assert market["spread_pct"] <= 2.0
    
    @pytest.mark.asyncio
    async def test_liquidity_filtering(self):
        """Test filtrado por liquidez mínima"""
        input_data = SearchFootballMarketsInput(
            min_liquidity=7.0,
            limit=100
        )
        result = await search_football_markets(input_data)
        
        # Todos deben tener liquidity >= 7
        for market in result["markets"]:
            assert market["liquidity_score"] >= 7.0


class TestArbitrageDetection:
    """Test arbitrage detection"""
    
    @pytest.mark.asyncio
    async def test_detect_spread_arbitrage(self):
        """Test detección de spread arbitrage"""
        input_data = DetectFootballArbitrageInput(
            league="EPL",
            min_roi_pct=2.0
        )
        result = await detect_football_arbitrage(input_data)
        
        assert "opportunities" in result
        # Todas las oportunidades deben cumplir ROI mínimo
        for opp in result["opportunities"]:
            assert opp["expected_roi_pct"] >= 2.0
    
    @pytest.mark.asyncio
    async def test_no_false_positives(self):
        """Test que no hay false positives en arbitrage"""
        input_data = DetectFootballArbitrageInput(
            min_roi_pct=15.0,  # ROI muy alto, debería haber pocos
            league="EPL"
        )
        result = await detect_football_arbitrage(input_data)
        
        # Debería haber pocas oportunidades
        assert result["opportunities_found"] <= 5


class TestPredictiveValidation:
    """Test validación de datos predictivos"""
    
    def test_team_stats_validation(self):
        """Test validación de stats de equipo"""
        team_stats = FootballTeamStats(
            team_id="LIV",
            team_name="Liverpool",
            season="2026-27",
            goals_per_match=2.1,
            xG_per_match=1.95,
            shots_per_match=14.2,
            possession_avg=58.3,
            goals_conceded_per_match=1.1,
            xGA_per_match=1.05,
            tackles_per_match=18.2,
            corners_per_match=5.2,
            free_kicks_per_match=12.1,
            form_rating_last_5=[8.2, 8.5, 7.9, 8.1, 8.3],
            wins_last_5=4,
            draws_last_5=1,
            losses_last_5=0
        )
        
        # Validar suma de form ratings
        assert sum(team_stats.form_rating_last_5) == 5 * 8.2  # ~41.0
        assert team_stats.wins_last_5 + team_stats.draws_last_5 + team_stats.losses_last_5 == 5
```

---

**Status:** Especificación técnica lista para implementación  
**Próximo Paso:** Iniciar Fase 2 con implementación de estas herramientas

