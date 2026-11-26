# Agent Onboarding — india-ate

You are an AI agent working on `india-ate`. BEFORE writing any code:

## Step 1: Read the Constitution
`cat .swarmforge/constitution.prompt`

## Step 2: Read Your Role
`cat .swarmforge/roles/<your-role>.prompt`

## Step 3: Check Your Inbox
`ls .swarmforge/handoffs/inbox/new/`

## Step 4: Verify Quality Gates Before Any Handoff
```bash
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
uv run mypy src/
uv run pytest --cov=india_ate --cov-fail-under=95
uv run radon cc src/ -a -nb  # max CC should be ≤ 10
uv run mutmut run && uv run mutmut results  # mutation score ≥ 80%
```

## Non-Negotiables
- Never write implementation before a failing test exists
- Never modify base classes in `models/base.py` without Architect approval
- Never generate/infer FSSAI IDs, legal names, or regulatory statuses
- Never import framework code into the `models/` layer
