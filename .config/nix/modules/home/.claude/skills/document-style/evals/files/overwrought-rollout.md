# Rollout Plan: Search Index v2

Before diving into the details, let me first explain the overall conclusion of this plan. In this document we will describe the approach we intend to take for the migration. **In short**, we will do a staged rollout.

The new index is the beating heart of our search stack, and the cutover is a tightrope walk between two cliffs: stale results on one side, missing results on the other. The rollout **orchestra** has three movements: shadow, canary, and full traffic.

Regarding the shadow phase duration, it should be noted that the length of this particular phase has been determined to be one week.

During canary, traffic shifting uses weighted routing. The weights follow a doubling scheme with holds between steps.

**Note:** rollback is **very** important. The rollback procedure is initiated by flipping the `search.v2.enabled` flag to false, which is **extremely** fast.
