# TRACK 03 — RGPD Compliance Audit
**PlantaOS × Rock in Rio Lisboa 2026**
Auditor: Claude Sonnet 4.6 | Date: 2026-05-27 | Scope: Both codebases

---

## Executive Summary

The **PlantaOS (planta-rir2026)** codebase is substantially compliant with RGPD requirements
as applied to a real-time crowd management system at a large public event. No raw MAC
addresses, biometric data, or per-person GPS tracks are stored or transmitted. The primary
exposure is the **complete absence of any written retention policy or DPIA document**.

The **reference system (rockinrio_official_v1)** shares the same privacy-by-design approach
in its sensor layer, but introduces **two MEDIUM-severity findings**: IP addresses are logged
in the SSE/WebSocket endpoint, and the user GPS input from `/v1/nearest-wc` is echoed back
in the API response (creating a partial data flow that, if logged by a reverse proxy with
default settings, would link an IP to a GPS coordinate).

**No BLOCKER findings** in either codebase.

---

## Category Assessments

### 1. MAC Address Handling — PASS

**Evidence searched:**
```
grep -ri "mac_address|mac_addr|raw_mac" backend/
```
Result: zero hits for any of these identifiers in planta-rir2026.

**Firmware (rockinrio_official_v1/firmware/lilygo_sniffer/rockinrio_v4.ino):**

The LilyGo firmware:
- Reads source MAC bytes into a `uint64_t mac` variable held only in `std::set<uint64_t> mac_window` (RAM)
- Calls `flush_mac_window()` every `DEDUP_WINDOW_MS` (10 seconds): `devices_raw = mac_window.size(); mac_window.clear()`
- HTTP POST payload contains **only** `devices_raw` (integer count) and `pessoas_estimadas` — no MAC bytes ever leave the device
- Comment at file head (line 15): *"MACs contados em memória e descartados após a janela de 10s. NUNCA persistidos em flash, EEPROM, SPIFFS ou enviados para o servidor."*

The `SensorReading` schema in planta-rir2026 (`backend/app/schemas.py:140`) accepts only:
`cluster_id`, `section`, `source`, `contagem_entrada`, `contagem_saida`, `ocupacao_absoluta`, `confianca_pct`, `ts` — no MAC field.

The rockinrio_official_v1 `LilygoPayload` (`backend/app/routers/ingest.py:44`) accepts:
`cluster_id`, `sensor_node_id`, `timestamp_utc`, `devices_raw`, `pessoas_estimadas`, `uptime_s`, `rssi_ap` — no MAC field.

**Assessment: PASS** — Architecture correctly implements count-before-transmit. Raw MACs never leave the device.

**Caveat:** The firmware does **not** apply a cryptographic hash (SHA-256 + truncation) before storing MACs in `mac_window`. Instead it uses raw 48-bit `uint64_t` keys. Because these keys are discarded every 10 seconds and **never transmitted**, this is compliant in practice. However the firmware comment claims RGPD compliance without explaining the in-memory-only lifecycle. This is sufficient but should be documented more explicitly for auditors.

---

### 2. Camera Frame Storage — PASS

**Evidence searched:**
```
grep -ri "frame.save|cv2.imwrite|image.save|write.*frame|store.*frame" backend/
```
Result: zero hits in both codebases.

The `ProsegurReading` schema (`backend/app/schemas.py`) accepts only:
`cluster_id`, `section`, `ocupacao_absoluta`, `fila_actual`, `confianca_ml`, `ts` — no image, frame, vector, or embedding field.

The rockinrio_official_v1 `CameraPayload` accepts: `cluster_id`, `sensor_node_id`, `timestamp_utc`, `count`, `confidence`, `zone` — no image data.

Comment in rockinrio_official_v1 sensor topology (`models/sensor_topology.py:18`):
*"RGPD: edge AI · zero imagens persistidas"*

