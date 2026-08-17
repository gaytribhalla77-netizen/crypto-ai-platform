# Production Evolution Roadmap

The current build completes the safe autonomous-intelligence foundation. The only intentionally gated boundary is live-money execution.

1. Run the full dependency install and DB integration suite.
2. Select one real FX broker and implement its adapter behind the existing provider-neutral contract.
3. Verify symbol specifications, market hours, spread, margin, partial fills, rejects, cancellations and reconciliation against a sandbox account.
4. Run long-duration paper trading and walk-forward validation.
5. Perform an independent security review.
6. Only after all gates pass, enable a separately deployed live adapter with a hard kill switch and small capital limits.
