# Agent Spec: Agent Dave

Generated: 2026-01-19
Template: Hybrid (Telegram + Supabase Postgres + Hetzner)

## Overview

- **Name**: Agent Dave
- **Slug**: agent_dave
- **Description**: CMO marketing genius for small businesses - analyzes ad spend vs revenue to deliver actionable marketing insights
- **Interface**: Telegram bot
- **Database**: Supabase Postgres (Klemtek instance)
- **Deployment**: Local for testing, Hetzner for production
- **Integrations**: Supabase MCP (existing Klemtek authentication)

## Architecture Decisions

### Interface: Telegram Bot
- Simple messaging interface for busy business owners
- Ultra-brief responses optimized for mobile
- Commands: `/start`, `/new` (new conversation), `/history` (resume old conversations)

### Database: Supabase Postgres
- Connects to existing Klemtek Supabase instance
- Uses Supabase MCP server for queries
- 1-hour cache for query results (balance freshness vs performance)
- Multi-tenant ready (user scoped by `klemtek_account_id`)

### Key Data Sources (from Klemtek Supabase)

| Table | Purpose |
|-------|---------|
| `google_ads_spend_daily` | Daily ad spend, leads, CPL by channel/location |
| `kfd_leads` | Lead-to-revenue attribution (3/6/12mo revenue) |
| `hcp_jobs` | Service revenue by job |
| `hcp_invoices` | Payment status and collections |
| `hcp_customers` | Customer data and lead sources |
| `call_tracking_dashboard` | Call quality, booking rates, rep performance |

### Available Metrics

**Acquisition:**
- Lead Acquisition Cost (LAC) = spend / leads
- Customer Acquisition Cost (CAC) = spend / new customers
- Cost per lead by channel (LSA vs PPC)

**Revenue:**
- ROAS = revenue / spend
- Customer Lifetime Value (3mo, 6mo, 12mo)
- Payback period

**Quality:**
- Booking rate = appointments / leads
- Quote-to-close rate
- Rep performance scores

## System Prompt Requirements

### Identity
Agent Dave is a thoughtful marketing advisor - not a data dump. He interprets numbers and highlights what matters.

### Personality & Tone
- **Confidence**: Thoughtful advisor ("Based on the data, I'd suggest...")
- **Language**: Basic marketing metrics with brief explanations when needed
- **Length**: Ultra-brief (Twitter-length insights, bullet points)
- **Proactivity**: Highlights problems even if not directly asked

### Core Behaviors

1. **When asked a question:**
   - Query the relevant data
   - Deliver insight in 1-2 sentences max
   - Flag any obvious problems noticed

2. **When data is insufficient:**
   - Clearly state what's missing
   - Suggest what data would help
   - Don't guess or speculate

3. **When delivering bad news:**
   - Be direct but constructive
   - Lead with the problem
   - Follow with actionable suggestion

4. **When asked about unavailable data:**
   - Admit clearly: "I don't have access to [X] data"
   - Suggest what they CAN ask about

### Multi-Location Handling
- When user doesn't specify location, ask which one
- Track user's default location preference in conversation context

### Example Interactions

**Quick metric check:**
```
User: What's my ROAS this week?
Dave: 3.2x ROAS this week ($4,800 revenue on $1,500 spend). Down from 3.8x last week - looks like CPL increased on LSA.
```

**Diagnostic:**
```
User: Why are leads down?
Dave: Leads down 23% vs last week. Two factors:
• LSA spend dropped $400 (budget cap hit?)
• PPC conversion rate fell from 4.2% to 2.8%
Check your daily budget settings.
```

**Strategic:**
```
User: Should I increase budget?
Dave: Based on your current 3.2x ROAS, yes - you're profitable. I'd add to LSA first since CPL is $45 vs $68 on PPC. Start with 20% increase and monitor for a week.
```

**Insufficient data:**
```
User: How did January compare to last January?
Dave: I only have data back to March 2024. Can compare to any month since then - want me to show January vs December instead?
```

## Technical Details

### Project Structure
```
agent_dave/
├── bot.py                          # Main Telegram bot entry point
├── requirements.txt
├── .env.example
├── modules/
│   ├── __init__.py
│   ├── conversation.py             # Conversation manager (Supabase)
│   ├── cache.py                    # 1-hour query cache
│   └── metrics.py                  # Marketing metric calculations
├── prompts/
│   └── system_prompt.md
├── tools/
│   ├── __init__.py
│   └── supabase_tools.py           # MCP tool definitions
└── CLAUDE.md
```

### MCP Tools Required

```python
@tool
def query_spend(days: int = 30, location: str = None) -> str:
    """Query ad spend data for the specified period."""

@tool
def query_leads(days: int = 30, location: str = None) -> str:
    """Query lead data with revenue attribution."""

@tool
def query_revenue(days: int = 30, location: str = None) -> str:
    """Query revenue from jobs and invoices."""

@tool
def query_call_metrics(days: int = 30, location: str = None) -> str:
    """Query call tracking performance metrics."""

@tool
def compare_periods(metric: str, period1: str, period2: str) -> str:
    """Compare a metric across two time periods."""
```

### Error Handling
- Query failures: Report clearly ("Couldn't fetch data, try again")
- Empty results: State clearly what's missing
- Cache misses: Fetch fresh and cache

### Conversation Persistence
- Store conversations in Supabase (new table: `agent_dave_conversations`)
- Support resuming old conversations via `/history` command
- Per-user conversation isolation

### Multi-Tenant Design
- All queries scoped by `klemtek_account_id`
- User-to-account mapping stored in config or user table
- Ready for additional businesses without code changes

## Environment Variables

```bash
# Telegram
TELEGRAM_TOKEN=...

# Claude
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-sonnet-4-5-20250514

# Supabase (use existing Klemtek credentials)
SUPABASE_URL=...
SUPABASE_SERVICE_KEY=...

# Cache
CACHE_TTL_SECONDS=3600
```

## Deployment

### Local Testing
```bash
cd /Users/philipgalebach/coding-projects/_agents/agent_dave
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Fill in credentials
python bot.py
```

### Hetzner Production
```bash
# Deploy to Hetzner via systemd
ssh admin@100.109.131.85
cd /opt/agent_dave && git pull
sudo systemctl restart agent_dave
```

## Interview Summary

| Topic | Decision |
|-------|----------|
| Interface | Telegram bot |
| Database | Supabase Postgres (Klemtek) |
| Caching | 1-hour TTL |
| Tone | Thoughtful advisor, basic metrics, ultra-brief |
| Proactivity | Reactive but highlights problems |
| Multi-tenant | Yes, ready for multiple accounts |
| Memory | Persistent conversations, can resume old ones |
| Restrictions | None - full CMO authority |
| Error handling | Report clearly, no guessing |
| Edge case focus | Insufficient data handling |

## Next Steps After Build

1. Create Telegram bot via @BotFather
2. Set up Supabase credentials in `.env`
3. Create `agent_dave_conversations` table in Supabase
4. Test locally with real Klemtek data
5. Deploy to Hetzner when ready
