# Daily Insight Agent System

This document explains the agent architecture of the Daily Insight Agent and how agents work together to provide personalized daily insights.

## What Are Agents in This System?

An **agent** is a specialized AI component with a specific role and bounded responsibility. Rather than one monolithic AI call that tries to do everything, we use three focused agents that work together:

1. **Reader Agent** - Summarizes external information objectively
2. **Reflection Agent** - Analyzes thinking patterns and biases
3. **Coach Agent** - Synthesizes insights and provides actionable advice

This design follows a core principle: **specialized agents with clear constraints are more effective than general-purpose AI**.

---

## The Three Core Agents

### 1. Reader Agent

**Role**: Objective summarizer of external content

**Input**: 
- New items collected today (from RSS, YouTube, Telegram, etc.)
- User's goals (for context, not for filtering)
- Does NOT receive diary entries

**Output** (JSON):
```json
{
  "summary": "Brief 2-3 sentence summary of today's content",
  "key_topics": ["topic1", "topic2", "topic3"],
  "important_quotes": [
    {"quote": "specific quote text", "source": "source name"},
    {"quote": "another relevant quote", "source": "source name"}
  ],
  "facts_vs_opinions": {
    "facts": ["verifiable fact", "another fact"],
    "opinions": ["subjective take", "interpretation"],
    "interpretations": ["what this might mean"]
  },
  "sources_used": ["Feed 1", "Feed 2"]
}
```

**Principles**:
- Never hallucinate or invent content
- Preserve original voice through direct quotes
- Separate facts from interpretations
- Keep it objective—this agent doesn't make judgments

**Implementation**: [app/agents/reader_agent.py](app/agents/reader_agent.py)

**Why separate from Reflection**: The Reader stays objective about external world; Reflection focuses on the internal world (diary, patterns, goals).

---

### 2. Reflection Agent

**Role**: Observer of internal patterns and thinking biases

**Input**:
- User's goals
- Recent diary entries (last 7 days by default)
- Does NOT receive external content

**Output** (JSON):
```json
{
  "key_observations": [
    "Significant pattern noticed in recent days",
    "Another recurring theme"
  ],
  "thinking_biases_detected": [
    {
      "bias_name": "Confirmation Bias",
      "evidence": "Evidence from diary that shows this bias"
    },
    {
      "bias_name": "Availability Heuristic",
      "evidence": "Evidence of this bias"
    }
  ],
  "alignment_with_goals": {
    "aligned": ["Goal 1 - making progress"],
    "misaligned": ["Goal 2 - not getting traction"],
    "unclear": ["Goal 3 - need more data"]
  },
  "patterns_noticed": ["recurring theme 1", "pattern 2"],
  "blind_spots": ["What user might not see", "Potential gap"],
  "hypothesis": "Best guess at what's really happening beneath the surface",
  "uncertainties": ["What I'm unsure about", "Areas that need more data"]
}
```

**Principles**:
- Act as a "wise observer," not confirming user's existing narrative
- Look for contradictions between stated goals and diary entries
- Track cognitive biases: confirmation bias, availability heuristic, sunk cost fallacy, narrative fallacy, recency bias, etc.
- Always include uncertainties—don't overstate confidence

**Biases Tracked**:
- Confirmation bias (seeking info that confirms existing beliefs)
- Availability heuristic (judging by recent/memorable examples)
- Sunk cost fallacy (continuing due to past investment)
- Narrative fallacy (creating stories to explain randomness)
- Recency bias (overweighting recent events)
- Hindsight bias (seeing past as predictable)
- Dunning-Kruger effect (overconfidence in knowledge)

**Implementation**: [app/agents/reflection_agent.py](app/agents/reflection_agent.py)

**Why separate from Coach**: Reflection is about understanding; the Coach is about action. Separating these helps prevent the Coach from being biased by the user's own narratives.

---

### 3. Coach Agent

**Role**: Synthesizer and practical advisor

**Input**:
- Reader Agent output (external context)
- Reflection Agent output (internal patterns)
- Goals
- Recent diary entries
- Everything combined for holistic view

**Output** (JSON):
```json
{
  "practical_tip": "One specific, actionable thing you can do today",
  "one_day_action": "Concrete steps with time estimates (e.g., '15 min: talk to colleague, 30 min: document decision')",
  "possible_project_idea": "Optional project to consider (can be null); usually 1-3 days of work",
  "warnings": [
    "Risk or consideration to keep in mind",
    "Another potential pitfall"
  ],
  "confidence": 0.85
}
```

