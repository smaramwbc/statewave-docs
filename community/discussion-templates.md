# Discussion Templates

Starter prompts for the most common discussion types. Copy the relevant block when you open a new discussion — filling in the headings is the fastest way to get a useful reply.

These are also the bodies you'd port into `.github/DISCUSSION_TEMPLATE/<slug>.yml` form templates if you adopt them later.

## Q&A

For setup help, usage questions, troubleshooting, deployment help.

```markdown
### What are you trying to do?
<!-- The actual goal, not just the symptom -->

### What did you expect to happen?

### What happened instead?
<!-- Errors, unexpected output, missing behavior -->

### Environment
- Statewave version:
- Install method: <!-- pip / docker / source -->
- Python / Node version:
- Database / storage: <!-- Postgres version, pgvector version -->
- Compiler mode: <!-- heuristic / llm -->
- Model / provider: <!-- via LiteLLM, e.g. gpt-4o-mini, claude-3-haiku, ollama/llama3 -->
- Deployment style: <!-- local / self-hosted / cloud -->

### Relevant logs or code
<!-- Trim to the failure. Redact secrets. Use ``` fences. -->
```

## Feature request

For product / SDK / API ideas, integrations, admin UI improvements. Use the **Ideas & Feature Requests** category.

```markdown
### Problem
<!-- What's hard or impossible today? -->

### Proposed solution
<!-- What you'd like to see. Sketch the API or UX if you can. -->

### Why this matters
<!-- Who is blocked / slowed down, and how often -->

### Alternatives considered
<!-- Workarounds you tried, related tools, why they fall short -->

### Who would use this?
<!-- Yourself, your team, a class of users -->

### Urgency
<!-- Blocking, important-not-urgent, nice-to-have -->
```

## RFC

For design proposals significant enough to deserve community review before implementation. Use the **RFCs** category.

```markdown
### Summary
<!-- One paragraph: what is being proposed and why -->

### Motivation
<!-- The problem being solved, with concrete use cases -->

### Proposed design
<!-- Enough detail that someone could critique or implement it.
     Cover: data model, API surface, behavior, migration path. -->

### Alternatives
<!-- Other designs considered and why they were rejected -->

### Risks / tradeoffs
<!-- What this constrains, what it makes harder, what could go wrong -->

### Open questions
<!-- Specific things you want feedback on -->

### Feedback requested
<!-- Who you most want to hear from, by when if there's a deadline -->
```

## Show and Tell

For agents, integrations, memory workflows, evals, benchmarks built with Statewave.

```markdown
### What did you build?
<!-- Short description, link if public -->

### What does Statewave remember?
<!-- Subjects, episode kinds, what gets compiled, what retrieval looks like -->

### Stack
- Agent framework:
- LLM provider / model:
- Statewave compiler mode:
- Embedding provider:
- Deployment:

### Demo / screenshots
<!-- Optional but appreciated -->

### What worked well?

### What was missing?
<!-- Honest gaps help us prioritize -->
```

## Integration report

For sharing how Statewave plugs into a specific framework or stack. Use the **Integrations** category.

```markdown
### Integration target
<!-- e.g. LangChain, LlamaIndex, CrewAI, AutoGen, OpenAI Agents SDK, MCP, custom -->

### Use case

### How Statewave fits
<!-- Where in the agent loop / app it sits, what it stores, what it retrieves -->

### Code sketch
<!-- Minimal example. Public repo link is even better. -->

### Friction encountered

### What would make this easier?
<!-- SDK helpers, docs, examples, API additions -->
```

## Research thread

For long-term memory, temporal memory, agent state, retrieval, evals, memory quality, context engineering.

```markdown
### Question or hypothesis

### Why it matters for memory systems

### What you've read / tried
<!-- Papers, prior art, experiments -->

### What you're proposing to test or discuss

### How Statewave could help (or not)
<!-- Honest framing — research questions don't need to map to product features -->
```
