# Guide for the simulation paper

Prepared on 14 October 2026. This is a writing and measurement guide, not manuscript prose. The new source records are in `references/packet-sources.json`. The supporting bibliography is `references/packet-bibliography.bib`; it supplements the existing bibliography.

## Define the kind of evidence first

A model with individual packets, queues, generation times, and deadlines can test application delivery more directly than a coarse service-score model. It is still a **packet-level traffic and queue simulation with an abstract Wi-Fi service model** unless it also models the relevant radio and protocol behavior. Do not call it a full implementation of Wi-Fi roaming merely because it uses small time steps.

List separately what is implemented and what is abstracted: channel contention, retries, aggregation, rate adaptation, uplink/downlink scheduling, discovery scans, security exchanges, client acceptance, and wired-path changes. An abstract interruption can represent their combined effect, but its distribution remains an assumption until measured. The first paper should describe a controlled simulation study and make its limits visible in the abstract, methods, and discussion.

## What the media sources support

| Design choice | Verified source support | What remains our assumption |
|---|---|---|
| Audio packets every 20 ms | RFC 7587 defines Opus `ptime` as the desired media duration per packet and gives 20 ms as its default when unspecified. | Fixed 20 ms generation, packet size, bitrate, silence handling, and recovery behavior in our workload. A 20 ms packet period is not a 20 ms network deadline. |
| Video frames at 30 frames/s | RFC 8836 describes nearly periodic video frames with variable sizes and possible packet fragmentation. | The choice of 30 frames/s, size distribution, key-frame pattern, and number of packets per frame. The 33.33 ms frame period is not automatically a delivery deadline. |
| Deadline-sensitive delivery | RFC 8836 explains why late interactive-media data may lose its value and why requirements differ from bulk transfers. | A chosen 60, 100, or 150 ms deadline and where its clock starts. None of these is a universal Wi-Fi requirement established by this source. |
| A useful-throughput measure | The same RFC discusses useful bandwidth and application-specific needs. | The utility curve, minimum useful bitrate, and relative weight assigned to each application. |