**Assessment: PASS** — Camera systems transmit only integer counts and confidence scores. No frames, crops, biometric vectors, or face embeddings enter either backend.

---

### 3. Firmware MAC Hashing — PARTIAL PASS

**File examined:** `rockinrio_official_v1/firmware/lilygo_sniffer/rockinrio_v4.ino`

The firmware uses in-memory deduplication with a 10-second window followed by full discard.
This achieves the privacy goal (no MACs transmitted) but does **not** implement a formal
cryptographic hash step. The firmware:
- Does NOT apply SHA-256 or any hash function to MACs before inserting into `mac_window`
- Does NOT produce a 32-bit truncated hash as the audit requirement specifies

**Finding (LOW):** The firmware's privacy approach (discard entire set after window) is
functionally equivalent to or stronger than hash+truncate, since not even a hash is
transmitted. However, it diverges from the stated RGPD architecture description
("send 32-bit truncated hash only"). Documentation should be aligned with the actual
implementation to avoid confusion during CNPD review.

**Assessment: PARTIAL PASS** — Privacy goal achieved through discard-not-hash approach. No
hash-before-transmit as specified in architecture documents.

---

### 4. Data Retention Policy — MISSING (HIGH)

**Evidence searched:**
```
find planta-rir2026 -name "RGPD*" -o -name "DPIA*" -o -name "privacy*"
find rockinrio_official_v1/docs -type f
```
Result: **zero results** — no RGPD, DPIA, or privacy policy documents exist in either codebase.

**rockinrio_official_v1 inline reference:** `db.py:70` states:
*"Retenção: 7 dias (configurada via TimescaleDB retention policy)"*

However, the Alembic migration (`migrations/versions/7b6b8032b0be_initial.py`) creates the
hypertable structure but contains **no** `add_retention_policy()` or `drop_chunks()` SQL call.
The 7-day retention is mentioned in a code comment but is **not implemented** in the migration.

**planta-rir2026** operates entirely in-memory (no database, no persistence layer) with
in-process state reset on restart. No formal retention policy document exists.

**Assessment: MISSING** — No written retention policy document. rockinrio_official_v1
retention policy referenced in comments but not enforced by code.

**Finding (HIGH):** CNPD expects a documented retention schedule as part of any DPIA. Draft
DPIA created as part of this audit (track_03_DPIA_draft.md).

---

### 5. Schema PII Fields — PASS

**SensorReading schema** (`backend/app/schemas.py:140-178`):
```python
class SensorReading(BaseModel):
    cluster_id: str          # WC cluster identifier (non-personal)
    section: str             # M / F / U  (non-personal)
    source: SensorSource     # IR or WiFi (non-personal)
    contagem_entrada: int    # aggregate count (non-personal)
    contagem_saida: int      # aggregate count (non-personal)
    ocupacao_absoluta: Optional[int]  # aggregate (non-personal)
    confianca_pct: float     # model confidence (non-personal)
    ts: float                # unix timestamp (non-personal)
```
No `lat`, `lon`, `mac`, `device_id`, `uuid`, `ip`, or any linkable identifier.

**ProsegurReading schema** (`backend/app/schemas.py`):
No PII fields — only `cluster_id`, `section`, `ocupacao_absoluta`, `fila_actual`, `confianca_ml`, `ts`.

**ClusterState schema** (`backend/app/schemas.py:100`):
Contains `lat: float` and `lon: float` fields. These are **static infrastructure coordinates**
(fixed GPS position of each WC cluster building) confirmed by:
- Comment in `backend/app/data/clusters.py:7`: *"GPS coordinates are static metadata only, NOT in telemetry payloads."*
- Values are hardcoded literals (e.g., `38.78230`, `-9.09371`) for each of the 8 clusters.

These are equivalent to a building address and are not personal data under RGPD Article 4.

