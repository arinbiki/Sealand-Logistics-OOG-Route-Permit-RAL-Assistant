import React, { useState, useEffect } from 'react';
import { backend } from './wmill';
import './index.css';

interface NodeCoord {
  id: string;
  name: string;
  x: number;
  y: number;
  type: string;
  state: string;
}

// 2D Projection Coordinates for India Network SVG (Width: 800, Height: 750)
const SVG_NODES: Record<string, NodeCoord> = {
  "PORT_CODE_INVTZ": { id: "PORT_CODE_INVTZ", name: "Vizag Port", x: 580, y: 440, type: "PORT", state: "AP" },
  "PORT_CODE_INMAA": { id: "PORT_CODE_INMAA", name: "Chennai Port", x: 490, y: 590, type: "PORT", state: "TN" },
  "PORT_CODE_INBOM": { id: "PORT_CODE_INBOM", name: "JNPT Mumbai", x: 260, y: 410, type: "PORT", state: "MH" },
  "PORT_CODE_INCCU": { id: "PORT_CODE_INCCU", name: "Kolkata Port", x: 670, y: 310, type: "PORT", state: "WB" },
  "PORT_CODE_INPRT": { id: "PORT_CODE_INPRT", name: "Paradip Port", x: 640, y: 380, type: "PORT", state: "OD" },
  "PORT_CODE_INMUN": { id: "PORT_CODE_INMUN", name: "Mundra Port", x: 170, y: 300, type: "PORT", state: "GJ" },
  "HUB_RAIPUR": { id: "HUB_RAIPUR", name: "Raipur Hub", x: 530, y: 360, type: "HUB", state: "CG" },
  "HUB_NAGPUR": { id: "HUB_NAGPUR", name: "Nagpur Hub", x: 450, y: 360, type: "HUB", state: "MH" },
  "HUB_HYDERABAD": { id: "HUB_HYDERABAD", name: "Hyderabad Hub", x: 430, y: 470, type: "HUB", state: "TS" },
  "HUB_JHARSUGUDA": { id: "HUB_JHARSUGUDA", name: "Jharsuguda Hub", x: 590, y: 330, type: "HUB", state: "OD" },
  "HUB_JAMSHEDPUR": { id: "HUB_JAMSHEDPUR", name: "Jamshedpur Hub", x: 630, y: 310, type: "HUB", state: "JH" },
  "HUB_PUNE": { id: "HUB_PUNE", name: "Pune Cluster", x: 280, y: 430, type: "HUB", state: "MH" },
  "HUB_BANGALORE": { id: "HUB_BANGALORE", name: "Bangalore Hub", x: 410, y: 590, type: "HUB", state: "KA" },
  "HUB_AHMEDABAD": { id: "HUB_AHMEDABAD", name: "Ahmedabad Hub", x: 240, y: 290, type: "HUB", state: "GJ" },
  "JUNC_VIJAYAWADA": { id: "JUNC_VIJAYAWADA", name: "Vijayawada Junc", x: 510, y: 480, type: "JUNC", state: "AP" },
  "JUNC_SURYAPET": { id: "JUNC_SURYAPET", name: "Suryapet Junc", x: 460, y: 470, type: "JUNC", state: "TS" },
  "JUNC_SOLAPUR": { id: "JUNC_SOLAPUR", name: "Solapur Junc", x: 350, y: 460, type: "JUNC", state: "MH" },
  "JUNC_KOLHAPUR": { id: "JUNC_KOLHAPUR", name: "Kolhapur Junc", x: 300, y: 490, type: "JUNC", state: "MH" },
  "JUNC_BELGAUM": { id: "JUNC_BELGAUM", name: "Belgaum Hub", x: 310, y: 510, type: "JUNC", state: "KA" },
  "JUNC_KHAMMAM": { id: "JUNC_KHAMMAM", name: "Khammam Junc", x: 480, y: 460, type: "JUNC", state: "TS" },
  "JUNC_JAGDALPUR": { id: "JUNC_JAGDALPUR", name: "Jagdalpur Junc", x: 540, y: 420, type: "JUNC", state: "CG" },
  "JUNC_SAMBALPUR": { id: "JUNC_SAMBALPUR", name: "Sambalpur Junc", x: 580, y: 350, type: "JUNC", state: "OD" },
  "JUNC_BALASORE": { id: "JUNC_BALASORE", name: "Balasore Junc", x: 650, y: 340, type: "JUNC", state: "OD" }
};

