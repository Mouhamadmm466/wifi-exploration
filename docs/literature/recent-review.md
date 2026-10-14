# Recent evidence: application-aware Wi-Fi roaming

Review date and cutoff: **14 October 2026**. This is a targeted review of 13 works from 2023–2026. It is not an exhaustive or systematic review. Eight entries include selected full-text sections; five rely on abstracts or publisher excerpts. We have not reproduced these papers' experiments. The complete checked titles, authors, dates, links and reading levels are in [the source register](../../references/recent-sources.json).

The main finding is clear: **using application information in Wi-Fi roaming is already an established research direction**. The project needs a narrower question and a fair experiment. A new weighted score alone will not establish a new contribution.

## How to read these notes

“Reported” describes what the source says. It does not mean we independently proved the result. “Assessment” gives our interpretation and the reason behind it. An abstract can establish that an idea has already been proposed. It usually cannot establish exactly how the algorithm works or whether its experiment is strong.

“Selected full text” means we inspected relevant methods, setup, results or limitations in the actual paper. It does not mean every equation, proof, figure or reference has been audited. No entry below should be described as a completed independent replication.

## The closest work

### R01 — Application context already controls handover (2026)

[IEICE technical report IN2025-76](https://ken.ieice.org/ken/paper/202603059csa/eng/). **Reading:** English abstract and metadata; Japanese full report unavailable in this review.

**Reported:** Terminal application state and link indicators guide AP selection. The controller can postpone a handover during an application that needs continuity, even when link indicators suggest an improvement. Experiments compare with the operating system's default behavior.

**Assessment:** This is the strongest direct overlap with the proposed idea. We cannot claim that application-based handover suppression is new. The abstract does not give enough detail to judge traffic generation, interruption measurements, client variety or statistical confidence. Obtain the full report before making a narrow novelty claim.

### R02 — Application-dependent QoS weights (2026)

[RAQOH/AOH, Telecommunication Systems](https://link.springer.com/article/10.1007/s11235-026-01410-6). **Reading:** publisher abstract and metadata; full article restricted.

**Reported:** AOH filters signal changes with hysteresis. RAQOH adds bandwidth and loss information; its weights adapt to network conditions and application type. Evaluation uses a hybrid Mininet–ns-3 environment.

**Assessment:** Application-dependent scoring and congestion-sensitive roaming are already covered here. We cannot infer from the abstract whether the method predicts actual handover interruption or handles stale measurements. Those are unresolved comparison questions, not proven gaps. A faithful baseline needs the full algorithm and parameter settings.

### R03 — Load-aware scoring with a comparison problem (2025)

[ELAHA, ECTI-CIT](https://ph01.tci-thaijo.org/index.php/ecticit/article/view/263263). **Reading:** selected full-text methods, setup, results and discussion.

**Reported:** ELAHA combines normalized RSSI with a load measure based on connected-device count. MATLAB tests use three APs, 10/30/60 stations and constant-rate UDP traffic. The RSSI baseline uses 5 dB hysteresis; ELAHA uses 10 dB.

**Assessment:** This provides a useful simple baseline. However, the changed hysteresis also affects handover count, so the comparison does not isolate load awareness. Our experiments should tune both fairly and compare them with equal hysteresis. Device count is an imperfect congestion measure when clients send different traffic volumes. These are limits of transferring the result, not evidence that the algorithm has no value.

### R04 — LLM roaming has an important timing limit (2025)

[On-Device LLM for Context-Aware Wi-Fi Roaming, arXiv v2](https://arxiv.org/html/2505.04174v2). **Reading:** selected method, evaluation, limitations and setup sections; author repository checked.

**Reported:** The work selects APs and adjusts roaming thresholds using context such as time and location. Its AP-selection evaluation centers on average RSSI and handover count. Section 3.5 states that LLM inference takes seconds, exceeding its 10–100 ms decision target. The practical threshold task updates every 30 seconds.

**Assessment:** An LLM is not justified in our fast decision path by these results. Good RSSI and fewer switches do not directly prove smoother calls. Cite the three authors in v2. The author's repository identifies an ICML ML4Wireless workshop presentation; do not call it an ICML main-track paper.

### R05 — Scale and control overhead also matter (2026)

[RAPSOVA, Computer Communications](https://www.sciencedirect.com/science/article/pii/S014036642600157X). **Reading:** publisher-indexed abstract and conclusion excerpts; direct retrieval failed and full text was not read.

**Reported:** A reinforcement-learning system divides the network into clusters, adapts to changing AP/client counts and selectively shares learning updates to limit overhead.

**Assessment:** A policy may improve one device while harming the wider network. This work makes scaling, changing topology and control traffic important comparison dimensions. Its available abstract does not establish application-session protection or the detailed cost of handovers. We must avoid claiming these are absent from the full work. Numerical claims and a reproduction baseline remain pending full-text access.

## Related approaches that shape the experiment

### R06 — Learning can include more than signal strength (2023 preprint; 2024 conference)

[MADAR](https://arxiv.org/html/2304.01210v1). **Reading:** selected full-text method and evaluation; later IEEE CCNC venue checked through publisher indexing.

**Reported:** Distributed multi-agent learning uses RSSI and channel-state information to improve roaming. The evaluation combines simulation and a realistic AP setting; its parameter table contains three APs, five channels and a 200 ms background scan interval.

**Assessment:** This is relevant to a learned baseline and scan cost. It does not by itself demonstrate application-level quality across many ordinary client devices. Channel-state information may be harder to obtain than RSSI on our chosen hardware, so we must state which inputs each baseline receives.

### R07 — Multiple links can change the cost of switching (2024)

[WiTwin architecture](https://arxiv.org/html/2404.18313v2). **Reading:** full-text architecture and operations sections.

**Reported:** A central digital twin uses measurements and position to guide association. The proposal assumes multi-link capabilities and moves links in sequence so one can continue to carry traffic. It assumes an ideal wired network for frame loss.

**Assessment:** A switching penalty measured for a single-radio client cannot simply be copied to this architecture. We should keep the initial experiment to one clearly stated device model. This is a proposed architecture, not evidence that every commercial Wi-Fi 7 client supports the described roaming behavior. No quantitative gain from this source is used here.

### R08 — Real hardware shows why timing deserves measurement (2024)

[Unlocking Mobility for Wi-Fi-Based Wireless Time-Sensitive Networks](https://biblio.ugent.be/publication/01HT260J62BD4W3QAS1SPH8P35). **Reading:** selected published full-text methods, results and conclusion.

The same work is reviewed as **M06** in [mechanisms and evidence](mechanisms-and-evidence.md). It is counted once in the source index. That review explains its specialized platform and why its hardware result cannot directly calibrate our simulator. Use the published DOI in the source register, not the placeholder in the accepted manuscript.

### R09 — Move before the link degrades (2023)

[Make Before Degrade, AINA](https://link.springer.com/chapter/10.1007/978-3-031-28451-9_49). **Reading:** publisher abstract and metadata; full chapter restricted.

**Reported:** A proof-of-principle software-defined Wi-Fi system uses computer-vision context to shift traffic before a path becomes poor. It demonstrates an industrial cloud-robotics use case and describes interruption-free mobility with a single radio.

**Assessment:** Predictive context and deciding when to move are not new concepts. We cannot extend the abstract's result to ordinary campus Wi-Fi or compare its delay definition with ours without the full method. External cameras also give this design information that a basic client policy may not have.

### R10 — QoE-oriented handoff extends beyond Wi-Fi (2024)

[Model-Free QoE-Aware Seamless Handoff](https://link.springer.com/article/10.1007/s11036-024-02305-z). **Reading:** publisher abstract and metadata; full article restricted.

**Reported:** S-MSH models handoff as a sequential decision problem, includes user traffic needs and uses Q-learning with a similarity mechanism. Simulation comparisons report reward and handoff-count improvements across heterogeneous networks.

**Assessment:** This is related method work, not direct evidence for Wi-Fi AP-to-AP roaming. A higher designed reward is not automatically a better video call. Its full QoE definition and simulation assumptions must be checked before borrowing its model or claiming a gap.

### R11 — Congestion and feasibility guards are already combined (2025)

[COHERE, arXiv v1](https://arxiv.org/html/2511.00439v1). **Reading:** selected full-text design and numerical results.

**Reported:** The framework ranks links using RSSI, load and delay, with operator- or data-based weights and an offloading feasibility rule. Mininet-WiFi evaluation covers 16, 32 and 64 stations in a modeled 5G/Wi-Fi setting.

**Assessment:** It is useful for designing congestion baselines, but cross-technology offloading differs from one-SSID Wi-Fi roaming. Its reported delay-cost improvement can exceed 100% because that cost can change sign; do not describe this as an equivalent reduction in physical latency. Peer-reviewed publication was not verified. Its abstract also retains a different framework name in places, so cite the title carefully.

### R12 — Application-specific costs need independent validation (2025)

[PEARL, arXiv v2](https://arxiv.org/html/2509.24085v2). **Reading:** selected reward, evaluation, limitations and appendices; author repository checks workshop status.

**Reported:** Wi-Fi Aware device-to-device control uses application delay tolerances and battery state. Evaluation combines measured logs with synthetic application use. The authors say stronger hardware validation with packet and energy counters is still needed.

**Assessment:** This supports application-dependent objectives, but it is not an AP-roaming result. Its configured tolerances are modeling choices, not universal standards for each application. We should test real outcomes separately from the score optimized by a policy. The paper is a NeurIPS AI4NextG workshop contribution, not a NeurIPS main-track result.

### R13 — Predicting a roam is different from improving it (2026)

[Proactive Roaming Prediction using LSTM, ICOIN](https://nsl.cau.ac.kr/papers/ictc/icoin2026-kwon-roaming.pdf). **Reading:** selected full-text dataset, model, evaluation and conclusion.

**Reported:** Factory traces cover over 80 vehicles and 40 APs. Table I gives 93,083,287 timesteps and 101,333 roaming events. A small LSTM predicts the AP ten seconds ahead; March 2025 is held out for testing. The authors acknowledge that rare roaming events inflate overall accuracy.

**Assessment:** The time-based test split is useful. We should also report precision, recall, false alarms and leave-device/site-out tests. Predicting an observed AP choice does not show that choice is best. A policy intervention is needed to test whether prediction reduces interruption. Automatic responses remain future work. Do not treat high event-detection accuracy as measured improvement in service continuity.

## What this means for our project

The following is our research judgment, based on the evidence above and the [older foundations](foundations.md). It is a plan to test, not a claim of novelty.

| Decision | Reason | Evidence to collect |
|---|---|---|
| Study application-dependent **benefit versus interruption cost** | Application context and load scores already exist. A useful question is when their benefit exceeds the harm from moving. | Actual service gaps and application outcome before/after each switch. |
| Include a simple, well-tuned load-aware baseline | Winning against weak RSSI logic can exaggerate the value of complexity. | Equal tuning budget, equal available observations, equal hysteresis comparisons. |
| Include a “stay during active session” baseline | Session-based suppression closely overlaps R01. | Cases where staying helps and where it traps the client on a failing AP. |
| Measure application quality separately from the policy score | The score can reward its own assumptions. | Deadline misses, useful throughput and call/video stalls where available. |
| Test stale and noisy measurements | A good AP estimate may be wrong by the time the switch happens. | Controlled observation delays, load shocks and confidence checks. |
| Start with a simple policy | More complex learning introduces training and timing costs. | Decision time, memory, stability and comparison with the same features. |
| Check all clients, not only the selected one | Moving clients redistributes load. | Fairness, worst-client performance and total control traffic. |

A defensible candidate question is: **When does using application needs and measured interruption cost improve roaming over well-tuned signal- and load-based rules, and when does it make roaming worse?** A negative result is useful if the experiment is fair and reproducible.

Before a paper claims a new mechanism, obtain R01 and R02 in full, compare their decisions step by step, and search the backward/forward citations of the closest sources. This review has not established that any proposed uncertainty rule, horizon or switching-cost formulation is new.

## Search and selection log

All searches below were run on **14 October 2026**. Search-engine date labels were treated as hints; bibliographic dates came from the source pages or paper itself. The searches were iterative, using titles found in earlier searches. R13 was added after another researcher supplied its primary PDF link; its title was then searched and its methods checked. Results were not exported as a complete search corpus, so we do not give a fabricated screening count or PRISMA diagram.

Primary-source pages used for evidence were publisher sites, arXiv, author repositories and university repositories. ResearchGate, search aggregators and author CVs sometimes helped discover a title or resolve a venue; their summaries were not used as the final basis for scientific conclusions.

Queries actually used included:

- `"Application Context" "Wi-Fi" "Handover" Sueda`
- `"On-Device LLM for Context-Aware Wi-Fi Roaming"`
- `"QoS-Aware Handoff Framework" Wi-Fi 2026`
- `"RAPSOVA" WiFi`
- `"Enhanced Load-Aware Handover" Wi-Fi`
- `Wi-Fi roaming handover 2024 2025 application aware dense reinforcement learning`
- `Wi-Fi handover 2023 2024 measurements 802.11r latency paper`
- `Wi-Fi handover roaming 2024 2025 2026 "arxiv" seamless multi link`
- `"Intelligent Handover Triggering Mechanism" "Wi-Fi"`
- `"Model-Free QoE-Aware Seamless Handoff" authors`
- `"RAPSOVA" Bellouch pdf`
- `"Wi-Fi" "roaming" "arxiv" "2025" seamless`
- `"Wi-Fi" "handover" "2023" "context" paper`
- `"RAPSOVA" "Bellouch" "hal"`
- `"RAPSOVA" "2026" Wi-Fi Bellouch Zitoune`
- `Wi-Fi roaming "2025" "arxiv.org/abs" handover`
- `"On-Device LLM for Context-Aware Wi-Fi Roaming" "Workshop" openreview`
- `"Unlocking Mobility for Wi-Fi-Based Wireless Time-Sensitive Networks"`
- `"PEARL: Peer-Enhanced Adaptive Radio" arxiv`
- `"COHERE" "2511.00439"`
- `"Distributed Multi-Agent Deep Q-Learning" "10.1109"`
- `"RAPSOVA" "Available online"`
- `"QoS-Aware Handoff Framework" "Nadeem" "Ali"`
- `"Proactive Roaming Prediction" LSTM 2026`

**Selection:** We prioritized direct AP roaming, application state, congestion, switching timing and practical evaluation. R07, R10, R11 and R12 are marked as adjacent because their architecture or control task differs from the intended campus experiment. Including them does not make them interchangeable baselines.

**Held for later:** “Intelligent Handover Triggering Mechanism in Wi-Fi Networks via Adaptation-based Reinforcement Learning” (ICT-DM 2024, IEEE document 10798924) was found, but the retrieved primary page exposed too little scientific content to assess it. “Optimizing Handover in Time-Sensitive Wi-Fi Networks through Machine Learning” (2024) appeared in the Ghent author record but was not reviewed. Both are follow-up reading priorities.

**Excluded from this recent set:** Older works belong in the foundations review. Patents and vendor material do not substitute for evaluated research. Cellular-only, LiFi-only, LoRaWAN and general channel-access work were not used to support Wi-Fi AP-roaming claims. We did not count repeated preprint, publisher and repository versions as separate studies. A failed request for a nonexistent v3 of R04 was corrected to the verified v2.

## Remaining evidence gaps

The biggest access gaps are the full reports for R01, R02 and R05. The biggest experimental gap is independent evidence on the intended clients and traffic. We also still need a documented citation-following pass, broader database searches and a later date update before manuscript submission. This first review is enough to reject a broad novelty claim and design stronger tests. It is not enough to say that the final proposed method is new or experimentally validated.
