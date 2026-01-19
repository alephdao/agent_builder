# Claude Model Selection Guide

## Available Models (January 2025)

### Claude Haiku 4.5
**Model ID:** `claude-haiku-4-5-20251001`

**Characteristics:**
- **Speed:** Lightning fast ⚡
- **Intelligence:** Lower capability
- **Cost:** Most economical

**Best for:**
- Simple, repetitive tasks
- High-volume requests
- Speed-critical applications
- Basic chat interactions
- Low-budget projects

**Not ideal for:**
- Complex reasoning
- Multi-step planning
- Code generation
- Nuanced responses

---

### Claude Sonnet 4.5 (Recommended)
**Model ID:** `claude-sonnet-4-5-20250929`

**Characteristics:**
- **Speed:** Balanced ⚖️
- **Intelligence:** High capability
- **Cost:** Moderate

**Best for:**
- Most agent applications (default choice)
- General-purpose assistants
- Code generation and debugging
- Agentic workflows
- Complex conversations
- Tool use and function calling

**Why it's recommended:**
- Best balance of performance/cost
- Strong reasoning capabilities
- Excellent tool use
- Fast enough for real-time chat
- Handles most tasks exceptionally well

---

### Claude Opus 4.5
**Model ID:** `claude-opus-4-5-20251101`

**Characteristics:**
- **Speed:** Slower 🐢
- **Intelligence:** Highest capability
- **Cost:** Premium pricing

**Best for:**
- Critical decision-making
- Complex multi-step reasoning
- Research and analysis
- High-stakes applications
- When absolute accuracy matters
- Budget is not a constraint

**Not ideal for:**
- Real-time chat (latency sensitive)
- High-volume applications
- Cost-sensitive projects
- Simple tasks

---

## Decision Matrix

| Use Case | Recommended Model |
|----------|-------------------|
| Telegram bot for casual chat | Haiku |
| Personal productivity assistant | Sonnet ✓ |
| Code review agent | Sonnet ✓ |
| Medical diagnosis support | Opus |
| Meeting transcript analyzer | Sonnet ✓ |
| Simple task tracker | Haiku |
| Research assistant | Opus |
| Customer support bot | Sonnet ✓ |
| Financial advisor agent | Opus |
| Language translator | Haiku or Sonnet |

## Cost Comparison

Approximate pricing (check current rates at https://www.anthropic.com/pricing):

| Model | Input (per 1M tokens) | Output (per 1M tokens) |
|-------|----------------------|------------------------|
| Haiku | Lowest | Lowest |
| Sonnet | Medium | Medium |
| Opus | Highest | Highest |

**Pro tip:** Start with Sonnet. Only upgrade to Opus if you need the extra intelligence, or downgrade to Haiku if speed/cost becomes an issue.

## Switching Models

You can easily change the model after building your agent by updating the model ID in your configuration:

```python
# In your agent code
options = ClaudeAgentOptions(
    model="claude-sonnet-4-5-20250929",  # Change this line
    # ... other options
)
```

## Legacy Models (Deprecated)

These models are being phased out:
- Claude 3.5 Sonnet
- Claude 3 Opus
- Claude 3 Haiku
- Claude 2.1
- Claude 2.0

**Migration:** Replace with Claude 4.5 equivalents for better performance.

---

**Last Updated:** January 2025

For the latest model availability and pricing, visit:
- https://docs.anthropic.com/claude/docs/models-overview
- https://www.anthropic.com/pricing
