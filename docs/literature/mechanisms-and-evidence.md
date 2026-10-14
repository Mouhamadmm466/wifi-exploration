# What Wi-Fi roaming mechanisms can and cannot do

Evidence review date: 14 October 2026. This part covers mechanisms, measurements, and tools. It complements the review of recent decision algorithms. It is a focused evidence review, not an exhaustive systematic review. The source IDs below also appear in `references/mechanism-sources.json`.

## The practical problem

The first experiment should ask **when a device should change its access point**, given limited and delayed information. It should not assume that finding a better access point makes the change free.

A useful working model has five parts: observe the network, decide whether to move, find or confirm a target, complete the wireless transition, and restore useful application delivery. Some parts overlap. Their times must not simply be added unless the implementation shows that they run in sequence.

The proposed first simulation studies decisions within one network, with the same IP address before and after a change. This is a scope choice. It avoids mixing wireless selection with address acquisition, routing changes, or transport migration.

## Three standards provide different kinds of help

| Mechanism | Practical role | What our experiment must still decide |
|---|---|---|
| 802.11k | Supplies radio information, including neighbor information. | Which observations are available, how old they are, and which targets are worth checking. |
| 802.11v | Provides network advice about possible transitions. | Whether the client accepts the advice and when it acts. |
| 802.11r | Reduces security work during a supported fast transition. | Whether switching is useful, how to discover the target, and the full service interruption. |

