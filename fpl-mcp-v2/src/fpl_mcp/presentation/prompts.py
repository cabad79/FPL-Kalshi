"""MCP prompt templates for Fantasy Premier League assistance."""

from typing import Any

from mcp.server.fastmcp import FastMCP


def register_prompts(mcp: FastMCP) -> None:
    """Register all FPL prompt templates."""

    @mcp.prompt()
    def transfer_advice_prompt(
        budget: float,
        position: str | None = None,
        team_to_sell: str | None = None,
    ) -> str:
        """Generate a transfer advice prompt for the user.

        Args:
            budget: Available budget in millions (e.g., 1.2).
            position: Position to fill (GKP, DEF, MID, FWD).
            team_to_sell: Name of the player to sell, if any.
        """
        parts = [
            "You are an expert Fantasy Premier League (FPL) advisor.",
            "",
            f"The user has a transfer budget of £{budget}m.",
        ]
        if position:
            parts.append(f"They are looking to strengthen their {position} position.")
        if team_to_sell:
            parts.append(f"They are considering selling {team_to_sell}.")
        parts.extend([
            "",
            "Please provide the following:",
            "1. Top 3 transfer recommendations within budget",
            "2. Key stats for each recommendation (form, fixtures, ownership)",
            "3. Upcoming fixture difficulty for the next 5 gameweeks",
            "4. Any injury or rotation risks to be aware of",
            "5. A brief justification for each pick",
        ])
        return "\n".join(parts)

    @mcp.prompt()
    def player_analysis_prompt(
        player_name: str,
        include_comparisons: bool = True,
    ) -> str:
        """Generate a detailed player analysis prompt.

        Args:
            player_name: Name of the player to analyze.
            include_comparisons: Whether to include comparison with similar players.
        """
        parts = [
            f"Analyze FPL player {player_name} in detail.",
            "",
            "Include the following sections:",
            "1. Current season performance (points, form, minutes)",
            "2. Underlying stats (xG, xA, ICT index, influence, creativity, threat)",
            "3. Fixture difficulty for the next 5 gameweeks",
            "4. Injury status and chance of playing",
            "5. Ownership % and transfer trends",
            "6. Value assessment (price vs. points return)",
        ]
        if include_comparisons:
            parts.extend([
                "7. Comparison with 2-3 similar players in the same price bracket",
                "8. Verdict: Buy, Hold, or Sell",
            ])
        else:
            parts.append("7. Verdict: Buy, Hold, or Sell")
        return "\n".join(parts)

    @mcp.prompt()
    def team_rating_prompt(
        player_list: str,
        budget_remaining: float = 0.0,
    ) -> str:
        """Generate a team rating and improvement prompt.

        Args:
            player_list: Comma-separated list of current squad players.
            budget_remaining: Remaining budget in millions.
        """
        parts = [
            "Rate the following FPL squad and suggest improvements:",
            "",
            f"Squad: {player_list}",
            f"Remaining budget: £{budget_remaining}m",
            "",
            "Please provide:",
            "1. Overall team rating (1-10) with reasoning",
            "2. Strengths of the current squad",
            "3. Weaknesses and areas for improvement",
            "4. Suggested transfers (if any) with alternatives",
            "5. Captain strategy for the upcoming gameweek",
            "6. Bench management advice",
        ]
        return "\n".join(parts)

    @mcp.prompt()
    def differential_players_prompt(
        max_ownership: float = 10.0,
        budget: float | None = None,
    ) -> str:
        """Generate a prompt to find differential (low-ownership) players.

        Args:
            max_ownership: Maximum ownership percentage for differential status.
            budget: Optional budget constraint in millions.
        """
        parts = [
            "Find differential FPL players that could provide an edge.",
            "",
            f"Criteria: ownership below {max_ownership}%",
        ]
        if budget is not None:
            parts.append(f"Budget constraint: £{budget}m")
        parts.extend([
            "",
            "For each differential found, provide:",
            "1. Player name, team, and position",
            "2. Current ownership %",
            "3. Recent form and expected points",
            "4. Upcoming fixture difficulty",
            "5. Why they could be a good differential pick",
            "6. Risk level (Low / Medium / High)",
        ])
        return "\n".join(parts)

    @mcp.prompt()
    def chip_strategy_prompt(available_chips: str) -> str:
        """Generate a chip strategy advice prompt.

        Args:
            available_chips: Comma-separated list of available chips
                (e.g., "wildcard, free_hit, bench_boost, triple_captain").
        """
        chips = [c.strip() for c in available_chips.split(",")]
        parts = [
            "Provide a chip strategy for the remainder of the FPL season.",
            "",
            f"Available chips: {', '.join(chips)}",
            "",
            "Please include:",
            "1. Recommended order of chip usage",
            "2. Optimal gameweeks for each chip (considering blanks, doubles, and fixtures)",
            "3. Squad composition strategy for each chip",
            "4. Risks and contingency plans",
            "5. Calendar overview of key gameweeks (blanks, doubles, DGWs)",
        ]
        return "\n".join(parts)
