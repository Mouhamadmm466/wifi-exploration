# Wi-Fi and research terms in simple words

| Term | Simple meaning |
| --- | --- |
| Access point or AP | The device that connects a phone or computer to a Wi-Fi network. |
| Client or station | The phone, laptop, or other device using the Wi-Fi connection. |
| Roaming or handoff | Changing from one serving AP to another. |
| SSID | The network name a user normally sees. |
| BSSID | An identifier for a particular basic Wi-Fi network, often associated with an AP radio. Several BSSIDs can use one SSID. |
| RSSI | A measure of received signal strength. It does not tell us the whole connection quality. |
| dBm | A logarithmic power unit. For typical received Wi-Fi signals, −50 dBm is stronger than −75 dBm. |
| Load | How busy a network resource is. Different papers measure this differently; station count, channel use, and queued traffic are not the same quantity. |
| Airtime | Time spent using the wireless channel. |
| Throughput | The rate of data transfer. Always check whether a paper counts all transmitted data or useful delivered data. |
| Latency | How long delivery takes. |
| RTT | Round-trip time: how long a request and its reply take together. It is not one-way delay. |
| Jitter | Variation in packet timing. It is not directly modeled in this first experiment. |
| Blackout | A period when the model delivers no data during a handoff. |
| Hysteresis or switching margin | A rule that requires a clear improvement before changing AP, to avoid repeated small changes. |
| Ping-pong | Moving from AP A to B and quickly back to A. Our exact time window is five seconds. |
| QoS | Measurable service properties, such as rate, delay, and loss. |
| QoE | The user's experience. Network measurements alone do not fully measure it. |
| Policy | The rule that decides whether and where to switch. |
| Baseline | A simpler or established rule used for comparison. |
| Ablation | Removing one part of a method to test what that part contributes. |
| Proxy | An indirect measure. Our service-deficit score is a proxy, not measured call quality. |
| Random seed | A starting number that lets a program recreate the same random sequence. |
| Paired comparison | Testing two rules in the same simulated conditions, then comparing their outcomes. |
| Bootstrap interval | A range calculated by repeatedly resampling whole experimental results. It reflects the sampled variation, not every kind of uncertainty. |
| Model mismatch | The real or simulated world differs from the formula used to predict it. |
| Preprint | A research manuscript shared before, or separately from, formal publication. Its review status must be checked. |
| Novelty | What is new compared with earlier work. A useful project can still need a narrower novelty claim. |

Definitions are simplified for this project. The [mechanism review](literature/mechanisms-and-evidence.md) gives the technical sources and boundaries.
