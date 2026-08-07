# Agent Guide

## Project

Issue Stance Aggregator is a media/product concept for organizing public controversies into clear issue pages. The core value is not to decide who is right, but to separate facts, claims, uncertainty, pro arguments, critical arguments, and evidence strength.

## Product Direction

Start as a curated editorial product, not a fully automated SNS crawler.

The first version should work like this:

1. An editor registers source URLs.
2. AI extracts summaries, facts, uncertainties, arguments, timelines, and evidence labels.
3. A human reviews and corrects the output.
4. The result is published as a readable issue page and summarized in a newsletter.

Avoid presenting SNS speculation as fact. Always separate:

- confirmed facts
- reported claims
- official statements
- personal explanations
- denials
- unverified SNS claims
- editorial analysis

## Preferred Initial Channels

Use Substack as the first monetization and audience-building channel.

Substack is suitable for:

- weekly newsletters
- paid deep-dive reports
- audience list building
- simple publishing without heavy engineering

Substack is not ideal for:

- complex issue databases
- interactive comparison tables
- custom stance maps
- advanced search
- reusable structured data

The recommended structure is:

| Role | Tool |
| --- | --- |
| Free and paid newsletter | Substack |
| Structured issue pages | Independent Web app |
| Data source | JSON first, DB later |
| Promotion | X, YouTube Shorts, TikTok, note if needed |

## Content Principles

- Use evidence links wherever possible.
- Do not overstate what the source proves.
- Label uncertainty clearly.
- Use neutral but readable language.
- Avoid amplifying personal attacks.
- Treat accident, minor, and victim-related topics with extra caution.
- Preserve correction history for published content.

## Recommended MVP

Build around one issue page format:

- 30-second summary
- confirmed facts
- unconfirmed claims
- issue map
- pro/defense arguments
- critical arguments
- comparison table
- timeline
- evidence list

Start with JSON-backed pages before building a database.

Recommended first topic: legislative seat reduction.

Reasons:

- lower personal-information risk
- clear pro/con structure
- easy to show numbers and tradeoffs
- useful for both general readers and policy-focused subscribers

## Standard Article Format: Issue Battle

For controversy articles, prefer the "Issue Battle" format when there are visible pro/con reactions.

The goal is not to create outrage or declare winners. The goal is to let readers see how each side argues, what evidence each side has, and where the unresolved points remain.

Use this structure:

1. Short summary.
2. List of major dispute points.
3. Multiple rounds of debate.
4. Each round includes:
   - the issue question
   - critical-side argument
   - defense-side argument
   - evidence for both sides
   - weakness or missing evidence
   - current editorial sorting
   - evidence strength rating
5. Final synthesis.
6. Evidence links.
7. Editorial note explaining that ratings are evidence strength, not popularity.

Avoid "winner/loser" wording unless the user explicitly asks for it. Prefer:

- current sorting
- evidence strength
- unresolved point
- stronger on current evidence
- requires additional confirmation

Do not use the battle format to amplify personal attacks. Convert hostile SNS language into neutral claims.

## Monetization

Do not rely only on advertising. Politics and controversy content can create brand-safety and platform-risk problems.

Preferred order:

1. Free issue pages.
2. Free Substack newsletter.
3. Paid Substack deep dives.
4. B2B custom reports.
5. Independent Web app with paid account features.
6. API or structured data access.

Potential pricing:

| Plan | Price |
| --- | --- |
| Free | 0 yen |
| Individual paid | 500-980 yen/month |
| Pro | 2,980-9,800 yen/month |
| Business | 30,000 yen/month and up |

## Editorial Risk

Political content requires trust. The product loses value if it becomes an outrage aggregator.

High-risk areas:

- defamation
- privacy violations
- reposting unverified claims
- selective evidence collection
- sponsor influence
- partisan framing hidden as neutrality

For each issue, explicitly show the evidence strength and the current uncertainty.
