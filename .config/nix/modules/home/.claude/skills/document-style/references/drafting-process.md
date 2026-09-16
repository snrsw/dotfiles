# Drafting process: one document through four versions

Read this when writing a document from scratch. It applies the four versions from the Drafting Process section of `document-style` to one document: a design doc that asks the backend team to approve token-bucket rate limiting for a public REST API. The numbers are invented for the example.

## Version 1: outline

The main points, in the order the reader meets them:

1. A few customers' batch jobs degrade latency for every customer.
2. Proposal: one token bucket per API key, stored in Redis.
3. Why the alternatives fail.
4. Rollout and risks.

The side list, for details that have no place yet:

- peak traffic is about 2000 req/s
- the gateway is a Go service behind an ALB
- bucket size and refill rate are still to be chosen
- a rejected request gets 429 plus a Retry-After header
- Redis becomes a hard dependency of the gateway
- mobile clients send a burst on app open, so a burst allowance matters

## Version 2: sections

Each section title with the one claim it makes. Each side-list item now sits in its section, in parentheses.

- **Problem** — three customers' nightly batch jobs double p99 latency for every other customer. (peak 2000 req/s; Go gateway behind an ALB)
- **Proposal** — one token bucket per API key in Redis caps each customer without affecting the others. (429 plus Retry-After on rejection; burst allowance for mobile clients)
- **Alternatives** — per-instance in-memory limits and ALB-level limits both fail to cap one customer across gateway instances.
- **Rollout and risks** — ship in log-only mode first; Redis becomes a hard dependency of the gateway. (bucket size and refill rate chosen from log-only data)

The side list is now empty. An item that fits no section at this stage is either a missing section or something the document does not need.

## Version 3: story line

The sub-points under each claim, in the order they are argued. Some are already sentences.

- **Problem**
  - Peak traffic is about 2000 req/s.
  - Three customers run nightly batch jobs that each push about 400 req/s for about an hour.
  - During those hours, p99 latency for all other customers doubles.
- **Proposal**
  - Definition: a token bucket holds up to N tokens and refills at R tokens per second. Each request takes one token, and a request that finds the bucket empty is rejected.
  - One bucket per API key, stored in Redis, so every gateway instance sees the same count.
  - A rejected request gets 429 with a Retry-After header.
  - N above R covers mobile clients that send a burst on app open.
- **Alternatives**
  - Per-instance in-memory buckets: a customer spread over 8 instances gets 8 times the limit.
  - ALB rate limiting: it works per source IP, and the batch jobs come from a NAT pool shared with normal traffic.
- **Rollout and risks**
  - Week 1: log-only; record what would have been rejected.
  - Week 2: enforce for the three batch customers, then for all keys.
  - Risk: if Redis is unreachable, the gateway must fail open or fail closed. We propose failing open and alerting.
  - Not verified: we expect the Redis round trip to add under 1 ms at p99.

## Version 4: prose

The paragraphs, written from version 3. Only the opening is shown; each remaining section is written the same way from its bullets.

> Three customers' nightly batch jobs double p99 latency for every other customer. We propose one token bucket per API key, stored in Redis, so that each customer is capped independently and across all gateway instances. We ask the backend team to approve this design before implementation starts.
>
> The gateway is a Go service behind an ALB and serves about 2000 req/s at peak. Three customers run nightly batch jobs that each push about 400 req/s for about an hour. During those hours, p99 latency for all other customers doubles.

Nothing moved between version 3 and version 4. The outline fixed the order in version 1, the sections fixed where each fact lives in version 2, and the story line fixed the order inside each section in version 3, so version 4 only had to turn bullets into sentences.