**Principles**:
- Provide ONE actionable tip (not a list of 10)
- Must be achievable in one day
- No generic motivation—be specific based on context
- Include relevant warnings (especially for finance, health, relationships)
- Estimate confidence 0-1 based on data clarity

**Special Cases**:
- Finance/investment tips include disclaimer about seeking professional advice
- Health-related advice is conservative, recommends professional consultation
- Relationship advice acknowledges emotional complexity

**Implementation**: [app/agents/coach_agent.py](app/agents/coach_agent.py)

**Why Coach is last**: It needs input from both Reader and Reflection to synthesize truly useful advice.

---

## Agent Interaction Flow

```
Day Start
    ↓
[Collectors gather data from all sources]
    ↓
[Storage: Save items to database]
    ↓
┌─────────────────────────────────┐
│ Load Today's Content            │
│ + Load Goals from Storage       │
│ + Load Recent Diary             │
└─────────────────────────────────┘
    ↓
    ├→ [Reader Agent]  ← External content
    │   (objective summary)
    │   ↓ reader_output
    │
    └→ [Reflection Agent]  ← Goals + Diary
        (pattern analysis)
        ↓ reflection_output
            ↓
            ├→ [Coach Agent]  ← reader_output
            │                  ← reflection_output
            │                  ← Goals + Diary
            │ (synthesize & advise)
            ↓ coach_output
                ↓
            [Combine all outputs]
                ↓
            [DailyInsight object]
                ↓
            [Save to database]
                ↓
            [Render as HTML/JSON]
```

### Key Design Decisions

1. **Sequential Processing**: Agents run in order (Reader, then Reflection, then Coach). This ensures the Coach has input from both other agents.

2. **Limited Communication**: Agents don't call each other; they pass structured JSON through the pipeline. This makes the system more reliable and testable.

3. **Data Isolation**: Reader never sees diary, Reflection never sees external content. This prevents biased blending.

4. **Error Resilience**: If any agent fails, the system continues with partial output (marked as partial in the UI).

---

## Extending the Agent System

### Adding a New Agent

1. **Create the agent class** in `app/agents/`:
   ```python
   from app.agents.base_agent import BaseAgent
   from app.models import AgentInput
   
   class CustomAgent(BaseAgent):
       def think(self, agent_input: AgentInput) -> dict:
           """Implement your agent logic here"""
           system_prompt = self._load_system_prompt("custom_agent")
           # Your implementation
           return {"key": "value"}
   ```

2. **Create system prompt** in `app/prompts/custom_agent.md`:
   ```markdown
   # Custom Agent System Prompt
   
   Your role is to...
   ```

3. **Add to pipeline** in `app/services/daily_pipeline.py`:
   ```python
   custom_output = CustomAgent(self.openai_client).think(agent_input)
   ```

4. **Update DailyInsight model** in `app/models.py` to include new output fields.

5. **Update HTML rendering** in `app/main.py` to display new output.

### Example: Trend Analysis Agent

Imagine you want to add an agent that detects trends over time:

```python
class TrendAgent(BaseAgent):
    """Detect patterns and trends across the past 30 days"""
    
    def think(self, agent_input: AgentInput) -> dict:
        # Analyze past 30 days of diary and content
        # Identify uptrends and downtrends
        # Return trend analysis
        return {
            "uptrends": ["topic trending up"],
            "downtrends": ["topic trending down"],
            "inflection_points": ["when things shifted"]
        }
```

---

## Agent Architecture Principles

### Principle 1: Single Responsibility

Each agent has one clear responsibility:
- Reader: summarize external information
- Reflection: understand internal patterns
- Coach: suggest action

This makes agents easier to test, understand, and maintain.

### Principle 2: Bounded Context

Each agent works with limited data:
- Reader sees only external content (not feelings/diary)
- Reflection sees only internal data (not news/feeds)
- Coach combines both but stays focused on actionable insight

This prevents agents from becoming overwhelmed or biased.

### Principle 3: Structured Output

All agents output JSON with defined schemas. This:
- Makes outputs predictable and composable
- Enables easy testing (compare JSON)
- Allows downstream code to depend on structure

### Principle 4: Fallible Reasoning

