# Research question and scope

Date: 14 October 2026. Status: exploratory research, before manuscript writing.

The broad project title is **Application-Aware Handoffs in Dense Wireless Networks**. A more precise working title for this first study is **When Is a Wi-Fi Handoff Worth the Interruption? Application Needs, Switching Cost, and Old Load Reports**.

We study a simple question: can a device make better roaming decisions by comparing the expected benefit of a new access point with the cost of changing connections? We also ask when old information makes that comparison unsafe. The aim is to find the conditions where a rule helps, fails, or adds no value.

## What the problem means

An access point, or AP, connects a device to a wireless network. A handoff changes the serving AP. A stronger received signal does not by itself tell us how much useful service the device will receive. Other users, interference, queues, and the network behind the AP can also matter. Changing AP can interrupt service.

The application matters because a file download and a live conversation do not need the same service. A short gap can be acceptable for a file download but harmful during a conversation. This first model represents these differences with explicit service requirements. It does not simulate a video player, a codec, or human satisfaction.

The observation problem is equally important. A device can measure its current connection, but it cannot normally know every candidate AP's current end-to-end performance. A load report describes an earlier observation and may be incomplete. We therefore separate the true simulated network state from the information available to the decision rule.

See [mechanisms and evidence](literature/mechanisms-and-evidence.md) for the sources behind these network facts and their practical limits.

## What earlier work changes

Application-based selection, load-aware selection, and handoff cost are established topics. In particular, the 2019 application-based study, the 2012 handoff-cost study, and the March 2026 application-context technical report are close enough to rule out a broad claim that these ideas are new. The [foundation review](literature/foundations.md) and [recent review](literature/recent-review.md) identify what each source supports.

Our possible contribution is narrower: a reproducible comparison that separates application requirements, interruption cost, and the age of candidate load information. Whether this combination is a new research contribution remains open. Access to the full text of the closest recent work is needed before making that claim.

## The main research question

For one moving client with several overlapping APs, how do application requirements, handoff interruption, and candidate-report age change the benefit of an application-aware roaming rule compared with simpler rules?

There are four parts:

1. Does knowing the application requirement improve service compared with using signal and load alone?
2. Does charging for a handoff improve service compared with an application-aware rule that ignores that cost?
3. Does a penalty for old candidate reports help, or does it make the device stay too long on a poor AP?
4. Which conditions reverse the apparent benefit?

## Hypotheses that can fail

These are exploratory hypotheses. They are not promises and were not registered with an external preregistration service.

| Hypothesis | Evidence that would support it in this model | Evidence against it |
| --- | --- | --- |
| H1: Application information helps when network service and application needs differ | Lower service deficit than the load-aware rule under the same observations | The simpler rule matches or beats it; gains vanish with a small change in requirements |
| H2: Explicit switching cost helps when interruptions are costly | Lower service deficit than the otherwise matching no-cost rule as interruption rises | Fewer handoffs but worse service, or no meaningful difference |
| H3: Caution about old reports helps under changing load | Lower service deficit than the otherwise matching no-age-penalty rule at older report ages | Delayed escape from a bad AP makes performance worse |
| H4: No rule is best everywhere | Stable, low-cost, or abrupt-change cases favor a simpler rule | Apparent universal victory requires checking the model and baseline settings for bias |

The main comparison uses service deficit, defined exactly in the [model document](simulation-model.md). We also report throughput, handoffs, and interruption separately. A weighted score can hide an important trade-off, so it is never the only result.

## Scope of this first experiment

We model one foreground client, a set of overlapping APs, and background load that changes without reacting to the client's decisions. All APs are treated as belonging to a network where the IP address can stay the same. The client is assumed to be able to apply the selected association.

This is a decision-level simulation. It is useful for checking an idea and testing its assumptions. It does not reproduce radio frames, channel contention, encryption, scanning, firmware, TCP recovery, or an operating system's roaming policy.

“Dense” describes overlapping choices in this pilot. Six modeled APs do not demonstrate dense-network scaling. Independent background load does not reproduce shared-channel interference. Because only one client changes AP, the study cannot establish network-wide fairness, load balancing, or stability when many clients act together.

## Why start with a small rule

A small rule lets us inspect each decision and remove one component at a time. If it fails, we can identify whether the cause is a poor service estimate, a wrong interruption estimate, or too much caution. A large learning system would add training data, runtime cost, and additional explanations to an already uncertain model.

Machine learning remains an option if we later have evidence that better estimates improve decisions. It should first predict something testable, such as interruption duration or candidate service, with a separate error analysis. We do not need an LLM in the fast decision path to answer the present question.

## What would justify a paper

The first package can support a paper proposal and an exploratory simulation report. A stronger research paper needs:

- A direct comparison with the closest prior algorithms, using their full definitions or released code.
- Evidence that the chosen metric represents an application outcome that matters.
- Tests where the policy's service estimate differs from the simulator's true service law.
- Changes in layout, application requirements, mobility, measurement errors, and client behavior.
- A model of multiple clients if the paper claims network-wide benefits.
- Trace-based or device-based calibration before claims about real Wi-Fi performance.

The next stage may still use simulation. A real-world improvement claim, however, needs evidence from real equipment or suitable measured traces. The pilot's conclusions must stay within its model.
