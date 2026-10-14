# Foundational studies that constrain the research claim

Reviewed on 14 October 2026. These older studies are included because a recent paper is not automatically the first paper to address an idea. The summaries below are our own reading notes. They are not replications.

## F01 Application-based access point selection

**Mun-Suk Kim, Yena Kim, SeungSeob Lee, SuKyoung Lee, and Nada Golmie.** “A user application-based access point selection algorithm for dense WLANs.” PLOS ONE, 16 January 2019. [Publisher full text](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0210738). DOI: 10.1371/journal.pone.0210738.

**Reading depth:** full-text sections on measurement, application traffic, selection, switching, and evaluation inspected.

The method learns AP performance from application traffic in places a person visits again. Its switching rule uses a minimum bandwidth requirement and a delayed, probabilistic change to avoid many devices moving at once. Evaluation combines measurements with simulation. The findings depend on repeated visits and learned history; they do not establish performance for every moving campus client. This paper prevents a claim that application-based selection or application-triggered switching is new. Sections 3, 4.4, and 5.3 are the most relevant reading points.

## F02 Handoff costs and short prediction windows

**Peter Dely, Andreas Kassler, Nico Bayer, Hans Einsiedler, and Christoph Peylo.** “Optimization of WLAN associations considering handover costs.” EURASIP Journal on Wireless Communications and Networking, 16 August 2012. [Publisher full text](https://link.springer.com/article/10.1186/1687-1499-2012-255). DOI: 10.1186/1687-1499-2012-255.

**Reading depth:** full-text model, objectives, comparison rules, evaluation, sliding-window method, and limitations inspected.

The authors include service interruption in association optimization. They distinguish an ideal future-aware bound from a practical estimate of the near future. Their main objective concerns download rates, and their numerical study is not a deployed roaming system. This is direct prior work for switching cost and short-horizon decisions. Adding either feature alone cannot support a novelty claim. Their discussion of alternative application objectives also makes a broad “cost plus applications” claim too weak without closer comparison.

## F03 Load-aware selection with 802.11k and 802.11v

**Toni Adame, Marc Carrascosa, Boris Bellalta, Iván Pretel, and Iñaki Etxebarria.** “Channel load aware AP / Extender selection in Home WiFi networks using IEEE 802.11k/v.” IEEE Access, 2021. [Author full text and version history](https://arxiv.org/abs/2004.08110). DOI: 10.1109/ACCESS.2021.3059473. The first preprint was posted on 17 April 2020; version 2 is dated 22 February 2021.

**Reading depth:** full-text mechanism, metric, simulation assumptions, testbed comparison, and open challenges inspected.

The selection metric combines signal with load on access and backhaul links. The paper includes simulation and a home-network testbed. It supports treating load-aware selection as established work. Its extender topology and association comparison do not directly validate our moving-client interruption model. We must also distinguish a recommended AP from a stock client's actual response. Sections IV, VI, and VII explain the mechanism, evidence, and remaining challenges.

## F04 Estimating service before association

**S. Vasudevan, K. Papagiannaki, C. Diot, J. Kurose, and D. Towsley.** “Facilitating Access Point Selection in IEEE 802.11 Wireless Networks.” Internet Measurement Conference, 2005. [Conference record](https://www.usenix.org/conference/imc-05/facilitating-access-point-selection-ieee-80211-wireless-networks); [full paper](https://www.usenix.org/legacy/events/imc05/tech/full_papers/vasudevan/vasudevan.pdf).

**Reading depth:** full-text estimation method, experiments, and conclusion inspected.

The paper estimates potential bandwidth using beacon delay. Its experiments used a controlled low-noise setting and old 802.11 hardware. The authors explicitly left several noise, timing, and vendor issues open. It establishes that candidate-service estimation is a long-standing problem. It does not provide a ready calibration for modern APs. For our study, the key lesson is to make the availability and age of candidate measurements explicit.

## Search record

The actual searches that led to these sources included “WiFi access point selection switching cost dwell time application QoE handover paper” and “Wi-Fi roaming handover application aware uncertainty measurement age decision 2024 2025 2026 paper.” We then followed publisher and author links and checked method and evaluation sections. The four works are included for conceptual overlap and primary-source access. Unrelated cellular handover results were not used as direct evidence for Wi-Fi.

The evidence supports a narrow research question, not a claim that nobody has combined these ideas before.
