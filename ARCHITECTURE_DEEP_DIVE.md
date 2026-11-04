# Technical Architecture & Engineering Deep Dive
## Sealand Logistics — OOG Route & Permit Retrieval-Augmented Logic (RAL) System

---

### 1. Conceptual Shift: From Probabilistic LLM RAG to Retrieval-Augmented Logic (RAL)

Traditional Retrieval-Augmented Generation (RAG) relies on:
1. Converting unstructured documents into vector embeddings.
2. Querying top-k chunks by cosine similarity.
3. Prompting a Large Language Model (LLM) to synthesize a text response.

While suitable for customer service chatbots, this pattern suffers catastrophic failure in heavy haulage engineering:
* **The Precision Gap**: A bridge with 4.85m clearance will physically crush a 4.90m boiler. LLMs cannot guarantee boolean inequality satisfaction ($4.90 > 4.85 \implies \text{BLOCKED}$).
* **Hallucination of Legal Checklists**: LLMs regularly invent permit form names or omit jurisdictional state transit taxes.
* **Latency & Cost**: An LLM agent takes 4–12 seconds and costs \$0.05–\$0.20 per query, failing high-volume route optimization.

**Retrieval-Augmented Logic (RAL)** transforms the stack:
* **Retrieval**: Fetches verified spatial nodes, highway segments, bridge load capacities, and statutory RTO rules from a Relational Spatial Graph (PostgreSQL).
* **Augmentation**: Injects physical transport engineering constraints (hydraulic axle line load under IRC:SP:35, hairpin turn radius, overhead sag tolerances).
* **Logic (The Solver)**: Executes a deterministic graph algorithm (NetworkX Dijkstra / A*) with composite risk weighting, outputting a mathematically verified corridor and an exact permit fee checklist in **1.55 milliseconds**.

---

### 2. Multi-Axle Physics & Load Distribution Engine

When moving super-heavy project cargo (e.g., 120MT power turbine), the load is mounted on multi-axle hydraulic modular trailers (e.g., Goldhofer, Scheuerle, or Nicolas axle lines).

#### 2.1 Indian Roads Congress Standard (IRC:SP:35)
Indian transport law regulates the maximum permissible load transferred by each axle line to highway pavement and bridge structures:
* Standard mechanical dual-wheel axle: 10.2 MT max.
* Hydraulic multi-axle modular line: **13.5 MT max per axle line**.

#### 2.2 Mathematical Model
Given:
* $W_c$: Net cargo weight (MT)
* $N_a$: Number of hydraulic axle lines
* $T_{\text{line}}$: Trailer tare weight per axle line $\approx 3.5\text{ MT}$
* $T_{\text{puller}}$: Heavy prime mover (ballast tractor) tare weight $\approx 12.0\text{ MT}$

The Gross Vehicle Weight (GVW) is formulated as:
$$\text{GVW} = W_c + (N_a \times T_{\text{line}}) + T_{\text{puller}}$$

The individual axle line loading $L_a$ is:
$$L_a = \frac{\text{GVW}}{N_a}$$

Safety condition:
$$L_a \le 13.5\text{ MT/axle line}$$

If $L_a > 13.5$, the engine triggers an immediate structural warning and computes the minimum recommended axle lines $N_{\text{rec}}$:
$$N_{\text{rec}} = \left\lceil \frac{\text{GVW}}{12.5\text{ MT}} \right\rceil$$

---

### 3. Spatial Highway Graph & Constraint Pruning

The road network is modeled as a weighted undirected graph $G = (V, E)$, where:
* $V$: Seaports (e.g., `PORT_CODE_INVTZ`), industrial hubs (e.g., `HUB_RAIPUR`), and major highway junctions (e.g., `JUNC_VIJAYAWADA`).
* $E$: Road segments characterized by distance $D_e$, design capacity $W_e^{\max}$, vertical clearance $H_e^{\min}$, width $W_e^{\max}$, and ghat terrain flag $G_e \in \{0, 1\}$.