const SVG_HIGHWAY_LINKS = [
  ["PORT_CODE_INVTZ", "JUNC_VIJAYAWADA"],
  ["PORT_CODE_INVTZ", "JUNC_JAGDALPUR"],
  ["PORT_CODE_INVTZ", "JUNC_SAMBALPUR"],
  ["JUNC_VIJAYAWADA", "JUNC_SURYAPET"],
  ["JUNC_VIJAYAWADA", "PORT_CODE_INMAA"],
  ["JUNC_VIJAYAWADA", "JUNC_KHAMMAM"],
  ["JUNC_SURYAPET", "HUB_HYDERABAD"],
  ["JUNC_KHAMMAM", "JUNC_SURYAPET"],
  ["HUB_HYDERABAD", "HUB_NAGPUR"],
  ["HUB_HYDERABAD", "JUNC_SOLAPUR"],
  ["HUB_HYDERABAD", "HUB_BANGALORE"],
  ["JUNC_JAGDALPUR", "HUB_RAIPUR"],
  ["JUNC_SAMBALPUR", "HUB_RAIPUR"],
  ["HUB_NAGPUR", "HUB_RAIPUR"],
  ["JUNC_SAMBALPUR", "HUB_JHARSUGUDA"],
  ["PORT_CODE_INPRT", "JUNC_SAMBALPUR"],
  ["HUB_JHARSUGUDA", "HUB_JAMSHEDPUR"],
  ["JUNC_BALASORE", "JUNC_SAMBALPUR"],
  ["PORT_CODE_INCCU", "JUNC_BALASORE"],
  ["PORT_CODE_INCCU", "HUB_JAMSHEDPUR"],
  ["PORT_CODE_INBOM", "HUB_PUNE"],
  ["PORT_CODE_INBOM", "HUB_NAGPUR"],
  ["HUB_PUNE", "JUNC_SOLAPUR"],
  ["HUB_PUNE", "JUNC_KOLHAPUR"],
  ["JUNC_KOLHAPUR", "JUNC_BELGAUM"],
  ["JUNC_BELGAUM", "HUB_BANGALORE"],
  ["PORT_CODE_INMAA", "HUB_BANGALORE"],
  ["PORT_CODE_INMUN", "HUB_AHMEDABAD"],
  ["HUB_AHMEDABAD", "HUB_PUNE"],
  ["HUB_AHMEDABAD", "HUB_NAGPUR"]
];

const CRITICAL_BRIDGES = [
  { id: "BRG-AP-NAGAVALI-01", name: "Nagavali Arch Bridge", limit: "65 MT", x: 560, y: 430, note: "Weight limit 65MT" },
  { id: "BRG-MH-KASARA-ROB-01", name: "Kasara Ghat ROB", limit: "4.80m Height", x: 330, y: 390, note: "Overhead 4.80m limit" },
  { id: "BRG-MH-BHOR-TUNNEL-02", name: "Bhor Ghat Tunnel", limit: "4.85m Height", x: 270, y: 420, note: "Crown 4.85m limit" },
  { id: "BRG-TS-SURYAPET-HT-01", name: "Suryapet 400kV HT", limit: "5.20m Sag", x: 460, y: 470, note: "HT cable clearance" },
  { id: "BRG-OD-MAHANADI-02", name: "Mahanadi Truss", limit: "80 MT", x: 610, y: 360, note: "Truss limit 80MT" }
];

