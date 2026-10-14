# Independent methodology review

Review date: 14 October 2026. Scope: a short, independent review of the first simulator, experiment runner, configuration and tests. This report records a snapshot; later changes need their own checks. The reviewer did not edit the simulation code or run the full study.

## Overall finding

The implementation is consistent with a small decision-model experiment. No blocking error in service accounting or future-information access was found in this inspection. The main concern is interpretation: extra caution about old reports needs a fair comparison with ordinary extra caution about switching. A result from the present utility model cannot establish a real application improvement.

Seven unit tests passed during the review. They cover paired traces, past-only report indices, future-state perturbation, fractional blackout accounting, emergency residence bypass, component removal and metric bounds. Passing these checks supports code consistency; it does not validate the physical model.

## Findings and status

### High priority: separate age information from extra switching resistance

**Evidence:** In `Controller.choose`, every alternative has the same report age, while the current AP has age zero. The age term subtracts the same amount from every alternative. At a fixed age this is additional switching hysteresis. In the first runner, `app_myopic` has a fixed quality margin of 0.03, while the proposed policy tunes its horizon and age penalty on pilot data.

**Consequence:** A gain over `app_myopic` or the `no_age_penalty` ablation does not show that the age of information itself helped. An equally cautious constant-margin policy may achieve the same result.

**Requested fix:** Include an application-quality rule whose constant switching margin is tuned on pilot seeds, with the same residence rule and observations. If added after the main experiment, label it a supplemental comparison and freeze its settings before its evaluation. Component removals should still retain the parent policy's other parameters.

**Status:** Sent to implementer. The lead researcher confirmed that the tuned static-margin comparison was requested. Its implementation and results were not yet inspected for this report.

### High priority for claims: the policy knows the outcome formula

**Evidence:** `prepare` uses `link_service` for both the true service and the controller's candidate estimate. The only difference in these calls is the age of candidate load. Model parameters and application requirements are known exactly.

**Consequence:** The experiment asks whether policies optimize this chosen model under old load reports. It does not test whether the service formula predicts measured Wi-Fi or human experience.

**Requested action:** Keep this limitation prominent. A later experiment should deliberately change the truth formula while leaving the controller estimate fixed, then use measured traces or hardware for calibration.

**Status:** Already clearly acknowledged in code and the research-question document. Remains an intended scope limit.

### Medium priority: “emergency” does not guarantee escape

**Evidence:** The emergency path removes residence time and decision margins, but keeps cost and age penalties. A direct check used current RSSI −85 dBm and quality 0.01, candidate RSSI −70 dBm and quality 0.05, candidate age 8 s and interruption 0.2 s. The proposed policy stayed; the application-myopic and no-age policies moved.

**Consequence:** The emergency flag is a bypass for selected restrictions, not a guaranteed recovery mechanism. The existing test checks one favorable case and does not establish general recovery.

**Requested action:** State the behavior precisely. If a separate dead-link safety rule is desired, define it once for all policies and test it under old reports. A code change is not required for the current scope if no recovery guarantee is claimed.

**Status:** Sent to lead researcher; documentation/implementation decision pending.

### Medium priority: signal and incumbent measurements are idealized

**Evidence:** All candidate RSSI values are fresh at every 0.25 s decision. Only their load values are old. The serving AP's true quality and residual rate replace the reported values immediately.

**Consequence:** This is a load-information-age experiment with free signal measurement and perfect serving-link knowledge. It does not model scan interruption, delayed performance estimates, or the time needed to learn a newly joined AP's quality.

**Requested action:** Use this exact description in the model document. In a later experiment, vary RSSI/report delay and observation cost separately.

**Status:** Partly visible in code and scope; sent to lead researcher for explicit model wording.

### Medium priority: interruption is an average-service penalty

**Evidence:** Both application profiles lose service linearly during blackout. Their different demands and RTT/loss weights change quality, but the model has no packet deadlines, playback buffer, concealment, queue recovery or session failure. The cost rule uses the same horizon family and interruption duration across profiles.

**Consequence:** The model can compare application-dependent service requirements. It cannot directly show that a particular gap freezes a call while a file transfer tolerates it. Equal total missing service spread over many small gaps or one long gap need not have equal effects on a real application.

