-- ==============================================================================
-- Sealand Logistics: OOG Route & Permit RAG Assistant (Deterministic Expert)
-- PostgreSQL + PostGIS / Spatial Graph Relational Schema & Seed Data
-- ==============================================================================

CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;

-- Drop existing tables if re-initializing
DROP TABLE IF EXISTS oog_audit_logs CASCADE;
DROP TABLE IF EXISTS oog_survey_overrides CASCADE;
DROP TABLE IF EXISTS oog_survey_jobs CASCADE;
DROP TABLE IF EXISTS bridge_constraints CASCADE;
DROP TABLE IF EXISTS oog_road_segments CASCADE;
DROP TABLE IF EXISTS rto_rules CASCADE;
DROP TABLE IF EXISTS oog_nodes CASCADE;

-- ------------------------------------------------------------------------------
-- 1. Nodes: Ports, Industrial Hubs, Border Checkposts, Highway Junctions
-- ------------------------------------------------------------------------------
CREATE TABLE oog_nodes (
    node_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    aliases TEXT[] NOT NULL DEFAULT '{}',
    state_code VARCHAR(10) NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    node_type VARCHAR(50) NOT NULL CHECK (node_type IN ('PORT', 'INDUSTRIAL_HUB', 'BORDER_CHECKPOST', 'HIGHWAY_JUNCTION')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_oog_nodes_name_trgm ON oog_nodes USING gin (name gin_trgm_ops);
CREATE INDEX idx_oog_nodes_aliases ON oog_nodes USING gin (aliases);

-- ------------------------------------------------------------------------------
-- 2. Highway Road Segments (Graph Edges)
-- ------------------------------------------------------------------------------
CREATE TABLE oog_road_segments (
    segment_id VARCHAR(60) PRIMARY KEY,
    highway_no VARCHAR(50) NOT NULL,
    from_node_id VARCHAR(50) NOT NULL REFERENCES oog_nodes(node_id),
    to_node_id VARCHAR(50) NOT NULL REFERENCES oog_nodes(node_id),
    distance_km DOUBLE PRECISION NOT NULL,
    baseline_max_weight_mt DOUBLE PRECISION NOT NULL DEFAULT 150.0,
    baseline_vertical_clearance_m DOUBLE PRECISION NOT NULL DEFAULT 6.0,
    baseline_horizontal_clearance_m DOUBLE PRECISION NOT NULL DEFAULT 5.5,
    lane_count INT NOT NULL DEFAULT 4,
    is_ghat_section BOOLEAN NOT NULL DEFAULT FALSE,
    monsoon_flood_risk BOOLEAN NOT NULL DEFAULT FALSE,
    toll_plaza_count INT NOT NULL DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_oog_segments_from_to ON oog_road_segments(from_node_id, to_node_id);
CREATE INDEX idx_oog_segments_highway ON oog_road_segments(highway_no);

-- ------------------------------------------------------------------------------
-- 3. Bridge, Flyover & Underpass Constraints
-- ------------------------------------------------------------------------------
CREATE TABLE bridge_constraints (
    bridge_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    highway_no VARCHAR(50) NOT NULL,
    segment_id VARCHAR(60) NOT NULL REFERENCES oog_road_segments(segment_id),
    state_code VARCHAR(10) NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    max_weight_mt DOUBLE PRECISION NOT NULL,
    min_vertical_clearance_m DOUBLE PRECISION NOT NULL,
    min_horizontal_clearance_m DOUBLE PRECISION NOT NULL,
    has_bypass BOOLEAN NOT NULL DEFAULT FALSE,
    bypass_route_details TEXT,
    structural_condition VARCHAR(50) NOT NULL DEFAULT 'GOOD' CHECK (structural_condition IN ('GOOD', 'RESTRICTED', 'CRITICAL_AUDIT_REQUIRED')),
    warning_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_bridge_constraints_segment ON bridge_constraints(segment_id);
CREATE INDEX idx_bridge_constraints_weight ON bridge_constraints(max_weight_mt);
CREATE INDEX idx_bridge_constraints_height ON bridge_constraints(min_vertical_clearance_m);

-- ------------------------------------------------------------------------------
-- 4. RTO & Statutory Transit Rules (State & Central MoRTH)
-- ------------------------------------------------------------------------------
CREATE TABLE rto_rules (
    rule_id SERIAL PRIMARY KEY,
    state_code VARCHAR(10) NOT NULL,
    state_name VARCHAR(100) NOT NULL,
    cargo_category VARCHAR(50) NOT NULL,
    permit_type_required VARCHAR(150) NOT NULL,
    issuing_authority VARCHAR(150) NOT NULL,
    online_portal_url VARCHAR(255) NOT NULL,
    processing_sla_days INT NOT NULL,
    tax_formula JSONB NOT NULL,
    escort_rules JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_rto_rules_state ON rto_rules(state_code);
CREATE INDEX idx_rto_rules_category ON rto_rules(cargo_category);

-- ------------------------------------------------------------------------------
-- 5. OOG Survey Jobs (Durable State Machine)
-- ------------------------------------------------------------------------------
CREATE TABLE oog_survey_jobs (
    job_id VARCHAR(100) PRIMARY KEY,
    client_id VARCHAR(100) NOT NULL DEFAULT 'SEALAND_CLIENT',
    cargo_description TEXT NOT NULL,
    cargo_weight_mt DOUBLE PRECISION NOT NULL,
    length_m DOUBLE PRECISION NOT NULL,
    width_m DOUBLE PRECISION NOT NULL,
    height_m DOUBLE PRECISION NOT NULL,
    axle_count INT NOT NULL DEFAULT 6,
    trailer_type VARCHAR(100) NOT NULL DEFAULT 'Hydraulic Modular Multi-Axle',
    origin_raw VARCHAR(150) NOT NULL,
    destination_raw VARCHAR(150) NOT NULL,
    origin_node_id VARCHAR(50) REFERENCES oog_nodes(node_id),
    destination_node_id VARCHAR(50) REFERENCES oog_nodes(node_id),
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'CALCULATED', 'FLAGGED_FOR_SURVEY', 'APPROVED', 'REJECTED')),
    selected_route JSONB,
    bottlenecks_detected JSONB DEFAULT '[]'::jsonb,
    permits_required JSONB DEFAULT '[]'::jsonb,
    total_permit_tax_inr NUMERIC(15, 2) DEFAULT 0.00,
    total_distance_km DOUBLE PRECISION DEFAULT 0.0,
    risk_score INT DEFAULT 0,
    risk_factors JSONB DEFAULT '[]'::jsonb,
    is_heavy_lift BOOLEAN DEFAULT FALSE,
    is_super_wide BOOLEAN DEFAULT FALSE,
    requires_police_escort BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_oog_survey_jobs_status ON oog_survey_jobs(status);
CREATE INDEX idx_oog_survey_jobs_created ON oog_survey_jobs(created_at DESC);

-- ------------------------------------------------------------------------------
-- 6. Human Dispatcher Overrides & Route Waivers
-- ------------------------------------------------------------------------------
CREATE TABLE oog_survey_overrides (
    override_id SERIAL PRIMARY KEY,
    job_id VARCHAR(100) NOT NULL REFERENCES oog_survey_jobs(job_id),
    override_by VARCHAR(100) NOT NULL,
    override_reason TEXT NOT NULL,
    forced_bridges JSONB DEFAULT '[]'::jsonb,
    special_conditions TEXT,
    approved_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 7. Audit Logging
-- ------------------------------------------------------------------------------
CREATE TABLE oog_audit_logs (
    log_id BIGSERIAL PRIMARY KEY,
    job_id VARCHAR(100),
    action VARCHAR(100) NOT NULL,
    details JSONB NOT NULL,
    logged_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ==============================================================================
-- SEED DATA: Realistic Indian National Highway Network for Heavy Haulage
-- ==============================================================================

-- 1. Nodes
INSERT INTO oog_nodes (node_id, name, aliases, state_code, latitude, longitude, node_type) VALUES
('PORT_CODE_INVTZ', 'Visakhapatnam Port', ARRAY['Vizag', 'Vishakapatnam', 'Visakhapatnam', 'INVTZ', 'Vizag Port'], 'AP', 17.6868, 83.2185, 'PORT'),
('PORT_CODE_INMAA', 'Chennai Port', ARRAY['Chennai', 'Madras', 'INMAA', 'Chennai Port Trust'], 'TN', 13.0827, 80.2707, 'PORT'),
('PORT_CODE_INNSA', 'JNPT Navi Mumbai', ARRAY['JNPT', 'Nhava Sheva', 'INNSA', 'Jawaharlal Nehru Port'], 'MH', 18.9499, 72.9525, 'PORT'),
('PORT_CODE_INCCU', 'Kolkata Haldia Port', ARRAY['Kolkata', 'Calcutta', 'Haldia', 'INCCU', 'Kolkata Port'], 'WB', 22.5726, 88.3639, 'PORT'),
('PORT_CODE_INPRT', 'Paradip Port', ARRAY['Paradip', 'Paradeep', 'INPRT'], 'OD', 20.3164, 86.6114, 'PORT'),
('PORT_CODE_INMUN', 'Mundra Port', ARRAY['Mundra', 'INMUN', 'Adani Mundra'], 'GJ', 22.8395, 69.7042, 'PORT'),

('NODE_HYD_HUB', 'Hyderabad Logistics Hub', ARRAY['Hyderabad', 'Secunderabad', 'Patancheru', 'Shamshabad'], 'TS', 17.3850, 78.4867, 'INDUSTRIAL_HUB'),
('NODE_NAGPUR_HUB', 'Nagpur Multimodal Hub', ARRAY['Nagpur', 'MIHAN', 'Butibori'], 'MH', 21.1458, 79.0882, 'INDUSTRIAL_HUB'),
('NODE_RAIPUR_STEEL', 'Raipur Industrial Corridor', ARRAY['Raipur', 'Bhilai', 'Durg'], 'CG', 21.2514, 81.6296, 'INDUSTRIAL_HUB'),
('NODE_JHARSUGUDA_ALUM', 'Jharsuguda Power Corridor', ARRAY['Jharsuguda', 'Vedanta Hub', 'Sundargarh'], 'OD', 21.8550, 84.0060, 'INDUSTRIAL_HUB'),
('NODE_JAMSHEDPUR_STEEL', 'Jamshedpur Tata Steel Zone', ARRAY['Jamshedpur', 'Tatanagar', 'Adityapur'], 'JH', 22.8046, 86.2029, 'INDUSTRIAL_HUB'),
('NODE_PUNE_MFG', 'Pune Auto Manufacturing Cluster', ARRAY['Pune', 'Chakan', 'Talegaon', 'Pimpri'], 'MH', 18.5204, 73.8567, 'INDUSTRIAL_HUB'),
('NODE_BLR_TECH', 'Bangalore Industrial Hub', ARRAY['Bangalore', 'Bengaluru', 'Peenya', 'Hosur'], 'KA', 12.9716, 77.5946, 'INDUSTRIAL_HUB'),
('NODE_AMD_HUB', 'Ahmedabad Engineering Hub', ARRAY['Ahmedabad', 'Sanand', 'Changodar'], 'GJ', 23.0225, 72.5714, 'INDUSTRIAL_HUB'),
('NODE_DGP_STEEL', 'Durgapur Industrial Complex', ARRAY['Durgapur', 'Asansol'], 'WB', 23.5204, 87.3119, 'INDUSTRIAL_HUB'),

('NODE_VGA_JUNCTION', 'Vijayawada Highway Junction', ARRAY['Vijayawada', 'Gannavaram', 'Amaravati'], 'AP', 16.5062, 80.6480, 'HIGHWAY_JUNCTION'),
('NODE_SRIKAKULAM_JCT', 'Srikakulam Road Node', ARRAY['Srikakulam', 'Palasa'], 'AP', 18.2949, 83.8938, 'HIGHWAY_JUNCTION'),
('NODE_BAM_JUNCTION', 'Berhampur Gateway', ARRAY['Berhampur', 'Brahmapur'], 'OD', 19.3150, 84.7941, 'BORDER_CHECKPOST'),
('NODE_BBS_JUNCTION', 'Bhubaneswar Highway Node', ARRAY['Bhubaneswar', 'Cuttack Junction'], 'OD', 20.2961, 85.8245, 'HIGHWAY_JUNCTION'),
('NODE_SBP_JUNCTION', 'Sambalpur East-West Node', ARRAY['Sambalpur', 'Hirakud'], 'OD', 21.4669, 83.9812, 'HIGHWAY_JUNCTION'),
('NODE_KGP_JUNCTION', 'Kharagpur Logistics Junction', ARRAY['Kharagpur', 'Midnapore'], 'WB', 22.3460, 87.2320, 'HIGHWAY_JUNCTION'),
('NODE_AURANGABAD_JCT', 'Chhatrapati Sambhajinagar Node', ARRAY['Aurangabad', 'Waluj'], 'MH', 19.8762, 75.3433, 'HIGHWAY_JUNCTION'),
('NODE_SURAT_IND', 'Surat Hazira Heavy Belt', ARRAY['Surat', 'Hazira'], 'GJ', 21.1702, 72.8311, 'INDUSTRIAL_HUB');

-- 2. Highway Segments
INSERT INTO oog_road_segments (segment_id, highway_no, from_node_id, to_node_id, distance_km, baseline_max_weight_mt, baseline_vertical_clearance_m, baseline_horizontal_clearance_m, lane_count, is_ghat_section, monsoon_flood_risk, toll_plaza_count) VALUES
-- NH-16 East Coast Corridor
('SEG_NH16_VIZAG_SRIKAKULAM', 'NH-16', 'PORT_CODE_INVTZ', 'NODE_SRIKAKULAM_JCT', 115.0, 70.0, 5.2, 4.5, 4, false, false, 2),
('SEG_NH16_SRIKAKULAM_VIZAG', 'NH-16', 'NODE_SRIKAKULAM_JCT', 'PORT_CODE_INVTZ', 115.0, 70.0, 5.2, 4.5, 4, false, false, 2),
('SEG_NH16_SRIKAKULAM_BERHAMPUR', 'NH-16', 'NODE_SRIKAKULAM_JCT', 'NODE_BAM_JUNCTION', 160.0, 80.0, 5.3, 4.8, 4, false, true, 2),
('SEG_NH16_BERHAMPUR_SRIKAKULAM', 'NH-16', 'NODE_BAM_JUNCTION', 'NODE_SRIKAKULAM_JCT', 160.0, 80.0, 5.3, 4.8, 4, false, true, 2),
('SEG_NH16_BERHAMPUR_BHUBANESWAR', 'NH-16', 'NODE_BAM_JUNCTION', 'NODE_BBS_JUNCTION', 170.0, 110.0, 5.5, 5.0, 4, false, false, 3),
('SEG_NH16_BHUBANESWAR_BERHAMPUR', 'NH-16', 'NODE_BBS_JUNCTION', 'NODE_BAM_JUNCTION', 170.0, 110.0, 5.5, 5.0, 4, false, false, 3),
('SEG_NH16_BHUBANESWAR_PARADIP', 'NH-16', 'NODE_BBS_JUNCTION', 'PORT_CODE_INPRT', 105.0, 150.0, 6.0, 5.5, 4, false, false, 2),
('SEG_NH16_PARADIP_BHUBANESWAR', 'NH-16', 'PORT_CODE_INPRT', 'NODE_BBS_JUNCTION', 105.0, 150.0, 6.0, 5.5, 4, false, false, 2),
('SEG_NH16_BHUBANESWAR_KHARAGPUR', 'NH-16', 'NODE_BBS_JUNCTION', 'NODE_KGP_JUNCTION', 280.0, 90.0, 5.4, 4.8, 4, false, true, 4),
('SEG_NH16_KHARAGPUR_BHUBANESWAR', 'NH-16', 'NODE_KGP_JUNCTION', 'NODE_BBS_JUNCTION', 280.0, 90.0, 5.4, 4.8, 4, false, true, 4),
('SEG_NH16_KHARAGPUR_KOLKATA', 'NH-16', 'NODE_KGP_JUNCTION', 'PORT_CODE_INCCU', 130.0, 120.0, 5.5, 5.2, 6, false, false, 2),
('SEG_NH16_KOLKATA_KHARAGPUR', 'NH-16', 'PORT_CODE_INCCU', 'NODE_KGP_JUNCTION', 130.0, 120.0, 5.5, 5.2, 6, false, false, 2),

-- NH-16 South to Vijayawada / Chennai
('SEG_NH16_VIZAG_VIJAYAWADA', 'NH-16', 'PORT_CODE_INVTZ', 'NODE_VGA_JUNCTION', 350.0, 120.0, 5.6, 5.2, 6, false, false, 5),
('SEG_NH16_VIJAYAWADA_VIZAG', 'NH-16', 'NODE_VGA_JUNCTION', 'PORT_CODE_INVTZ', 350.0, 120.0, 5.6, 5.2, 6, false, false, 5),
('SEG_NH16_VIJAYAWADA_CHENNAI', 'NH-16', 'NODE_VGA_JUNCTION', 'PORT_CODE_INMAA', 430.0, 140.0, 5.8, 5.5, 6, false, false, 6),
('SEG_NH16_CHENNAI_VIJAYAWADA', 'NH-16', 'PORT_CODE_INMAA', 'NODE_VGA_JUNCTION', 430.0, 140.0, 5.8, 5.5, 6, false, false, 6),

-- NH-65 Connecting Vijayawada to Hyderabad & Pune
('SEG_NH65_VIJAYAWADA_HYDERABAD', 'NH-65', 'NODE_VGA_JUNCTION', 'NODE_HYD_HUB', 275.0, 140.0, 5.5, 5.2, 4, false, false, 4),
('SEG_NH65_HYDERABAD_VIJAYAWADA', 'NH-65', 'NODE_HYD_HUB', 'NODE_VGA_JUNCTION', 275.0, 140.0, 5.5, 5.2, 4, false, false, 4),
('SEG_NH65_HYDERABAD_PUNE', 'NH-65', 'NODE_HYD_HUB', 'NODE_PUNE_MFG', 550.0, 130.0, 5.4, 5.0, 4, false, false, 7),
('SEG_NH65_PUNE_HYDERABAD', 'NH-65', 'NODE_PUNE_MFG', 'NODE_HYD_HUB', 550.0, 130.0, 5.4, 5.0, 4, false, false, 7),

-- NH-44 Connecting Hyderabad to Nagpur & Bangalore
('SEG_NH44_HYDERABAD_NAGPUR', 'NH-44', 'NODE_HYD_HUB', 'NODE_NAGPUR_HUB', 500.0, 150.0, 5.8, 5.5, 4, false, false, 6),
('SEG_NH44_NAGPUR_HYDERABAD', 'NH-44', 'NODE_NAGPUR_HUB', 'NODE_HYD_HUB', 500.0, 150.0, 5.8, 5.5, 4, false, false, 6),
('SEG_NH44_HYDERABAD_BANGALORE', 'NH-44', 'NODE_HYD_HUB', 'NODE_BLR_TECH', 570.0, 160.0, 6.0, 5.8, 6, false, false, 7),
('SEG_NH44_BANGALORE_HYDERABAD', 'NH-44', 'NODE_BLR_TECH', 'NODE_HYD_HUB', 570.0, 160.0, 6.0, 5.8, 6, false, false, 7),

-- NH-53 East-West Corridor (Nagpur -> Raipur -> Sambalpur -> Paradip / Kolkata)
('SEG_NH53_NAGPUR_RAIPUR', 'NH-53', 'NODE_NAGPUR_HUB', 'NODE_RAIPUR_STEEL', 285.0, 130.0, 5.5, 5.2, 4, false, false, 4),
('SEG_NH53_RAIPUR_NAGPUR', 'NH-53', 'NODE_RAIPUR_STEEL', 'NODE_NAGPUR_HUB', 285.0, 130.0, 5.5, 5.2, 4, false, false, 4),
('SEG_NH53_RAIPUR_SAMBALPUR', 'NH-53', 'NODE_RAIPUR_STEEL', 'NODE_SBP_JUNCTION', 260.0, 120.0, 5.4, 5.0, 4, false, false, 3),
('SEG_NH53_SAMBALPUR_RAIPUR', 'NH-53', 'NODE_SBP_JUNCTION', 'NODE_RAIPUR_STEEL', 260.0, 120.0, 5.4, 5.0, 4, false, false, 3),
('SEG_NH53_SAMBALPUR_JHARSUGUDA', 'SH-10', 'NODE_SBP_JUNCTION', 'NODE_JHARSUGUDA_ALUM', 55.0, 180.0, 6.2, 6.0, 4, false, false, 1),
('SEG_NH53_JHARSUGUDA_SAMBALPUR', 'SH-10', 'NODE_JHARSUGUDA_ALUM', 'NODE_SBP_JUNCTION', 55.0, 180.0, 6.2, 6.0, 4, false, false, 1),
('SEG_NH53_SAMBALPUR_BHUBANESWAR', 'NH-55', 'NODE_SBP_JUNCTION', 'NODE_BBS_JUNCTION', 280.0, 95.0, 5.2, 4.6, 2, false, true, 3),
('SEG_NH53_BHUBANESWAR_SAMBALPUR', 'NH-55', 'NODE_BBS_JUNCTION', 'NODE_SBP_JUNCTION', 280.0, 95.0, 5.2, 4.6, 2, false, true, 3),

-- Heavy Industrial Feeder Lines
('SEG_JHARSUGUDA_JAMSHEDPUR', 'NH-49', 'NODE_JHARSUGUDA_ALUM', 'NODE_JAMSHEDPUR_STEEL', 265.0, 140.0, 5.6, 5.2, 4, false, false, 3),
('SEG_JAMSHEDPUR_JHARSUGUDA', 'NH-49', 'NODE_JAMSHEDPUR_STEEL', 'NODE_JHARSUGUDA_ALUM', 265.0, 140.0, 5.6, 5.2, 4, false, false, 3),
('SEG_JAMSHEDPUR_KHARAGPUR', 'NH-49', 'NODE_JAMSHEDPUR_STEEL', 'NODE_KGP_JUNCTION', 135.0, 130.0, 5.5, 5.0, 4, false, false, 2),
('SEG_KHARAGPUR_JAMSHEDPUR', 'NH-49', 'NODE_KGP_JUNCTION', 'NODE_JAMSHEDPUR_STEEL', 135.0, 130.0, 5.5, 5.0, 4, false, false, 2),
('SEG_JAMSHEDPUR_DURGAPUR', 'NH-18', 'NODE_JAMSHEDPUR_STEEL', 'NODE_DGP_STEEL', 165.0, 120.0, 5.4, 5.0, 4, false, false, 2),
('SEG_DURGAPUR_JAMSHEDPUR', 'NH-18', 'NODE_DGP_STEEL', 'NODE_JAMSHEDPUR_STEEL', 165.0, 120.0, 5.4, 5.0, 4, false, false, 2),

-- Western Corridor connecting JNPT / Pune / Ahmedabad
('SEG_NH48_JNPT_PUNE', 'NH-48', 'PORT_CODE_INNSA', 'NODE_PUNE_MFG', 150.0, 150.0, 5.0, 4.6, 6, true, false, 2),
('SEG_NH48_PUNE_JNPT', 'NH-48', 'NODE_PUNE_MFG', 'PORT_CODE_INNSA', 150.0, 150.0, 5.0, 4.6, 6, true, false, 2),
('SEG_NH48_PUNE_BANGALORE', 'NH-48', 'NODE_PUNE_MFG', 'NODE_BLR_TECH', 840.0, 150.0, 5.8, 5.5, 6, false, false, 9),
('SEG_NH48_BANGALORE_PUNE', 'NH-48', 'NODE_BLR_TECH', 'NODE_PUNE_MFG', 840.0, 150.0, 5.8, 5.5, 6, false, false, 9),
('SEG_NH48_JNPT_SURAT', 'NH-48', 'PORT_CODE_INNSA', 'NODE_SURAT_IND', 280.0, 160.0, 5.8, 5.5, 6, false, false, 4),
('SEG_NH48_SURAT_JNPT', 'NH-48', 'NODE_SURAT_IND', 'PORT_CODE_INNSA', 280.0, 160.0, 5.8, 5.5, 6, false, false, 4),
('SEG_NH48_SURAT_AHMEDABAD', 'NH-48', 'NODE_SURAT_IND', 'NODE_AMD_HUB', 260.0, 160.0, 6.0, 5.6, 6, false, false, 3),
('SEG_NH48_AHMEDABAD_SURAT', 'NH-48', 'NODE_AMD_HUB', 'NODE_SURAT_IND', 260.0, 160.0, 6.0, 5.6, 6, false, false, 3),
('SEG_AHMEDABAD_MUNDRA', 'NH-947', 'NODE_AMD_HUB', 'PORT_CODE_INMUN', 350.0, 180.0, 6.2, 5.8, 4, false, false, 4),
('SEG_MUNDRA_AHMEDABAD', 'NH-947', 'PORT_CODE_INMUN', 'NODE_AMD_HUB', 350.0, 180.0, 6.2, 5.8, 4, false, false, 4);

-- 3. Specific Bridge Constraints (Physical Bottlenecks)
INSERT INTO bridge_constraints (bridge_id, name, highway_no, segment_id, state_code, latitude, longitude, max_weight_mt, min_vertical_clearance_m, min_horizontal_clearance_m, has_bypass, bypass_route_details, structural_condition, warning_notes) VALUES
('BR_SRIKAKULAM_NAGAVALI', 'Nagavali River Arch Bridge', 'NH-16', 'SEG_NH16_VIZAG_SRIKAKULAM', 'AP', 18.3012, 83.9015, 65.0, 4.9, 4.2, true, 'Bypass via Srikakulam Bypass Road (adds 18km, supports 150MT)', 'RESTRICTED', 'Old masonry arch piers. Loads > 65MT strictly prohibited over main bridge.'),
('BR_GODAVARI_FOURTH', 'Godavari 4th Bridge Rajahmundry', 'NH-16', 'SEG_NH16_VIZAG_VIJAYAWADA', 'AP', 17.0005, 81.7800, 160.0, 5.8, 5.2, false, NULL, 'GOOD', 'Heavy prestressed concrete structure. Safe up to 160MT.'),
('BR_KRISHNA_PRAKASAM', 'Prakasam Barrage Approach ROB', 'NH-16', 'SEG_NH16_VIZAG_VIJAYAWADA', 'AP', 16.5120, 80.6180, 80.0, 5.0, 4.5, true, 'Kanaka Durga Bypass Viaduct (supports 180MT)', 'RESTRICTED', 'Height restricted due to overhead railway traction lines (OHE).'),
('BR_RUSHIKULYA_GANJAM', 'Rushikulya River Bridge', 'NH-16', 'SEG_NH16_SRIKAKULAM_BERHAMPUR', 'OD', 19.3510, 84.8120, 75.0, 5.2, 4.6, false, NULL, 'RESTRICTED', 'Pier scouring detected during monsoon. Max speed 10 km/h for heavy cargo.'),
('BR_MAHANADI_CUTTACK', 'Mahanadi River Viaduct', 'NH-16', 'SEG_NH16_BHUBANESWAR_KHARAGPUR', 'OD', 20.4850, 85.8820, 100.0, 5.4, 4.8, true, 'Choudwar Industrial Bypass (supports 200MT)', 'GOOD', 'Multi-span concrete girder bridge.'),
('BR_SUBARNAREKHA_JALESWAR', 'Subarnarekha Border Bridge', 'NH-16', 'SEG_NH16_BHUBANESWAR_KHARAGPUR', 'OD', 21.8210, 87.2100, 85.0, 5.1, 4.5, false, NULL, 'RESTRICTED', 'Critical interstate bridge on Odisha-WB border. Weigh-in-motion automated sensor.'),
('BR_BHOR_GHAT_ROB', 'Khandala Railway Over Bridge', 'NH-48', 'SEG_NH48_JNPT_PUNE', 'MH', 18.7520, 73.3610, 150.0, 4.8, 4.4, false, NULL, 'CRITICAL_AUDIT_REQUIRED', 'Severe height restriction: 4.8m vertical clearance under railway overhead wires.'),
('BR_KASARA_GHAT_UNDERPASS', 'Kasara Ghat NH-160 Underpass', 'NH-48', 'SEG_NH48_JNPT_PUNE', 'MH', 19.6540, 73.4890, 90.0, 4.7, 4.1, true, 'Nashik Phata Outer Bypass', 'RESTRICTED', 'Low clearance tunnel; escorts required.'),
('BR_WAINGANGA_BHANDARA', 'Wainganga River Bridge Bhandara', 'NH-53', 'SEG_NH53_NAGPUR_RAIPUR', 'MH', 21.1720, 79.6510, 95.0, 5.3, 4.8, true, 'Bhandara Outer Bypass (supports 180MT)', 'RESTRICTED', 'Single 2-lane old section undergoing widening.'),
('BR_SHEONATH_DURG', 'Sheonath River Bridge Durg', 'NH-53', 'SEG_NH53_NAGPUR_RAIPUR', 'CG', 21.1920, 81.2810, 120.0, 5.6, 5.0, false, NULL, 'GOOD', 'Standard NHAI 4-lane box girder bridge.'),
('BR_HIRAKUD_CANAL', 'Hirakud Feeder Canal Bridge', 'SH-10', 'SEG_NH53_SAMBALPUR_JHARSUGUDA', 'OD', 21.5210, 83.9100, 190.0, 6.2, 5.8, false, NULL, 'GOOD', 'Built specifically for heavy power plant and smelter equipment delivery.'),
('BR_SURYAPET_HT_LINE', 'Suryapet 220kV Overhead Line Crossing', 'NH-65', 'SEG_NH65_VIJAYAWADA_HYDERABAD', 'TS', 17.1420, 79.6210, 250.0, 5.2, 6.0, false, NULL, 'RESTRICTED', 'Electrical clearance constraint. High loads > 5.2m require TSTRANSCO power shutdown.');

-- 4. RTO & Statutory Transit Rules
INSERT INTO rto_rules (state_code, state_name, cargo_category, permit_type_required, issuing_authority, online_portal_url, processing_sla_days, tax_formula, escort_rules) VALUES
('CENTRAL', 'All India Ministry of Road Transport', 'ALL_ODC_OOG', 'MoRTH National Online ODC Transit Permit', 'Ministry of Road Transport and Highways (MoRTH)', 'https://morth.nic.in/online-odc-portal', 2, 
 '{"base_fee_inr": 10000, "per_km_inr": 25, "weight_slab_over_40mt_inr": 80}'::jsonb,
 '{"escort_required_if_width_gt_m": 3.5, "police_escort_if_width_gt_m": 4.5, "max_speed_kmh": 25}'::jsonb),

('AP', 'Andhra Pradesh', 'ODC_OOG', 'AP State RTO Transit Clearance & Road Tax', 'Transport Commissioner, Andhra Pradesh (Vijayawada)', 'https://aptransport.org/odc-clearance', 3,
 '{"base_fee_inr": 15000, "weight_surcharge_per_mt_inr": 120, "distance_rate_per_km_inr": 45, "width_penalty_factor": 1.25}'::jsonb,
 '{"pilot_car": true, "police_escort_if_heavy": true, "night_movement_allowed": false, "curfew_hours": "18:00 - 06:00"}'::jsonb),

('TS', 'Telangana', 'ODC_OOG', 'TS Transport Heavy Machinery Transit NOC', 'RTO Telangana (Hyderabad)', 'https://transport.telangana.gov.in', 3,
 '{"base_fee_inr": 12000, "weight_surcharge_per_mt_inr": 100, "distance_rate_per_km_inr": 40, "width_penalty_factor": 1.2}'::jsonb,
 '{"pilot_car": true, "police_escort_if_heavy": false, "night_movement_allowed": true, "urban_curfew": "08:00 - 11:00, 17:00 - 21:00"}'::jsonb),

('OD', 'Odisha', 'ODC_OOG', 'STA Odisha Heavy Transit Permit & Bridge Safety Clearance', 'State Transport Authority (STA Cuttack)', 'https://odishatransport.gov.in', 4,
 '{"base_fee_inr": 18000, "weight_surcharge_per_mt_inr": 150, "distance_rate_per_km_inr": 50, "width_penalty_factor": 1.35}'::jsonb,
 '{"pilot_car": true, "police_escort_if_heavy": true, "bridge_inspection_mandatory_if_weight_gt_mt": 100, "night_movement_allowed": false}'::jsonb),

('WB', 'West Bengal', 'ODC_OOG', 'WB Transport Directorate Inter-State Transit NOC', 'Transport Directorate, Government of West Bengal (Kolkata)', 'https://transport.wb.gov.in', 5,
 '{"base_fee_inr": 20000, "weight_surcharge_per_mt_inr": 140, "distance_rate_per_km_inr": 55, "width_penalty_factor": 1.4}'::jsonb,
 '{"pilot_car": true, "police_escort_if_heavy": true, "kolkata_entry_curfew": "06:00 - 22:00", "night_movement_allowed": true}'::jsonb),

('MH', 'Maharashtra', 'ODC_OOG', 'Maharashtra RTO ODC Road Safety Permit', 'Transport Commissioner, Maharashtra (Mumbai)', 'https://transport.maharashtra.gov.in', 4,
 '{"base_fee_inr": 22000, "weight_surcharge_per_mt_inr": 160, "distance_rate_per_km_inr": 60, "width_penalty_factor": 1.3}'::jsonb,
 '{"pilot_car": true, "ghat_section_police_escort": true, "night_movement_allowed": false, "curfew_hours": "19:00 - 05:00"}'::jsonb),

('CG', 'Chhattisgarh', 'ODC_OOG', 'Chhattisgarh Heavy Transit Certificate', 'Transport Department, Raipur', 'https://cgtransport.gov.in', 3,
 '{"base_fee_inr": 14000, "weight_surcharge_per_mt_inr": 110, "distance_rate_per_km_inr": 42, "width_penalty_factor": 1.2}'::jsonb,
 '{"pilot_car": true, "police_escort_if_heavy": false, "night_movement_allowed": true}'::jsonb),

('TN', 'Tamil Nadu', 'ODC_OOG', 'Tamil Nadu Transport Special Heavy Load Pass', 'Transport Department, Chennai', 'https://tnsta.gov.in', 3,
 '{"base_fee_inr": 16000, "weight_surcharge_per_mt_inr": 130, "distance_rate_per_km_inr": 48, "width_penalty_factor": 1.25}'::jsonb,
 '{"pilot_car": true, "police_escort_if_heavy": false, "night_movement_allowed": false}'::jsonb),

('KA', 'Karnataka', 'ODC_OOG', 'Karnataka Heavy Transit Endorsement', 'Transport Department, Bangalore', 'https://transport.karnataka.gov.in', 4,
 '{"base_fee_inr": 18000, "weight_surcharge_per_mt_inr": 140, "distance_rate_per_km_inr": 52, "width_penalty_factor": 1.3}'::jsonb,
 '{"pilot_car": true, "police_escort_if_heavy": true, "night_movement_allowed": false}'::jsonb),

('GJ', 'Gujarat', 'ODC_OOG', 'Gujarat Motor Vehicles Dept ODC Transit Approval', 'Commissioner of Transport, Gandhinagar', 'https://cot.gujarat.gov.in', 3,
 '{"base_fee_inr": 15000, "weight_surcharge_per_mt_inr": 115, "distance_rate_per_km_inr": 45, "width_penalty_factor": 1.2}'::jsonb,
 '{"pilot_car": true, "police_escort_if_heavy": false, "night_movement_allowed": true}'::jsonb);
