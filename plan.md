This plan replaces the probabilistic nature of an LLM-based RAG with a **Deterministic Constraint Solver** and a **Graph-Based Retrieval Engine**. In this architecture, "Retrieval-Augmented Generation" becomes **Retrieval-Augmented Logic (RAL)**, where the output is a mathematically verified route and permit set rather than a predicted string of text.

---

### System Design: OOG Route & Permit "Deterministic Expert"

#### 1. The Data Layer (PostgreSQL + PostGIS)
Instead of a Vector DB (which requires an LLM to interpret), we use a **Relational Spatial Graph**.
*   **`bridge_constraints` Table:** Stores `bridge_id`, `lat/long`, `max_weight_mt`, `min_vertical_clearance_m`, and `road_segment_id`.
*   **`rto_rules` Table:** Stores `state_code`, `cargo_category` (ODC/OOG), `permit_type_required`, and `tax_formula` (as a JSONB object).
*   **`route_graph` (PostGIS):** A weighted graph of the National Highway (NH) network where "weight" is a composite of distance and constraint severity.

#### 2. The Sensor & Trigger Layer (n8n)
*   **Trigger:** Webhook from the company’s ERP/CRM or an IMAP trigger for "Route Survey Request" emails.
*   **Heuristic Classifier (n8n Code Node):** A JavaScript/Python script using `Regex` and `String Distance (Levenshtein)` to extract:
    *   **Origin/Destination:** Maps "Vizag" to `PORT_CODE_INVTZ`.
    *   **Specs:** Extracts `Weight`, `Length`, `Width`, `Height` from unstructured email bodies.
*   **Routing Logic:** If `Weight > 100MT`, route to the "Heavy Lift Sub-Workflow"; if `Width > 4m`, route to the "Wide Load Sub-Workflow."

#### 3. The Deterministic Planner (Windmill Flows - DAG)
The Flow is a sequence of atomic steps that solve the "Route Puzzle."

*   **Step 1: Graph Pruning (Python + NetworkX):** 
    *   *Logic:* Takes the destination and origin. Runs a Breadth-First Search (BFS) on the `route_graph`.
    *   *Constraint Filter:* Eliminates any bridge or tunnel where `Cargo_Height > Bridge_Clearance` or `Cargo_Weight > Bridge_Limit`.
*   **Step 2: Permit Rule Engine (Python):**
    *   *Logic:* A deterministic lookup against the `rto_rules` table. It iterates through every state the pruned route passes through and builds a "Mandatory Permit Set."
*   **Step 3: Risk Scoring (Algorithmic):**
    *   *Logic:* Calculates a score based on: 
        1. Total number of "Bottlenecks" (bridges within 5% of the cargo limit).
        2. Estimated "Escort Requirements" (if width > 3.5m).
        3. Seasonal factors (e.g., North-East India monsoon roadblocks).
*   **Step 4: Human Verification (Suspend Step):** 
    *   If `Risk_Score > 70`, the Flow suspends. This replaces the LLM's "confidence check."

#### 4. The Heuristic "Brain" (Windmill Scripts)
*   **The "Route Generator" Script:** Uses `NetworkX` to find the path of "Least Resistance." If the shortest path is blocked by a 40MT bridge and the cargo is 55MT, it deterministically calculates the nearest alternate highway that supports 60MT+.
*   **The "Compliance Validator":** A Pydantic-validated script that checks if the extracted cargo dimensions are physically possible for the selected route.

#### 5. The User Interface (Windmill Apps)
*   **Route Survey Dashboard:** A UI showing a map (via Mapbox/Leaflet) with the "Green Route" (Safe) and "Red Nodes" (Bottlenecks).
*   **Permit Matrix:** A grid showing which state requires which form.
*   **Manual Override:** A dispatcher can toggle a "Force Bridge" switch if they have local knowledge the graph lacks, which triggers an "Audit Log" entry in Postgres.

---

### End-to-End Implementation Guide

#### Phase 1: Data Engineering & Ingestion
1.  **Schema Setup:** Create the PostGIS-enabled PostgreSQL database. 
2.  **Ingestion Pipeline:** Build a Windmill Flow that runs nightly to scrape (via `BeautifulSoup`) or import (via `Pandas`) updated bridge data and RTO notifications.
3.  **Fuzzy Matching Setup:** Enable `pg_trgm` extension in Postgres. This allows the system to find "Visakhapatnam" even if the user types "Vishakapatnam" without an LLM.

#### Phase 2: Building the Logic Engine
1.  **Script Development:** Write the Python "Graph Pruning" script. 
    *   *Logic:* Input: `{origin: 'A', dest: 'B', weight: 55}`. 
    *   *Process:* `graph = nx.from_sql_db(...)`, `filtered_graph = prune_edges(graph, weight)`.
    *   *Output:* `[list_of_viable_path_ids]`.
2.  **DAG Construction:** In Windmill, link the "Prune" script to the "Permit Lookup" script. Ensure the output of one is the strictly-typed input of the next.

#### Phase 3: n8n & MCP Integration
1.  **The Contract:** Define the JSON Schema for the request. n8n must send exactly `{ "cargo_specs": {}, "geo": {} }`.
2.  **MCP Server Setup:** Configure the n8n MCP server to expose a "Route_Check" tool. 
3.  **Execution:** Windmill (as the brain) calls the n8n MCP server at the end of the flow to trigger the "Send Email to Client" workflow.

#### Phase 4: Production Deployment (Enterprise Level)
1.  **Workflows as Code (WAC):** Use the Windmill CLI to export all Flows and Scripts into a Git repository. This allows for Peer Review and Rollbacks.
2.  **Resource Management:** Use Windmill "Resources" for DB connection strings. Never hardcode credentials.
3.  **Error Handling:** Implement "Retry Policies" in Windmill for network calls to the Map API. If it fails 3 times, trigger a "Slack Alert" sub-workflow via n8n.
4.  **Observability:** Set up a "Job Logs" retention policy. Every route calculation must be reproducible by looking at the logs (Deterministic Audit Trail).

#### Phase 5: Testing Strategy
1.  **Unit Testing:** Test the "Bridge Pruning" logic with synthetic data (e.g., a 100MT cargo on a 50MT bridge must return "No Path Found").
2.  **Integration Testing:** Run the n8n Webhook $\rightarrow$ Windmill Flow $\rightarrow$ Postgres $\rightarrow$ n8n Email loop end-to-end.
3.  **User Acceptance Testing (UAT):** Have a Senior Logistics Manager compare the system's output against 10 historical manual route surveys to verify accuracy.

### Why this is "Enterprise Grade"
*   **Zero Hallucination:** The system cannot invent a permit or a bridge limit. It only reports what is in the database.
*   **Auditability:** Every decision is logged with a timestamp and the specific version of the "Rule Script" used.
*   **Speed:** A deterministic DAG executes in milliseconds compared to the seconds of latency in a multi-step LLM agent.
*   **Security:** No sensitive client data is ever sent to a third-party AI provider.