**Requested action:** Avoid calling the utility a call-quality or QoE measurement. Later tests should include an independently defined deadline or stall outcome and vary interruption patterns.

**Status:** The research-question document already says it does not simulate a player, codec or human satisfaction. This more specific consequence should remain visible when interpreting results.

### Medium priority: confidence intervals have a narrow meaning

**Evidence:** The runner uses disjoint pilot/evaluation seeds, shares traces across policies, and resamples whole seed pairs within each scenario/profile/delay/interruption cell. This is appropriate for paired simulation comparisons. The broad tables average cells descriptively.

**Consequence:** Intervals describe random-trace variability within this fixed model and frozen tuning choice. They do not cover model error, new sites, arbitrary applications or tuning uncertainty. Many separate contrasts also create a multiple-comparison problem if individual intervals are treated as confirmatory discoveries.

**Requested action:** Label intervals exploratory, per-cell and unadjusted. Do not infer that a global policy is best from the number of cells whose intervals exclude zero. Add independently held-out environments before stronger generalization claims.

**Status:** Sent to lead researcher. The analysis code itself does not claim a population-wide significance test.

## Checks that were satisfactory

- The 20 ms and 200 ms interruptions are integrated fractionally; they are not rounded up to the 250 ms decision interval. A unit test also covers interruptions spanning multiple steps.
- The controller receives current/past observations, not future trace values. Perturbing future states leaves earlier decisions unchanged in the test.
- Predicted report age matches the report's actual time index in the default configuration.
- Throughput units are consistent: application demand in Mbps multiplied by the fraction served. RTT is weighted by delivered service, so it should be described as conditional on delivery; outages are reported separately.
- Pilot selection is recorded before evaluation. Evaluation seeds are disjoint from pilot seeds.
- The common two-second residence rule reduces one obvious fairness difference between policies.
- One foreground client and external background load are disclosed. These results cannot establish multi-client fairness, global load balancing or the response of other clients.

## Small implementation cautions

The supplied periods and delays are multiples of the time step, so the rounding in `prepare` is exact here. Future configuration files should validate this relationship or record the effective rounded times. A report period shorter than half a step can round to zero and must be rejected. These are configuration-hardening suggestions, not failures in the default run.

The first tuning grids have different sizes and do not include all plausible margins. Report selected endpoints; if an optimum lies at an edge, a wider pilot-only search is preferable. Do not widen the grid in response to evaluation winners and reuse those same evaluation seeds as independent confirmation.

## Snapshot identifiers

The following hashes identify the files inspected. They may differ from the final delivered version after the requested changes.

- `src/roaming.py`: `3a5786f197789496c708d2d7a8cdb78c84a45d1f88412731354eb8a94e16bcc7`
- `scripts/run_study.py`: `1fa5c2c1129109fa9478663265ca0aa5464175b8478ab86df6d5f1f214af496c`
- `configs/study.json`: `8c26543222a18a16c84fbc5dc75e92b85f553e1c800fda1f39838cef8a5cadb0`
- `tests/test_roaming.py`: `e3ed1f854d4ceec84c84e9b6c743c64f162446f2e026ad26a83b0ea5b416478f`

This review supports the internal consistency of the bounded pilot. It does not establish novelty, validate application quality or QoE, or demonstrate an improvement on real Wi-Fi equipment.

## Final integration follow-up

The lead researcher records the following resolutions after the review snapshot above:

- A separately pilot-tuned static-margin baseline was added. It selected 0.03 and matched all eight application-myopic outcome metrics across 2,880 evaluation rows. The main negative result remains unchanged.
- The [capacity-model mismatch experiment](model-mismatch.md) was added with fixed candidate parameters and unchanged candidate estimates. Its limited sensitivity results are reported separately.
- The [model document](simulation-model.md) now explicitly describes free fresh candidate RSSI, ideal serving quality, common candidate age, and the absence of a guaranteed emergency rescue.
- An emergency counterexample test was added. The full suite now has ten passing tests, including the two mismatch tests.
- Reproduction review found missing output-path support in the static diagnostic and a relative-path error in the mismatch manifest. Those interfaces were repaired, and both supplemental experiments were rerun. These fixes did not change the numerical methods.

These resolutions address the specific comparison and reproducibility issues. They do not remove the physical-model, application-model, or novelty limits recorded above.
