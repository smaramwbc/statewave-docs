# Show us your memory problem

> Suggested category: **Research** (or **General** if Research isn't enabled yet). Pin after posting.

---

## Title

Show us your memory problem

## Body

The honest reason Statewave exists: every team building agents eventually hits the same wall, and the wall has different shapes depending on what they tried first.

This thread is the place to describe **the wall you hit**. We're collecting these to make the patterns legible — both for us, when prioritizing, and for everyone reading who might recognize their own situation.

You don't need to have a solution. You don't need to be using Statewave. Honest descriptions of the failure mode are the most useful thing.

### Prompts

Pick whatever resonates.

#### What breaks with chat history?
- Token limits forcing truncation of useful context
- Stale facts persisting because nothing curates the history
- Hallucinated history when the model fills in gaps
- Loss of preferences and decisions across sessions
- No way to inspect, correct, or audit what's been "remembered"

#### What breaks with vector DB memory?
- Recency-vs-relevance fights you can't tune
- Retrieval that's semantically close but operationally wrong
- No structure — every chunk is the same kind of thing
- No provenance back to the source event
- "It worked in eval, it doesn't work in prod"

#### What breaks with graph or RAG memory?
- Schema design eats the project before any agent ships
- Updates and conflict resolution become a side quest
- Graph queries that don't compose with how the model wants to retrieve
- Maintenance cost that scales with corpus, not with users

#### What should an agent actually remember?
- Preferences (durable)
- Decisions made together (durable, with provenance)
- Account / customer state (durable, supersedable)
- Recent conversation (short-lived, ranked)
- Outcomes ("we tried X, it didn't work")
- Relationships between subjects
- What it's been told *not* to do

#### What should an agent forget?
- Stale facts that have been superseded
- One-off context that doesn't generalize
- Anything the user asked it to forget (and provably so)
- Things that were wrong (with a record that they were wrong, not silent erasure)

#### Memory as something you operate, not something you set and forget
- How should memory be **inspected**? — list, search, filter, view a subject timeline
- How should memory be **corrected**? — by hand, by re-compilation, by superseding
- How should memory be **exported**? — for backup, audit, migration, sharing
- How should memory be **reset**? — per subject, per kind, per time window, per tenant
- What does "memory health" look like in production?

### Format

Whatever's natural. A bullet list, a paragraph, a war story, a diagram, a code snippet. The more specific the situation, the more useful the post.

If you don't want to attach your name to a use case (NDA, customer-sensitive, unannounced product), say so and we'll treat the discussion accordingly. For genuinely sensitive specifics, route to the contact channels in [SUPPORT.md](https://github.com/smaramwbc/statewave/blob/main/SUPPORT.md) instead of posting publicly.

We'll synthesize patterns from this thread into roadmap updates and into [why-statewave.md](https://github.com/smaramwbc/statewave-docs/blob/main/why-statewave.md). Crediting respondents (or keeping you anonymous) per your preference.