Agents explicitly include:
- Uncertainties (what they don't know)
- Confidence levels (how sure they are)
- Multiple hypotheses (not just one answer)

This makes the system more honest and useful.

### Principle 5: Graceful Degradation

If an agent fails:
- System continues with partial output
- UI clearly marks what's missing
- Better to have partial insight than crash

---

## Configuration

Agent behavior is controlled through environment variables and config:

```python
# Token limits per agent (from .env or config.py)
MAX_TOKENS_READER = 1000       # Brief summaries
MAX_TOKENS_REFLECTION = 1500   # Deeper analysis
MAX_TOKENS_COACH = 800         # Concise advice

# Model selection
OPENAI_MODEL = "gpt-4o-mini"   # Fast and affordable
# Or: "gpt-4-turbo" for more reasoning
```

Adjust these based on:
- **Token limits**: Smaller = faster/cheaper but less detailed
- **Model**: Larger models think deeper but cost more
- **Temperature**: Add to agent calls for creativity (0.7-0.9) vs consistency (0.0-0.3)

---

## Testing Agents

Each agent has unit tests in `tests/test_agents.py`:

```python
def test_reader_agent():
    items = [ContentItem(source=SourceType.RSS, title="...", ...)]
    agent = ReaderAgent(mock_openai_client)
    
    output = agent.think(AgentInput(
        new_items=items,
        goals=goals,
        recent_diary=[]
    ))
    
    assert "summary" in output
    assert "key_topics" in output
    assert len(output["sources_used"]) > 0
```

Key testing patterns:
- Mock OpenAI client to avoid API calls
- Use fixtures for sample data
- Verify output structure matches schema
- Test edge cases (empty input, single item, many items)

---

## Performance & Cost

### Token Usage (Approximate)

Average daily run with typical data:
- **Reader Agent**: 300-500 tokens
- **Reflection Agent**: 400-800 tokens
- **Coach Agent**: 200-400 tokens
- **Total**: 900-1700 tokens per day ≈ $0.01-0.03

### Optimization Strategies

1. **Token Counting**: Pre-count tokens before sending to avoid overages
   ```python
   tokens = openai_client.count_tokens(prompt)
   if tokens > limit:
       truncate_content()
   ```

2. **Caching**: Cache yesterday's insight to avoid re-analysis
   ```python
   if insight_exists(today):
       return cached_insight
   ```

3. **Batching**: Process weekly instead of daily for reflection
   ```python
   if day == "Sunday":
       reflection_lookback = 7  # Full week
   else:
       reflection_lookback = 1  # Just yesterday
   ```

---

## Common Questions

### Q: Why not use one powerful agent instead of three?

A: Specialized agents are more reliable because:
- Clear responsibility = easier to debug
- Limited input = less confusion for AI
- Easy to test each agent independently
- If Reader fails, Reflection still works

One mega-agent would be tempting but fail silently or produce confused output.

### Q: Can I change agent order?

A: Yes, but some orders work better:
- **Good**: Reader → Reflection → Coach (as implemented)
- **Bad**: Coach → Reflection (Coach has no context)
- **Possible**: Parallel Reader + Reflection (they don't interact)

The current order ensures each agent has the context it needs.

### Q: How do I make agents more creative?

A: In `openai_client.py`, adjust the temperature parameter:
```python
response = openai.ChatCompletion.create(
    model=self.model,
    messages=messages,
    temperature=0.7,  # Higher = more creative, lower = more consistent
)
```

Default is 0.3 (consistency). Increase to 0.7-0.9 for creative suggestions.

### Q: How often should agents run?

A: Default is once daily (when user loads web interface). For automatic daily runs:

```python
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(run_daily_pipeline, 'cron', hour=6, minute=0)
scheduler.start()
```

This runs the pipeline every day at 6 AM.

---

## Further Reading

- [System Prompt Files](app/prompts/) - Read the actual prompts each agent uses
- [Agent Base Class](app/agents/base_agent.py) - Understand the common interface
- [Pipeline Orchestrator](app/services/daily_pipeline.py) - See how agents are coordinated
- [Models](app/models.py) - Understand AgentInput and agent output schemas
- [README.md](README.md) - Broader project architecture

---

## Contributing New Agents

If you create new agents, please:

1. Follow the BaseAgent interface
2. Document your agent here with its role, input, output
3. Add tests in `tests/test_agents.py`
4. Update the flow diagram above
5. Include a "why separate" explanation for why this agent deserves its own role

The goal is to keep agents focused and composable—each one should answer one question well rather than trying to answer everything.