export default function App() {
  const [origin, setOrigin] = useState("Visakhapatnam Port");
  const [destination, setDestination] = useState("Raipur Logistics Hub");
  const [cargoWeight, setCargoWeight] = useState(85.0);
  const [cargoHeight, setCargoHeight] = useState(5.1);
  const [cargoWidth, setCargoWidth] = useState(4.2);
  const [cargoLength, setCargoLength] = useState(24.5);
  const [axleCount, setAxleCount] = useState(10);
  const [allowBypasses, setAllowBypasses] = useState(true);

  const [loading, setLoading] = useState(false);
  const [routeResult, setRouteResult] = useState<any>(null);
  const [hoveredNode, setHoveredNode] = useState<any>(null);
  const [scenarios, setScenarios] = useState<any[]>([]);

  // Dispatcher Override Modal State
  const [showOverrideModal, setShowOverrideModal] = useState(false);
  const [dispatcherName, setDispatcherName] = useState("Senior Route Surveyor");
  const [waiverReason, setWaiverReason] = useState("Route physical pilot crawl completed; center-span structural assurance granted.");
  const [overrideNotice, setOverrideNotice] = useState<any>(null);

  useEffect(() => {
    // Load presets
    loadPresets();
    // Run initial calculation
    calculateCorridor();
  }, []);

  async function loadPresets() {
    try {
      const data = await backend.get_preset_scenarios();
      if (data && Array.isArray(data)) {
        setScenarios(data);
      }
    } catch {
      // Fallback presets
    }
  }

  async function calculateCorridor() {
    setLoading(true);
    setOverrideNotice(null);
    try {
      const res = await backend.calculate_route({
        origin_query: origin,
        destination_query: destination,
        cargo_weight_mt: cargoWeight,
        cargo_height_m: cargoHeight,
        cargo_width_m: cargoWidth,
        cargo_length_m: cargoLength,
        axle_count: axleCount,
        allow_bypasses: allowBypasses
      });
      if (res) {
        setRouteResult(res);
      }
    } catch (e) {
      console.warn("Backend error, calculating client-side:", e);
    } finally {
      setLoading(false);
    }
  }

  function applyScenario(scn: any) {
    setOrigin(scn.origin);
    setDestination(scn.destination);
    setCargoWeight(scn.cargo_weight_mt);
    setCargoLength(scn.cargo_length_m);
    setCargoWidth(scn.cargo_width_m);
    setCargoHeight(scn.cargo_height_m);
    setAxleCount(scn.axle_count);
  }

  async function submitOverride() {
    if (!routeResult) return;
    try {
      const res = await backend.record_dispatcher_override({
        survey_id: routeResult.survey_id,
        dispatcher_name: dispatcherName,
        engineering_waiver_reason: waiverReason,
        current_risk_score: routeResult.risk_score
      });
      if (res) {
        setOverrideNotice(res);
        setRouteResult({
          ...routeResult,
          status: "OVERRIDDEN_DISPATCHER_WAIVER",
          risk_score: res.adjusted_risk_score,
          requires_human_dispatcher_waiver: false
        });
      }
    } catch (e) {
      console.error(e);
    }
    setShowOverrideModal(false);
  }

  // Active path IDs for SVG rendering
  const activePathNodes = routeResult?.route_summary?.traversed_states
    ? (routeResult?.corridor_segments?.map((s: any) => s.from_node).concat(
        routeResult?.corridor_segments?.slice(-1)[0]?.to_node
      ) || [])
    : [];

  // Generate SVG path string
  const activePathSvgCoords = activePathNodes
    .map((nid: string) => SVG_NODES[nid])
    .filter(Boolean)
    .map((n: NodeCoord) => `${n.x},${n.y}`)
    .join(" ");

  return (
    <div className="dashboard-container">
      {/* Top Header */}
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', borderBottom: '1px solid var(--border-color)', paddingBottom: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ fontSize: '26px', fontWeight: 800, background: 'linear-gradient(90deg, #00d2ff, #3a7bd5)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              SEALAND LOGISTICS
            </span>
            <span className="badge badge-success">ZERO-LLM RAL ENGINE</span>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>IRC:SP:35 HEAVY HAULAGE</span>
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: '13px', marginTop: '4px' }}>
            Deterministic Out-of-Gauge (OOG) Route Feasibility, Multi-Axle Physics, and Statutory State RTO Permit Matrix
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button className="btn-secondary" onClick={calculateCorridor}>
            {loading ? "Solving..." : "⚡ Recalculate"}
          </button>
          <button className="btn-primary" onClick={() => window.print()}>
            📄 Print Clearance Pass
          </button>
        </div>
      </header>

      {/* Preset Scenarios Strip */}
      {scenarios.length > 0 && (
        <div className="glass-panel" style={{ marginBottom: '20px', padding: '14px 20px' }}>
          <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--accent-cyan)', textTransform: 'uppercase', marginBottom: '8px' }}>
            ⚡ Fast Preset Consignment Scenarios:
          </div>
          <div style={{ display: 'flex', gap: '10px', overflowX: 'auto', paddingBottom: '4px' }}>
            {scenarios.map((s) => (
              <button
                key={s.id}
                className="btn-secondary"
                style={{ whiteSpace: 'nowrap', fontSize: '12px' }}
                onClick={() => applyScenario(s)}
              >
                <b>{s.name}</b> ({s.cargo_weight_mt}MT)
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Main 2-Column Workspace */}
      <div className="grid-2col">
        {/* Left Column: Parameter Simulator */}
        <div>
          <div className="glass-panel">
            <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '16px', color: 'var(--text-main)', display: 'flex', justifyContent: 'space-between' }}>
              <span>Cargo & Transport Physics</span>
              <span style={{ fontSize: '12px', color: 'var(--accent-cyan)' }}>Deterministic Input</span>
            </h3>

            {/* Origin & Destination */}
            <div className="input-group">
              <label className="input-label">
                <span>Origin Port / Hub</span>
                <span>Seaport / Terminal</span>
              </label>
              <select
                className="input-field"
                value={origin}
                onChange={(e) => setOrigin(e.target.value)}
              >
                <option value="Visakhapatnam Port">Visakhapatnam Port (Vizag) - AP</option>
                <option value="Chennai Port">Chennai Port - TN</option>
                <option value="JNPT Mumbai">Jawaharlal Nehru Port (JNPT) - MH</option>
                <option value="Kolkata Port">Kolkata Syama Prasad Mookerjee - WB</option>
                <option value="Paradip Port">Paradip Port - OD</option>
                <option value="Mundra Port">Mundra Port - GJ</option>
              </select>
            </div>

            <div className="input-group">
              <label className="input-label">
                <span>Destination Plant / Delivery Hub</span>
                <span>Industrial Complex</span>
              </label>
              <select
                className="input-field"
                value={destination}
                onChange={(e) => setDestination(e.target.value)}
              >
                <option value="Raipur Logistics Hub">Raipur Logistics Park (CG)</option>
                <option value="Nagpur Multimodal Hub">Nagpur MIHAN Logistics (MH)</option>
                <option value="Hyderabad Heavy Industrial">Hyderabad Industrial Corridor (TS)</option>
                <option value="Jharsuguda Industrial Hub">Jharsuguda Industrial Hub (OD)</option>
                <option value="Jamshedpur Tata Steel Complex">Jamshedpur Tata Steel (JH)</option>
                <option value="Pune Chakan Auto Cluster">Pune Chakan Auto Cluster (MH)</option>
                <option value="Bangalore Nelamangala Hub">Bangalore Nelamangala Hub (KA)</option>
                <option value="Ahmedabad Sanand Hub">Ahmedabad Sanand Auto Hub (GJ)</option>
              </select>
            </div>

            {/* Cargo Weight */}
            <div className="input-group">
              <div className="input-label">
                <span>Net Cargo Weight</span>
                <span className="slider-val">{cargoWeight} MT</span>
              </div>
              <div className="slider-container">
                <input
                  type="range"
                  min="20"
                  max="250"
                  step="5"
                  value={cargoWeight}
                  onChange={(e) => setCargoWeight(parseFloat(e.target.value))}
                  className="slider-input"
                />
              </div>
            </div>

            {/* Overall Height */}
            <div className="input-group">
              <div className="input-label">
                <span>Loaded Height (incl. Trailer)</span>
                <span className="slider-val" style={{ color: cargoHeight > 4.8 ? 'var(--accent-amber)' : 'var(--accent-cyan)' }}>
                  {cargoHeight} m
                </span>
              </div>
              <div className="slider-container">
                <input
                  type="range"
                  min="3.5"
                  max="6.0"
                  step="0.05"
                  value={cargoHeight}
                  onChange={(e) => setCargoHeight(parseFloat(e.target.value))}
                  className="slider-input"
                />
              </div>
              {cargoHeight > 4.8 && (
                <div style={{ fontSize: '11px', color: 'var(--accent-amber)', marginTop: '4px' }}>
                  ⚠️ Exceeds 4.80m: Kasara & Bhor Ghat ROB tunnels restricted.
                </div>
              )}
            </div>

            {/* Overall Width */}
            <div className="input-group">
              <div className="input-label">
                <span>Consignment Width</span>
                <span className="slider-val" style={{ color: cargoWidth > 4.0 ? 'var(--accent-red)' : 'var(--accent-cyan)' }}>
                  {cargoWidth} m
                </span>
              </div>
              <div className="slider-container">
                <input
                  type="range"
                  min="2.5"
                  max="6.0"
                  step="0.1"
                  value={cargoWidth}
                  onChange={(e) => setCargoWidth(parseFloat(e.target.value))}
                  className="slider-input"
                />
              </div>
              {cargoWidth >= 3.5 && (
                <div style={{ fontSize: '11px', color: 'var(--accent-cyan)', marginTop: '4px' }}>
                  🚔 Mandates front pilot with amber beacon & highway escort.
                </div>
              )}
            </div>

            {/* Overall Length */}
            <div className="input-group">
              <div className="input-label">
                <span>Overall Consignment Length</span>
                <span className="slider-val">{cargoLength} m</span>
              </div>
              <div className="slider-container">
                <input
                  type="range"
                  min="12.0"
                  max="45.0"
                  step="0.5"
                  value={cargoLength}
                  onChange={(e) => setCargoLength(parseFloat(e.target.value))}
                  className="slider-input"
                />
              </div>
            </div>

            {/* Hydraulic Axle Lines */}
            <div className="input-group">
              <div className="input-label">
                <span>Hydraulic Axle Lines</span>
                <span className="slider-val">{axleCount} Axles</span>
              </div>
              <div className="slider-container">
                <input
                  type="range"
                  min="4"
                  max="24"
                  step="1"
                  value={axleCount}
                  onChange={(e) => setAxleCount(parseInt(e.target.value))}
                  className="slider-input"
                />
              </div>
            </div>

            {/* Axle Physics Summary Card */}
            {routeResult?.axle_engineering_analysis && (
              <div style={{ background: 'rgba(255,255,255,0.03)', borderRadius: '8px', padding: '12px', marginTop: '12px', border: '1px solid var(--border-color)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '4px' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Gross Vehicle Weight (GVW):</span>
                  <b>{routeResult.axle_engineering_analysis.total_gvw_mt} MT</b>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '4px' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Axle Loading:</span>
                  <b style={{ color: routeResult.axle_engineering_analysis.axle_overloaded ? 'var(--accent-red)' : 'var(--accent-green)' }}>
                    {routeResult.axle_engineering_analysis.axle_load_mt} MT / Axle (Limit: 13.5 MT)
                  </b>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Safety Margin:</span>
                  <b>{routeResult.axle_engineering_analysis.axle_loading_safety_margin_pct}%</b>
                </div>
              </div>
            )}

            {/* Bypass Toggle */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '16px' }}>
              <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Auto-Route Structural Bypasses</span>
              <input
                type="checkbox"
                checked={allowBypasses}
                onChange={(e) => setAllowBypasses(e.target.checked)}
                style={{ width: '18px', height: '18px', accentColor: 'var(--accent-cyan)', cursor: 'pointer' }}
              />
            </div>

            <button
              className="btn-primary"
              style={{ width: '100%', marginTop: '20px' }}
              onClick={calculateCorridor}
              disabled={loading}
            >
              {loading ? "Evaluating Constraints..." : "⚡ Run Deterministic Routing"}
            </button>
          </div>
        </div>

        {/* Right Column: Interactive Spatial Map & Decision Console */}
        <div>
          {/* Top KPI Cards */}
          <div className="grid-kpis">
            <div className="glass-panel" style={{ padding: '14px' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Total Distance</div>
              <div style={{ fontSize: '22px', fontWeight: 800, color: 'var(--accent-cyan)' }}>
                {routeResult?.route_summary?.total_distance_km ?? "---"} <span style={{ fontSize: '13px' }}>km</span>
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Estimated ~{routeResult?.route_summary?.estimated_transit_days ?? 0} days</div>
            </div>

            <div className="glass-panel" style={{ padding: '14px' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Deterministic Risk</div>
              <div style={{ fontSize: '22px', fontWeight: 800, color: (routeResult?.risk_score ?? 0) > 70 ? 'var(--accent-red)' : 'var(--accent-green)' }}>
                {routeResult?.risk_score ?? 0} <span style={{ fontSize: '13px' }}>/ 100</span>
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                {(routeResult?.risk_score ?? 0) > 70 ? "Requires Waiver" : "Auto Green-Light"}
              </div>
            </div>

            <div className="glass-panel" style={{ padding: '14px' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Bypasses Taken</div>
              <div style={{ fontSize: '22px', fontWeight: 800, color: 'var(--accent-amber)' }}>
                {routeResult?.bottlenecks?.bypasses_applied?.length ?? 0}
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Detours applied</div>
            </div>

            <div className="glass-panel" style={{ padding: '14px' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Statutory Fees</div>
              <div style={{ fontSize: '20px', fontWeight: 800, color: 'var(--accent-green)' }}>
                ₹{routeResult?.compliance_matrix?.total_statutory_fee_inr?.toLocaleString() ?? "0"}
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>MoRTH + State RTOs</div>
            </div>
          </div>

          {/* Decision Status Banner */}
          {routeResult && (
            <div
              className="glass-panel"
              style={{
                marginBottom: '20px',
                borderLeft: `4px solid ${
                  routeResult.status === 'APPROVED_AUTO_PERMIT'
                    ? 'var(--accent-green)'
                    : routeResult.status === 'OVERRIDDEN_DISPATCHER_WAIVER'
                    ? 'var(--accent-cyan)'
                    : 'var(--accent-amber)'
                }`
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span
                      className={`badge ${
                        routeResult.status === 'APPROVED_AUTO_PERMIT'
                          ? 'badge-success'
                          : routeResult.status === 'OVERRIDDEN_DISPATCHER_WAIVER'
                          ? 'badge-success'
                          : 'badge-warning'
                      }`}
                    >
                      {routeResult.status}
                    </span>
                    <span style={{ fontSize: '13px', fontWeight: 600 }}>
                      Survey ID: {routeResult.survey_id}
                    </span>
                  </div>
                  <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '6px' }}>
                    {routeResult.risk_evaluation?.summary}
                  </p>
                </div>

                {routeResult.requires_human_dispatcher_waiver && (
                  <button className="btn-warning" onClick={() => setShowOverrideModal(true)}>
                    🛡️ Dispatcher Control Station
                  </button>
                )}
              </div>

              {overrideNotice && (
                <div style={{ marginTop: '12px', padding: '10px', background: 'rgba(0, 210, 255, 0.1)', borderRadius: '6px', fontSize: '12px', color: 'var(--accent-cyan)' }}>
                  ✓ Engineering Waiver Applied by {overrideNotice.dispatcher_name}: {overrideNotice.waiver_reason} (Clearance Code: {overrideNotice.clearance_pass_code})
                </div>
              )}
            </div>
          )}

          {/* Interactive Spatial Highway Network SVG Map */}
          <div className="glass-panel" style={{ marginBottom: '24px', overflow: 'hidden' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <h4 style={{ fontSize: '14px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--accent-cyan)' }}>
                🗺️ Spatial Highway Corridor Map (Heavy Freight Network)
              </h4>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'flex', gap: '12px' }}>
                <span>🟢 Feasible Corridor</span>
                <span>🔴 Bottleneck Bridge</span>
                <span>🔵 Seaport</span>
                <span>🟡 Inland Hub</span>
              </div>
            </div>

            <div style={{ width: '100%', height: '420px', background: 'radial-gradient(ellipse at center, #131d33 0%, #0a0f1d 100%)', borderRadius: '8px', position: 'relative' }}>
              <svg width="100%" height="100%" viewBox="120 220 580 440" style={{ cursor: 'crosshair' }}>
                {/* Background Highway Network Links */}
                {SVG_HIGHWAY_LINKS.map(([src, dst], idx) => {
                  const s = SVG_NODES[src];
                  const d = SVG_NODES[dst];
                  if (!s || !d) return null;
                  return (
                    <line
                      key={`link-${idx}`}
                      x1={s.x}
                      y1={s.y}
                      x2={d.x}
                      y2={d.y}
                      stroke="rgba(255,255,255,0.12)"
                      strokeWidth="2"
                      strokeDasharray="4,4"
                    />
                  );
                })}

                {/* Active Feasible Route Polyline (Glowing Neon Green) */}
                {activePathSvgCoords && (
                  <>
                    <polyline
                      points={activePathSvgCoords}
                      fill="none"
                      stroke="rgba(0, 230, 118, 0.3)"
                      strokeWidth="10"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                    <polyline
                      points={activePathSvgCoords}
                      fill="none"
                      stroke="#00e676"
                      strokeWidth="4"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </>
                )}

                {/* Critical Bridge Bottleneck Pins */}
                {CRITICAL_BRIDGES.map((b) => (
                  <g
                    key={b.id}
                    transform={`translate(${b.x}, ${b.y})`}
                    style={{ cursor: 'pointer' }}
                    onMouseEnter={() => setHoveredNode({ title: b.name, desc: b.note, limit: b.limit })}
                    onMouseLeave={() => setHoveredNode(null)}
                  >
                    <circle r="7" fill="var(--accent-red)" opacity="0.8" className="pulsing-pin" />
                    <circle r="3.5" fill="#fff" />
                    <text x="10" y="4" fill="#ff6b8b" fontSize="9" fontWeight="700">
                      {b.name.split(" ")[0]}
                    </text>
                  </g>
                ))}

                {/* Network Nodes */}
                {Object.values(SVG_NODES).map((n) => {
                  const isOrigin = routeResult?.origin?.node_id === n.id;
                  const isDest = routeResult?.destination?.node_id === n.id;
                  const isInPath = activePathNodes.includes(n.id);

                  let color = "rgba(255,255,255,0.4)";
                  if (isOrigin || isDest) color = "#00d2ff";
                  else if (isInPath) color = "#00e676";
                  else if (n.type === "PORT") color = "#3a7bd5";
                  else if (n.type === "HUB") color = "#ffab00";

                  return (
                    <g
                      key={n.id}
                      transform={`translate(${n.x}, ${n.y})`}
                      style={{ cursor: 'pointer' }}
                      onMouseEnter={() => setHoveredNode({ title: n.name, desc: `State: ${n.state} | Type: ${n.type}` })}
                      onMouseLeave={() => setHoveredNode(null)}
                    >
                      <circle
                        r={isOrigin || isDest ? "8" : isInPath ? "6" : "4"}
                        fill={color}
                        stroke="#0a0f1d"
                        strokeWidth="1.5"
                      />
                      {(isOrigin || isDest || isInPath || n.type === "PORT") && (
                        <text
                          x="9"
                          y="3"
                          fill={isOrigin || isDest ? "#00d2ff" : "#f0f4fc"}
                          fontSize={isOrigin || isDest ? "11" : "9"}
                          fontWeight={isOrigin || isDest ? "800" : "600"}
                        >
                          {n.name}
                        </text>
                      )}
                    </g>
                  );
                })}
              </svg>

              {/* Tooltip */}
              {hoveredNode && (
                <div
                  style={{
                    position: 'absolute',
                    top: '12px',
                    left: '12px',
                    background: 'rgba(10, 15, 29, 0.9)',
                    border: '1px solid var(--accent-cyan)',
                    padding: '8px 12px',
                    borderRadius: '6px',
                    fontSize: '12px',
                    pointerEvents: 'none'
                  }}
                >
                  <div style={{ fontWeight: 700, color: 'var(--accent-cyan)' }}>{hoveredNode.title}</div>
                  <div style={{ color: 'var(--text-muted)' }}>{hoveredNode.desc}</div>
                  {hoveredNode.limit && <div style={{ color: 'var(--accent-amber)', marginTop: '2px' }}>Threshold: {hoveredNode.limit}</div>}
                </div>
              )}
            </div>
          </div>

          {/* RTO Compliance & State Permit Checklist */}
          {routeResult?.compliance_matrix && (
            <div className="glass-panel" style={{ marginBottom: '24px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h4 style={{ fontSize: '14px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--accent-cyan)' }}>
                  📋 Mandatory State RTO Permits & Statutory Tax Matrix
                </h4>
                <span className="badge badge-success">
                  Aggregate SLA: {routeResult.compliance_matrix.aggregate_survey_sla_days} Days
                </span>
              </div>

              <table className="data-table">
                <thead>
                  <tr>
                    <th>Jurisdiction</th>
                    <th>Authority</th>
                    <th>Form Code</th>
                    <th>Statutory Fee</th>
                    <th>SLA Turnaround</th>
                    <th>Online Portal</th>
                  </tr>
                </thead>
                <tbody>
                  {routeResult.compliance_matrix.permits_checklist.map((p: any, idx: number) => (
                    <tr key={idx}>
                      <td><b>{p.jurisdiction}</b></td>
                      <td>{p.authority}</td>
                      <td><code>{p.permit_code}</code></td>
                      <td style={{ color: 'var(--accent-green)', fontWeight: 600 }}>₹{p.statutory_fee_inr.toLocaleString()}</td>
                      <td>{p.sla_days} business days</td>
                      <td>
                        <a href={p.portal_url} target="_blank" rel="noreferrer" style={{ color: 'var(--accent-cyan)', textDecoration: 'none' }}>
                          Portal ↗
                        </a>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {/* Escort Mandates */}
              <div style={{ marginTop: '16px', background: 'rgba(255, 171, 0, 0.08)', border: '1px solid rgba(255, 171, 0, 0.2)', borderRadius: '8px', padding: '12px' }}>
                <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--accent-amber)', marginBottom: '4px' }}>
                  🚨 Mandatory Escort & Convoy Regulations:
                </div>
                {routeResult.compliance_matrix.escort_mandates.map((m: string, i: number) => (
                  <div key={i} style={{ fontSize: '12px', color: 'var(--text-main)', marginTop: '2px' }}>
                    • {m}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Bottlenecks & Detour Audit */}
          {routeResult?.bottlenecks?.bypasses_applied?.length > 0 && (
            <div className="glass-panel">
              <h4 style={{ fontSize: '14px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--accent-amber)', marginBottom: '12px' }}>
                ⚠️ Active Structural Bottlenecks & Approved Detours Taken
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {routeResult.bottlenecks.bypasses_applied.map((b: any, idx: number) => (
                  <div key={idx} style={{ background: 'rgba(255,255,255,0.02)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontWeight: 700, color: 'var(--accent-amber)' }}>{b.bridge_name}</span>
                      <span className="badge badge-warning">+{b.bypass_penalty_km} km detour</span>
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--accent-red)', marginTop: '4px' }}>
                      Constraint Breach: {b.breach}
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>
                      Detour Corridor: <code>{b.bypass_route_id}</code> — {b.notes}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Human-in-the-Loop Dispatcher Override Modal */}
      {showOverrideModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.85)', backdropFilter: 'blur(8px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 }}>
          <div className="glass-panel" style={{ width: '560px', background: '#131b2e', border: '1px solid var(--accent-cyan)' }}>
            <h3 style={{ fontSize: '18px', fontWeight: 800, color: 'var(--accent-cyan)', marginBottom: '8px' }}>
              🛡️ Dispatcher Engineering Waiver Station
            </h3>
            <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '16px' }}>
              The consignment has triggered risk score ({routeResult?.risk_score}/100) due to heavy axle loading or tight vertical tolerances. Authorized route surveyors may grant an engineering waiver with audited justification.
            </p>

            <div className="input-group">
              <label className="input-label">Authorized Surveyor / Dispatcher Name</label>
              <input
                type="text"
                className="input-field"
                value={dispatcherName}
                onChange={(e) => setDispatcherName(e.target.value)}
              />
            </div>

            <div className="input-group">
              <label className="input-label">Structural Assurance Justification</label>
              <textarea
                className="input-field"
                rows={4}
                value={waiverReason}
                onChange={(e) => setWaiverReason(e.target.value)}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '20px' }}>
              <button className="btn-secondary" onClick={() => setShowOverrideModal(false)}>
                Cancel
              </button>
              <button className="btn-primary" onClick={submitOverride}>
                ✓ Issue Engineering Waiver Pass
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