Apple documents both client control and the use of signal strength, channel utilization, and associated-client count in candidate scoring. Thus, beating a signal-only policy does not establish an improvement over modern client behavior. A stronger comparison also needs load-aware selection and a native-client baseline in later hardware work. Device and operating-system support must be checked for the exact test configuration. [M01: Apple deployment documentation](https://support.apple.com/en-euro/guide/deployment/dep98f116c0f/web)

## What can actually be observed?

These are proposed information boundaries for the experiment, rather than claims that every driver exposes every field.

| Quantity | Plausible source | Restriction in a fair experiment |
|---|---|---|
| Current signal strength | Associated-link measurements | Add measurement noise and a stated sampling period. |
| Candidate signal strength | Scan results or network reports | Store observation time; do not silently refresh it every decision. |
| Candidate channel load | Advertised BSS Load or controller telemetry | Include missing reports, averaging, delay, and age. |
| Current application delivery | Client counters or controlled traffic | Use only completed observations from the past. |
| Candidate application delay or goodput | Prediction or a real probe | It is not directly known before association. Label predictions; charge for probes if modeled. |
| Future movement or future load | Not available to an ordinary policy | Reserve for an explicitly named oracle, if used. |
| Application need | An explicit class declared by our test application | Use a class such as interactive or bulk; no content inspection is needed. |

The hostapd configuration exposes separate BSS Load update and utilization-averaging periods. It also has a fixed-load testing option. This supports testing stale load information, but does not establish that advertised utilization equals spare application throughput. Station count also cannot tell us how much traffic each station sends. These last two points are interpretation limits for our model. [M02: pinned hostapd configuration](https://android.googlesource.com/platform/external/wpa_supplicant_8/+/e1f26c3029a96c86624ab8f35b28c85d5401a4a3/hostapd/hostapd.conf)

All compared policies should receive the same observation record for a given time and scenario. The proposed policy may use more fields than a signal-only baseline, but a load-aware baseline must have access to those same fields. Evaluator-only values belong in a separate data structure. A target's true queue, future load, and future delivered quality must not enter a policy through a convenient helper function.

## Evidence that changes the research design

### M03 — ns-3 official Wi-Fi model documentation

**Type and reading:** project documentation; overview, scope limitations, association, and roaming sections read on 14 October 2026. The moving documentation URL did not identify a pinned release in the inspected page.

The inspected page states that its Wi-Fi model lacks Layer-2 roaming, authentication/encryption, and processing delays. It describes association and several modern PHY/MAC features. This does not mean that all external ns-3 extensions lack roaming. It means that adopting ns-3 would require checking a named release and any extension, then validating the missing transition behavior. Our first simulator is therefore described as a decision-level model, not an implementation of 802.11k/v/r. [Official design page, sections 35.1.2 and 35.1.3.2.2](https://www.nsnam.org/docs/models/html/wifi-design.html)

### M04 — Mininet-WiFi official architecture

**Type and reading:** project documentation; introduction, architecture, and wireless-medium sections read on 14 October 2026; no release version shown.

Mininet-WiFi uses Linux virtual wireless interfaces and tools including hostapd and wpa_supplicant. Its wireless medium uses traffic control or wmediumd. It is a useful later step for testing control messages and real application software. A virtual radio cannot establish the interruption distribution of a physical adapter, firmware, and operating system. Any emulation experiment should pin the complete software stack and disclose the medium model. [Project documentation](https://mininet-wifi.github.io/)

### M05 — Mishra, Shin, and Arbaugh: empirical handoff analysis

**Type and reading:** University of Maryland technical report dated 18 September 2002; related journal publication in 2003. The institutional eight-page PDF was accessed; process, experiment, and latency-decomposition passages were inspected. Text extraction contains damaged words. This is a targeted reading, not a claim that the 2003 publisher version was read.

The early measurements separated probing, authentication, and reassociation. Probe delay dominated their equipment. The result supports measuring phases separately; its absolute timings and percentages must not be treated as current Wi-Fi 6/7 behavior. The experiment also makes device variation a reason to report the exact client and AP combination. [Institutional record and report](https://drum.lib.umd.edu/items/05f9c530-8b14-4514-b530-229e1318b219)

### M06 — Unlocking Mobility for Wi-Fi-Based Wireless Time-Sensitive Networks

**Type and reading:** peer-reviewed IEEE Access article, published 23 February 2024; DOI `10.1109/ACCESS.2024.3369481`. The institutional full PDF was accessed. The abstract and targeted passages on the handover procedure, hardware implementation, and measurements were inspected.

Avila-Campos and colleagues combine location information and RSSI with a controlled openwifi platform. Their design changes driver/radio behavior and prepares the wired and wireless paths. The hardware study shows why scan avoidance and transition execution deserve separate attention. It is not a commodity-laptop roaming benchmark. We should not copy its measured delay into our simulator as a universal fast-transition cost. Instead, our costs remain assumptions until measured on our target equipment. [Ghent University full text](https://backoffice.biblio.ugent.be/download/01HT260J62BD4W3QAS1SPH8P35/01HT262K38E2S7NVKFT4WGMV0Z)

### M07 — QUIC-HOA

**Type and reading:** peer-reviewed GLOBECOM conference paper, 8–12 December 2024; added to IEEE Xplore on 11 March 2025. Publisher and institutional abstracts and metadata read; full methods and results were not accessible in this review.

Chen and colleagues examine QUIC connection migration during hard handovers and propose a handover-aware cross-layer trigger. The abstract reports substantial gains in its tested conditions. We do not reproduce its numerical gains because the full setup was not checked. Its relevance here is the boundary between wireless transition and transport recovery. Moving to a new IP network requires a separate experiment from our same-subnet design. [Publisher record](https://ieeexplore.ieee.org/document/10900944/), [authors' university record](https://scholar.nycu.edu.tw/en/publications/quic-hoa-a-cross-layer-handover-aware-design-for-quic-connection-/)

### M08 — Wi-Fi Multi-Link Operation: An Experimental Study of Latency and Throughput

**Type and reading:** author preprint submitted 3 May 2023, linked to a journal article with DOI `10.1109/TNET.2023.3283154`; institutional publication records list the journal issue in 2024. The full preprint was accessed; abstract, measured-dataset description, trace-based simulation method, and relevant results passages were inspected.

Carrascosa and colleagues use measured 5 GHz occupancy traces to study multi-link behavior. The title must not be read as evidence of commercial Wi-Fi 7 roaming trials. The study finds that the effect of multiple links depends on their load pattern and packet mapping. It motivates stress tests with uneven candidate loads, but does not validate our single-link handoff model. [Author preprint](https://arxiv.org/abs/2305.02052), [institutional publication record](https://www.upf.edu/web/wisecom/publications?_ppc_WAR_ppcportlet_INSTANCE_XzeaCbHWu7o9_cur=3&_ppc_WAR_ppcportlet_INSTANCE_XzeaCbHWu7o9_delta=20&_ppc_WAR_ppcportlet_INSTANCE_XzeaCbHWu7o9_ppcSearchKeyWord=&_ppc_WAR_ppcportlet_INSTANCE_XzeaCbHWu7o9_resetCur=false&p_p_id=ppc_WAR_ppcportlet_INSTANCE_XzeaCbHWu7o9&p_p_lifecycle=0&p_p_mode=view&p_p_state=normal)

### M09 — Seamless Roaming based on Distributed Multi-Link Operation over IEEE 802.11bn

**Type and reading:** WFCS conference paper, 10–13 June 2025; publisher abstract and metadata read; full paper not obtained.

The proposed method allows association with several APs through enhanced multi-link operation. The publisher describes simulation results. Its reported short transition is not a hardware measurement and is not a promised property of every Wi-Fi 7 or future Wi-Fi 8 product. It provides a future comparison: when multiple links reduce interruption, does application-aware timing still add value? That is outside the first single-link experiment. [IEEE publisher record](https://ieeexplore.ieee.org/document/11077616/)

### M10 — wpa_supplicant control interface

**Type and reading:** official API documentation labeled version 2.5; command, event, status, scan, and BSS sections read on 14 October 2026. It is older documentation, not evidence of the current installed version.

The interface provides commands, status, and event notifications that can support a controlled Linux research client. This makes command time and observed completion separately recordable. The chosen build, driver, and firmware still need a capability check. A successful command response must not be counted as a successful roam without checking the resulting association and data delivery. [Official control-interface documentation](https://w1.fi/wpa_supplicant/devel/ctrl_iface_page.html)

### M11 — QUIC transport specification

**Type and reading:** IETF RFC 9000, May 2021; sections 8.2 and 9 on path validation and connection migration inspected.

QUIC supports address changes using connection IDs and path validation, with conditions on when migration is allowed. That mechanism is separate from selecting a Wi-Fi AP. Our first experiment holds the IP path constant; later work can measure transport recovery after an address change. Neither fast association nor QUIC support alone proves uninterrupted application delivery. [RFC 9000](https://www.rfc-editor.org/rfc/rfc9000.html#section-9)

### M12 — WebRTC statistics

**Type and reading:** W3C Candidate Recommendation Draft dated 25 September 2025; status and inbound-media statistics sections inspected. This is a draft, not a final W3C Recommendation.

The specification defines counters including video freezes, audio concealment, packet loss, jitter, and buffer delay. These offer later application-level measurements that go beyond Wi-Fi signal and average throughput. They are not direct user satisfaction scores, and field availability must be checked in the chosen browser. Synthetic deadline failures in our simulation should therefore be called a service-quality proxy, not measured video-call quality or human QoE. [Dated WebRTC statistics draft](https://www.w3.org/TR/2025/CRD-webrtc-stats-20250925/)

## What these sources justify for today's simulation

The justified design is a controlled exploration of a tradeoff: a switch may improve future service while causing a short interruption now. We should compare signal, load-aware, and cost-aware policies under identical causal observations. We should then remove each extra feature to see which one helps. The model should also include situations where staying is better.

The chosen interruption durations, application deadlines, path-loss parameters, and telemetry delays are experimental settings. They are not measurements from these papers. Their role is to test sensitivity. Conclusions should state the parameter range in which the result holds.

With a coarse decision interval, a short handoff can be charged as a fractional loss of service within an interval. However, this does not resolve individual packet deadlines. A 250 ms model cannot establish a 10 ms packet-delay percentile or the timing of a video freeze. If its outputs include deadline failure, the report must explain exactly how this proxy is calculated. Packet-level or real-media validation is a later step.

## Search record and review limits

All searches below were run on 14 October 2026 using the web search tool. Search results were used for discovery. Technical claims above use publisher, institutional, standards-body, author-preprint, or project sources. The table groups consecutive queries with the same purpose; the JSON record keeps the literal query text.

| Search group | Queries and follow-up | Outcome |
|---|---|---|
| Standards in practice | Apple Wi-Fi roaming k/r/v; hostapd BSS Load; wpa_supplicant control and background scan | M01, M02, M10 retained. |
| Tool boundaries | ns-3 Wi-Fi roaming limitations; Mininet-WiFi mobility and medium model | M03 and M04 retained; official sections inspected. |
| Foundational measurement | Exact Mishra handoff-analysis title; 2003 DOI follow-up | M05 institutional PDF retained; publisher full page failed to open. |
| Recent controlled mobility | Exact Ghent mobility title; Wi-Fi 6 roaming experimental 2024; Wi-Fi roaming measurement 2025 | M06 retained. A 2025 robotics study and an ICNC voice comparison were found but not included because full-text access was not completed. |
| Cross-layer recovery | QUIC-HOA 2024; exact title with PDF/authors; university-domain search | M07 retained at abstract depth; M11 checked for protocol scope. |
| Multi-link boundaries | Wi-Fi 7/MLO roaming measurement 2025/2026; distributed-MLO exact title; author/institutional follow-ups | M08 targeted full-text review; M09 abstract-only review. Other results were not treated as measured handover evidence. |
| Application measurement | Direct visit to the W3C statistics specification; freeze and concealment field search | M12 retained at selected-section depth. |

This set contains 12 distinct evidence sources: five research works and seven technical documents. It does not mean that 12 recent papers were fully read. Some papers are old foundations, two were available only at abstract depth, and technical documents are not research papers. The broader algorithm review is a separate part of the project.