#### 3.1 Edge Filtering Logic
For every edge $e = (u, v) \in E$:
1. Retrieve associated structural bottlenecks $B_e \subset \text{bridge\_constraints}$.
2. For each bridge $b \in B_e$:
   * If $W_c > W_b^{\max}$ or $H_c > H_b^{\min}$:
     * If $b_{\text{bypass\_available}} = \text{True}$:
       $$D_e \leftarrow D_e + \Delta D_{\text{bypass}}$$
       $$\text{Record } b \text{ as BYPASS\_APPLIED}$$
     * Else:
       $$E \leftarrow E \setminus \{e\}$$
3. If $G_e = 1$ (Ghat section) and $W_c > 4.5\text{m}$:
   $$E \leftarrow E \setminus \{e\} \quad (\text{Hairpin curve radius violation})$$

#### 3.2 Composite Edge Cost Function
To balance mileage, terrain hazard, and structural wear, edge weights are computed as:
$$\text{Weight}(e) = D_e + (35.0 \times G_e) + (20.0 \times \text{Bottlenecks}(e))$$

The shortest passable corridor is then computed via Dijkstra's algorithm:
$$\mathcal{P}^* = \operatorname{argmin}_{\mathcal{P}} \sum_{e \in \mathcal{P}} \text{Weight}(e)$$

---

### 4. Deterministic Multi-State RTO Compliance Engine

Whenever corridor $\mathcal{P}^*$ traverses a state $S \in \{\text{AP}, \text{TS}, \text{OD}, \text{WB}, \text{MH}, \text{CG}, \text{TN}, \text{KA}, \text{GJ}\}$:

#### 4.1 Central MoRTH Statutory Levy
$$\text{Fee}_{\text{MoRTH}} = \text{Base} + (\max(0, W_c - 49\text{MT}) \times 1.25 \times D_{\text{total}} \times 0.40)$$

#### 4.2 State Transit Levy
$$\text{Fee}_{S} = \text{Base}_S + \left(\max(0, W_c - 49\text{MT}) \times R_S \times \frac{D_{\text{total}}}{|S_{\text{traversed}}|} \times 0.30\right)$$
If $W_c > 3.8\text{m}$ or $H_c > 5.0\text{m}$, $\text{Fee}_S$ is scaled by dimension multiplier $M_S \in [1.10, 1.25]$.

#### 4.3 Escort & Convoy Rules
* **Police Highway Patrol**: Mandated under MV Act Section 112 if $W_c \ge 4.0\text{m}$, $L_c \ge 25\text{m}$, or $W_c \ge 90\text{MT}$.
* **Private Pilot Convoy**: 1 lead vehicle with revolving amber beacon + 1 trail safety vehicle with retro-reflective chevrons.
* **Night Curfew**: State highways in TS, WB, MH prohibit ODC movement between 20:00 and 06:00 hrs.

---

### 5. Algorithmic Risk Scoring (0 to 100)

$$\text{Risk Score} = 15 + \Delta_{\text{weight}} + \Delta_{\text{axle}} + \Delta_{\text{height}} + \Delta_{\text{width}} + \Delta_{\text{ghat}} + \Delta_{\text{detour}} + \Delta_{\text{curfew}}$$

* $\Delta_{\text{weight}}$: $+15$ if $W_c > 80\text{MT}$; $+25$ if $W_c > 120\text{MT}$.
* $\Delta_{\text{axle}}$: $+30$ if $L_a > 13.5\text{MT}$; $+10$ if $L_a > 11.5\text{MT}$.
* $\Delta_{\text{height}}$: $+12$ if $H_c > 4.75\text{m}$; $+20$ if $H_c > 5.20\text{m}$.
* $\Delta_{\text{width}}$: $+10$ if $W_c > 3.8\text{m}$; $+20$ if $W_c > 4.5\text{m}$.
* $\Delta_{\text{ghat}}$: $+12 \times \text{Ghat Count}$ (max $+25$).
* $\Delta_{\text{detour}}$: $+8 \times \text{Bypass Detours}$ (max $+20$).
* $\Delta_{\text{curfew}}$: $+8$ if 2 or more traversed states impose night travel curfews.

#### Governance Threshold:
* **Score $\le 70$**: `APPROVED_AUTO_PERMIT` $\implies$ Port clearance pass green-lit.
* **Score $> 70$**: `FLAGGED_FOR_DISPATCHER_SURVEY` $\implies$ Workflow suspends for engineering inspection and audited waiver in the React 19 Raw App.