**rockinrio_official_v1 `/v1/nearest-wc` response** (`routers/proximity.py:132`):
Returns `"user_gps": {"lat": lat, "lon": lon}` — echoes the user's submitted GPS back.
This is an **ephemeral API response** (not stored), but if the request URL is logged by
uvicorn's access logger (default behaviour), the GPS coordinates appear in log files as
query parameters: `GET /v1/nearest-wc?lat=38.782&lon=-9.093&gender=F`

**Finding (MEDIUM):** rockinrio_official_v1 proximity endpoint logs GPS+IP via default
uvicorn access log. See Section 8 for fix.

---

### 6. Individual Tracking — PASS

**Evidence searched:**
```
grep -ri "biometric|face.*crop|face.*vector|embedding|device_id|bluetooth|ble_uuid|movement.*log|track.*person"
```
Result: zero hits in both codebases (excluding .venv and node_modules).

All counts are aggregate occupancy integers. The system tracks "how many people are in WC-03"
not "person X entered WC-03 at time T". No per-person movement log exists in any table,
model, or schema.

IR events in rockinrio_official_v1 (`ir_events` table) record door, direction, beam
timestamps, and confidence — but no person identifier. Events cannot be linked to an
individual across separate door crossings (no session, token, or biometric identifier).

**Assessment: PASS**

---

### 7. WiFi Probe Counting Protocol — PASS

```
grep -rn "telemoveis|wifi.*count|probe.*count|sniff|sniffer" backend/app/schemas.py backend/app/routers/
```
Result: zero hits in schemas.py (correct — no sniffer-specific fields).

The ingest router (`routers/ingest.py`) uses the generic `SensorReading` with `source=WiFi`,
accepting only `contagem_entrada` / `contagem_saida` / `ocupacao_absoluta` counts. The
WiFi→people conversion factor (2.5×) is applied in firmware before transmission.

**Assessment: PASS**

---

### 8. IP Addresses in Logs

**planta-rir2026:** No `request.client`, `remote_addr`, or IP logging found in any router or
service. WebSocket logs only client count (integer). Startup uses `uvicorn --reload` without
explicit `--no-access-log`; default uvicorn access log **will** include remote IP addresses
for all requests including sensor ingest.

**Finding (MEDIUM):** Default uvicorn access logging logs IP addresses for every HTTP
request, including from Prosegur cameras and LilyGo sensors. Sensor IPs are not visitor IPs,
but the access log configuration is undocumented.

**rockinrio_official_v1:**
- `routers/ws_sse.py:161-164`: Explicitly captures and logs client IP:
  ```python
  client_ip = request.client.host if request.client else "unknown"
  log.info("sse.connected clusters=%s ip=%s", cluster_ids, client_ip)
  log.info("sse.disconnected clusters=%s ip=%s", cluster_ids, client_ip)
  ```
  These log lines appear for every dashboard/display TV connection.
- `routers/proximity.py:132`: User GPS echoed in response (see Section 5).
  Combined with access log IP, creates a linkable record: `IP + GPS + timestamp`.

**Finding (MEDIUM):** rockinrio_official_v1 explicitly logs visitor IP in structured log.
This is not illegal per se (IPs can be logged for security) but requires RGPD notice, a
defined retention period for logs, and should not appear alongside GPS coordinates.

---

## Complete Violation Register

