# ADR-002: Heuristic memory compilation for v1

**Status:** Accepted  
**Date:** 2026-04-24

## Context

Memory compilation (deriving structured memories from raw episodes) can use LLMs, heuristics, or a hybrid approach.

## Decision

Use heuristic/regex-based compilation for v1. Design the compiler interface to be pluggable so LLM-backed compilation can be added without changing the API or data model.

## Rationale

- No external API dependency for core functionality
- Deterministic and testable
- Fast local development
- LLM compilation is a natural v2 upgrade path

## Consequences

- Profile fact extraction is limited to pattern matching
- Episode summaries are truncation-based
- Acceptable for demonstrating the product loop