Sources: [P01: RFC 8836](https://www.rfc-editor.org/rfc/rfc8836.html), [P02: RFC 7587](https://www.rfc-editor.org/rfc/rfc7587.html). RFC 8836 is an Informational RFC; do not describe it as a mandatory universal deadline standard.

If packets are generated at the end of an audio block, the network delay begins after that block has been collected. State whether packetization, encoding, decoding, and rendering time are included. A one-way network deadline is only part of a full conversational delay budget. Sweep the chosen deadline or playout budget so the conclusion does not depend on one convenient number.

## Metric definitions to freeze before the main runs

These definitions are proposed study choices. Match them to the code, then use the same definitions in every table and figure.

| Metric | Definition and reporting rule |
|---|---|
| Packet delivery delay | Receiver-arrival time minus generation time. Report percentiles conditional on arrival, together with loss and late-delivery rates. |
| On-time delivery fraction | Generated packets received by their declared deadlines, divided by all generated packets eligible for evaluation. Count each packet once. |
| Deadline failure fraction | One minus on-time delivery fraction. Split it into network/queue loss and received-too-late components. |
| Useful goodput | Payload bits delivered on time divided by the stated observation duration. For bulk traffic, use total delivered payload bits instead. |
| Loss burst | Consecutive generated packets not received, in generation order. Report run lengths and duration; keep late-arrival bursts as a separate measure. |
| Audio continuity proxy | Consecutive audio blocks unavailable at their scheduled playout times. State that no real decoder, speech reconstruction, or listener test was used. |
| Complete video-frame delivery | A frame is complete when its required packets have arrived; the completion time is the latest required-packet arrival. Specify the rule for missing packets and deadline expiry. |
| Frame deadline failure | A generated frame is incomplete at its scheduled deadline. Treating all frame packets as necessary is a deliberately strict reconstruction rule, not a claim about every codec. |
| Bulk completion time | Time from transfer start to final required byte received. If unfinished at run end, report it as incomplete or right-censored, not as completed at the cutoff. |
| Roaming cost | Transition count, accumulated blocked-service time, failed attempts, and returns to an earlier AP within a declared time window. |

Do not discard a late packet from all statistics simply because it is useless for playout. It still consumed service and is evidence of delayed delivery. Expiring old packets in a queue can improve useful delivery, but that is a scheduling decision that must be shared across policies or tested separately.

Use a generation cutoff and a drain period long enough to decide whether the final packets met their deadlines. Alternatively, define an explicit censoring rule. Do not count the unobserved future of the last packet as a success or loss by accident. Exclude startup intervals only by a declared rule shared across policies.

If the paper uses the name **RTP interarrival jitter**, implement the RFC 3550 calculation rather than the standard deviation of delays. For consecutive received packets, let `D` be the change in arrival spacing minus the change in source timestamp spacing. The update is `J = J + (abs(D) - J) / 16`, using consistent units and arrival order. A simple delay standard deviation is valid as its own metric, but should have that name. [P04: RFC 3550, section 6.4.1](https://www.rfc-editor.org/rfc/rfc3550.html#section-6.4.1)

## Video freezes need a playout model

The W3C draft defines a freeze using the gap between rendered frames: at least `max(3 * mean_duration, mean_duration + 150 ms)`, where the mean uses the last 30 rendered-frame durations. With an otherwise steady 30 frames/s history, this threshold is about 183.3 ms. That calculation is an illustration, not a fixed threshold for every history. [M12 / P03: dated WebRTC statistics draft](https://www.w3.org/TR/2025/CRD-webrtc-stats-20250925/)

A packet-arrival gap and a missed frame deadline are not rendered-frame gaps. To approximate freeze behavior, the simulation must define scheduled playout, frame completion, late-frame handling, and whether the last decoded frame remains on screen. It must also define the initial history and a freeze continuing at simulation end. Use a name such as **simulated playout freeze** and describe differences from the draft. If that receiver logic is absent, report frame deadline failures and delivery gaps instead.

Do not label packet loss as audio concealment unless a concealment mechanism is modeled. Do not calculate MOS from an invented formula. A network or playout proxy can be useful without claiming measured human experience.

## Closest works and the novelty boundary

The titles and author lists of `R01`, `R02`, `R04`, and `F01` were rechecked on their publisher or author-preprint pages. No mismatch was found. These checks do not upgrade an abstract-only reading to a full-method review.

- **R01, Sueda, Saiki, and Koike (2026):** the public abstract already describes using application state to suppress some handovers during continuity-sensitive sessions. The Japanese report's full methods were not obtained through the public page or targeted searches. Treat this as a close prior work and an unresolved detailed comparison, not evidence that our mechanism is new. [IEICE record](https://ken.ieice.org/ken/paper/202603059csa/eng/)
- **R02, Nadeem, Ali, Ali, and Manzoor (2026):** the publisher confirms a QoS-aware framework, including application-related weighting. The page requires subscription access for the full article; public-title, DOI, author-manuscript, and repository searches did not yield an accessible full method. Do not implement a guessed version and call it a reproduction of RAQOH. [Springer record](https://link.springer.com/article/10.1007/s11235-026-01410-6)
- **R04, Lee, Lu, and Doppler (2025):** the arXiv record confirms the context-aware roaming paper and its authors. Distinguish the use of an LLM in a decision layer from evidence that application playout improves. Use the existing selected-full-text review for a precise comparison. [Author preprint](https://arxiv.org/abs/2505.04174)
- **F01, Kim, Kim, Lee, Lee, and Golmie (2019):** the publisher confirms the application-based AP-selection study. Application-related selection is an established topic; the new paper needs a narrower contribution. [PLOS ONE article](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0210738)

A defensible contribution can be the reproducible test of a clearly stated tradeoff: how application deadlines, uncertain candidate information, and switching cost affect the value of roaming. It may include a transparent policy and useful negative results. Do not claim the first application-aware roaming method, state-of-the-art superiority, or a novel algorithm without a stronger comparison.

## Proposed professional structure

IEEE's author guidance separates the research question, reproducible method, results, interpretation, and supported conclusion. Follow the exact target venue's instructions when chosen. A general IEEE-style layout is not proof of acceptance or compliance with every venue. [P05: IEEE structure guide](https://journals.ieeeauthorcenter.ieee.org/create-your-ieee-journal-article/create-the-text-of-your-article/structure-your-article/)

For this study, the following is our proposed structure:

1. **Title and abstract.** Name the application-aware handoff question and simulation scope. Write the abstract after results are final. Include the strongest qualified finding and its main limitation.
2. **Introduction.** Explain one concrete mobility problem, the research question, and the contribution that the evidence can support.
3. **Related work.** Compare the closest methods by inputs, control location, application treatment, switching cost, and evaluation type. Mark missing full-method access.
4. **System model and assumptions.** Define topology, mobility, candidate observations, report age, queue service, packet workloads, and handoff interruption. Define units and symbols once.
5. **Decision policies.** Give reproducible rules or pseudocode. Distinguish a reproduced method, an inspired baseline, and a new study-specific heuristic. Explain parameter selection without using test outcomes.
6. **Experimental method.** Describe scenario families, random streams, paired trials, train/tuning/test separation where relevant, metrics, confidence intervals, and failure/censoring rules.
7. **Results.** Answer each research question with a small set of figures. Include losses, tradeoffs, and conditions where the policy is worse. State the sample unit and number of runs.
8. **Discussion and limitations.** Explain likely mechanisms and alternate explanations. Separate observed model behavior from predicted behavior on real devices.
9. **Conclusion.** Answer the question within the tested setting and name the next validation step. Introduce no new result.
10. **Availability and acknowledgments.** Link code/configuration/results, explain how to regenerate them, and disclose AI assistance. Append detailed parameter tables and checks if the venue permits.

Keep ordinary sentences short. Prefer “the policy changed AP fewer times” to “the system achieved unprecedented mobility intelligence.” A percentage must have a named baseline, metric, condition, and uncertainty. Figures should label units and show run-level variation; a polished diagram cannot replace validation.

## Statistical and artifact checks

The independent trial is a complete scenario run with its seed or mobility/load block. Packets within one run are not independent experimental replications. Pair policies on the same generated environment while keeping policy-internal state separate. Report paired differences and run-level uncertainty. Label exploratory sweeps as exploratory; do not hide unfavorable cells in an overall average.

Choose a few primary outcomes before the final run. With many metrics and conditions, avoid treating every apparent difference as a separate confirmed finding. A confidence interval describes uncertainty under this model and sampling design; it does not account for an inaccurate radio model.

Save the final configuration, source revision, seeds, run manifest, raw per-run results, and figure-generation instructions. This follows IEEE's support for sharing methods, data, and code. It does not require publishing personal identifiers or secrets. [P06: IEEE reproducibility guidance](https://journals.ieeeauthorcenter.ieee.org/create-your-ieee-journal-article/research-reproducibility/)

## AI assistance and authorship

IEEE's current policy calls for disclosure of AI-generated content, including code, with the system, affected sections, and level of use identified in the acknowledgments. Editing alone is treated differently, but this project involves research support and code generation, so an editing-only description would be incomplete. [P07: IEEE submission policy](https://conferences.ieeeauthorcenter.ieee.org/author-ethics/guidelines-and-policies/submission-policies/)

For the later manuscript, record the tool and any verified model identifier, the assistance with literature search, code, experiments, analysis, figures, and writing, and the checks actually completed. Do not invent an exact model version or claim human verification that has not occurred. Human authors must review and approve the final submission and remain responsible for it. AI tools belong in the disclosure, not as people in the author list.

Use only author names, affiliations, funding, contact details, and contributions supplied or confirmed by the user. A repository owner name does not establish a legal name, university, laboratory, or funding source. Do not insert received/accepted dates, an IEEE copyright notice, or a publication DOI into a draft as if publication had occurred.

No participant study or hardware trial should be implied by synthetic media and simulation. If future work involves people, real conversations, or institutional network data, its reporting and consent basis must be documented at that time.