| ID | Severity | Codebase | File | Line | Description |
|----|----------|----------|------|------|-------------|
| V-01 | HIGH | Both | — | — | No written retention policy document exists. 7-day retention referenced in db.py comment but not implemented in Alembic migration. |
| V-02 | HIGH | Both | — | — | No DPIA document exists. Required before event operation under RGPD Article 35 (large-scale processing in public space). |
| V-03 | MEDIUM | rockinrio_official_v1 | backend/app/routers/ws_sse.py | 161–164, 228 | Client IP explicitly logged in structured application log for every SSE connection. Retention period for these logs not defined. |
| V-04 | MEDIUM | rockinrio_official_v1 | backend/app/routers/proximity.py | 132 | User GPS coordinates echoed in API response and visible in uvicorn access log query string, linking IP to physical location. |
| V-05 | MEDIUM | Both | RUNBOOK_LOCAL.md | 23 | `uvicorn app.main:app --reload` starts with default access logging enabled. No `--no-access-log` flag or log anonymization configured. Sensor IPs (non-personal) and potentially display screen IPs logged. |
| V-06 | LOW | rockinrio_official_v1 | firmware/lilygo_sniffer/rockinrio_v4.ino | 52–90 | Architecture document specifies "32-bit truncated hash only" but firmware uses raw uint64_t MAC keys in memory. Functionally private (discarded every 10s, never transmitted) but documentation is inconsistent. |
| V-07 | LOW | rockinrio_official_v1 | backend/app/models/db.py | 70 | Retention policy of "7 days" stated in code comment but not enforced. No TimescaleDB `add_retention_policy()` call exists in migrations. |

---

## Recommended Fixes

### FIX-01 (HIGH): Create and publish DPIA
Create DPIA document (draft provided as `track_03_DPIA_draft.md`) and submit to CNPD before
event operation. Display brief privacy notice at festival entry.

### FIX-02 (HIGH): Implement data retention
**rockinrio_official_v1:** Add retention policy to Alembic migration:
```python
# In upgrade():
op.execute("SELECT create_hypertable('sensor_readings', 'timestamp_utc', if_not_exists => TRUE);")
op.execute("SELECT add_retention_policy('sensor_readings', INTERVAL '7 days');")
op.execute("SELECT add_retention_policy('ir_events', INTERVAL '7 days');")
op.execute("SELECT add_retention_policy('fused_snapshots', INTERVAL '30 days');")
```
**planta-rir2026:** Add a one-paragraph retention statement to documentation (in-memory only,
cleared on restart, no persistence outside RAM).

### FIX-03 (MEDIUM): Anonymize IP logging in rockinrio_official_v1
```python
# ws_sse.py — replace lines 161-164, 228 with:
# Log only connection count, not IP
log.info("sse.connected clusters=%s", cluster_ids)
log.info("sse.disconnected clusters=%s", cluster_ids)
```
Alternatively, hash the IP before logging: `hashlib.sha256(client_ip.encode()).hexdigest()[:16]`

### FIX-04 (MEDIUM): Remove GPS echo from /nearest-wc response
```python
# proximity.py — remove "user_gps" from response:
return {
    **result,
    "timestamp": datetime.now(timezone.utc).isoformat(),
    # Remove: "user_gps": {"lat": lat, "lon": lon},
}
```
The frontend already knows the user's GPS; echoing it back in the response is unnecessary.

### FIX-05 (MEDIUM): Disable or anonymize uvicorn access log
```bash
# For both codebases, start uvicorn with:
uvicorn app.main:app --no-access-log --port 8000
```
Or configure a log filter to strip IP addresses from access log entries.

### FIX-06 (LOW): Align firmware documentation with implementation
Update `rockinrio_v4.ino` header comment to accurately describe the in-memory-discard
approach rather than referencing "32-bit truncated hash" architecture that is not implemented.

---

## Summary Scorecard

| Category | planta-rir2026 | rockinrio_official_v1 |
|----------|---------------|----------------------|
| MAC addresses | PASS | PASS |
| Camera frames | PASS | PASS |
| Firmware hashing | PARTIAL PASS | PARTIAL PASS |
| Retention policy | MISSING | MISSING (code comment only) |
| Schema PII | PASS | PASS |
| Individual tracking | PASS | PASS |
| IP in logs | MEDIUM risk | MEDIUM risk (explicit) |
| DPIA document | MISSING | MISSING |

**Overall: NO BLOCKERS. Two HIGH findings (missing DPIA + missing retention policy enforcement) must be resolved before event operation.**
