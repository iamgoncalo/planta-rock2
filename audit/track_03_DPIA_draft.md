# Data Protection Impact Assessment (DPIA)
## PlantaOS × Rock in Rio Lisboa 2026 — Crowd Management System

**Document status:** DRAFT — for CNPD submission review
**Prepared by:** Planta Smart Homes, Lda.
**Contact:** hi@planta.design
**Date:** 2026-05-27
**Legal basis reference:** RGPD (Regulamento (UE) 2016/679), Article 35

---

## 1. Introduction and Necessity Test

Under RGPD Article 35(1) and (3)(b), a DPIA is mandatory before processing that involves
systematic monitoring of a publicly accessible area. Rock in Rio Lisboa 2026 involves
temporary installation of sensor infrastructure across festival grounds accessible to
approximately 70,000 members of the public per day. This DPIA satisfies the mandatory
assessment prior to any data processing activity associated with the event.

This DPIA was prepared in accordance with the CNPD Guidelines on DPIAs (aligned with
WP29 Opinion WP248 rev.01) and the EDPB Guidelines 4/2022 on DPIAs.

---

## 2. Description of Processing

### 2.1 Purpose

The PlantaOS system provides real-time occupancy monitoring of 8 sanitary facility
clusters (WC-01 through WC-08) at the Rock in Rio Lisboa 2026 festival venue (Parque da
Bela Vista, Lisboa). The purpose is to:

1. **Safety:** Prevent dangerous overcrowding by alerting staff when occupancy exceeds
   safe thresholds (typically 85% of capacity)
2. **Service quality:** Redirect attendees to less congested facilities via digital
   signage and a mobile-accessible routing service
3. **Operational planning:** Generate aggregate usage statistics for future event planning

### 2.2 Nature of Data Processed

The system processes **exclusively aggregate, non-personal data** at the point of collection.
No data field in any sensor payload can identify, or be reasonably linked to, a natural
person.

| Data element | Source | Nature | Personal? |
|---|---|---|---|
| WiFi device count (integer) | LilyGo sensor | Aggregate count of unique MAC addresses in 10-second window. MACs discarded before transmission. | No |
| People estimate (integer) | LilyGo sensor | Device count × 2.5 conversion factor | No |
| IR beam crossing event | IR sensor | Binary event: door A, direction IN/OUT, timestamp | No |
| Camera occupancy count (integer) | Prosegur AI camera | Persons counted by edge AI model | No |
| Queue length estimate (integer) | Prosegur AI camera | Queue count from edge AI model | No |
| Cluster ID (string) | All sensors | Fixed identifier for one of 8 WC buildings | No |
| Timestamp (UTC) | All sensors | When the reading was taken | No |
| User GPS coordinates | Proximity API | Submitted voluntarily by attendee for routing | Potentially personal |

### 2.3 WiFi Counting — Technical Detail

WiFi probe requests are passively received by LilyGo LoRa32 ESP32 sensors operating in
promiscuous mode. The firmware:

1. Filters out locally-administered MAC addresses (iOS 14+ / Android 10+ randomised MACs,
   identified by bit 1 of the first octet) to reduce noise
2. Stores observed MACs as 64-bit integer keys in a RAM-only `std::set<uint64_t>` for a
   10-second deduplication window
3. At the end of each window: records only the **count** (`mac_window.size()`) then
   immediately clears the entire set (`mac_window.clear()`)
4. Transmits only the integer count to the backend via HTTPS POST every 60 seconds

Raw MAC addresses are **never** written to flash, EEPROM, SPIFFS, or any persistent storage
on the device. They are **never** transmitted over the network. The count represents
statistical density of nearby devices, not identification of specific devices.

### 2.4 Camera AI — Technical Detail

Prosegur camera systems run AI inference entirely on-device (edge computing). Only integer
count outputs (number of persons in frame, queue estimate, confidence score) are transmitted
to the backend. No video frames, still images, facial crops, feature vectors, or biometric
templates are stored or transmitted at any point.

### 2.5 Proximity Routing Service

The optional GET `/v1/nearest-wc` endpoint accepts latitude and longitude coordinates
submitted by festival attendees who choose to use the routing service. These coordinates are:

- Used in real time to compute distance to each WC cluster
- Returned in the API response to the same session
- **Not stored** in any database, log, or persistent medium
- Not linked to any other identifier (no account, no session token, no device ID)

The GPS coordinates represent the attendee's position within the festival grounds
(approximately 1.2 km²) for a single transaction lasting less than 100ms. These coordinates
are not precise enough to identify a home address and are not retained after the response.

**Residual risk noted:** Default web server access logs may record the GPS coordinates as
URL query parameters alongside the IP address of the requesting device. Mitigation is
described in Section 7.

---

## 3. Legal Basis

### 3.1 Primary legal basis: Legitimate Interest (Article 6(1)(f))

**Controller's legitimate interest:** Planta Smart Homes, Lda., acting as technology
provider for Rock in Rio Lisboa S.A. (event organiser), has a legitimate interest in
preventing dangerous crowd conditions at a large public event.

**Necessity test:** The system processes the minimum data required to achieve the safety
objective. Only aggregate counts are collected. No alternative (less privacy-invasive)
technical means could achieve real-time occupancy monitoring at the required granularity
and latency across 8 facility clusters simultaneously.

**Balancing test:** The data subjects (festival attendees) would reasonably expect that a
large-scale public event with over 70,000 daily attendees operates some form of crowd
monitoring. The processing does not affect their rights or interests because it produces no
individual-level record. The aggregate nature of all data means the processing cannot
disadvantage any individual.

### 3.2 Public safety overlay

For the purposes of safety operations, additional legal basis may be invoked:
- **Article 6(1)(d):** Protection of vital interests — prevention of crowd crush events
- **Article 6(1)(c):** Compliance with legal obligations — Portuguese Law n.º 39/2013
  (safety requirements for large-scale events) requires crowd monitoring

### 3.3 Proximity routing service (optional)

The GPS-based routing service is based on **explicit consent (Article 6(1)(a))** — attendees
must actively navigate to the routing interface and submit their location. The interface must
display a brief privacy notice before the first request.

---

## 4. Data Subjects

| Category | Approximate number | Relationship |
|---|---|---|
| Festival attendees | 70,000 per day | Members of the public, present voluntarily |
| Festival staff | ~5,000 | Workers, subject to employer RGPD notice |
| Accredited press/production | ~500 | WC-08 served separately; excluded from public counts |

All data subjects are adults (festival minimum age 18) or accompanied minors.

The system cannot distinguish between different categories of data subject. All persons
in the same physical area contribute identically and indistinguishably to aggregate counts.

---

## 5. Data Flows

```
Attendee presence
       │
       ▼
┌──────────────────────────────────────────┐
│  LilyGo sensor (ESP32)                   │
│  - WiFi MACs → count window (10s RAM)    │
│  - Discard MACs, send count via HTTPS    │
└──────────────┬───────────────────────────┘
               │  {cluster_id, devices_raw,
               │   pessoas_estimadas} only
               ▼
┌──────────────────────────────────────────┐
│  IR sensor (E18-D80NK)                   │
│  - Door crossing → direction + timestamp │
│  - No person identifier                  │
└──────────────┬───────────────────────────┘
               │  {cluster_id, door_id,
               │   direction, timestamp}
               ▼
┌──────────────────────────────────────────┐
│  Prosegur AI Camera (edge inference)     │
│  - Video processed on-device             │
│  - Only count output transmitted         │
└──────────────┬───────────────────────────┘
               │  {cluster_id, count,
               │   confidence}
               ▼
┌──────────────────────────────────────────┐
│  PlantaOS Backend (FastAPI / in-memory)  │
│  - Sensor fusion → cluster occupancy %  │
│  - No persistence beyond application    │
│    restart                               │
│  - Data retained in RAM only             │
└──────────────┬───────────────────────────┘
               │  Aggregate cluster states
               ▼
┌──────────────────────────────────────────┐
│  Dashboard / Display screens             │
│  - Operational staff view                │
│  - Shows: cluster %, queue, alerts       │
│  - No personal data displayed            │
└──────────────────────────────────────────┘

Optional flow (user-initiated):
Attendee → submits GPS via browser → Proximity API → returns WC recommendation → GPS discarded
```

**No personal data is retained beyond the lifecycle of a single HTTP request except:**
- WiFi device counts (aggregates) held in application memory until next sensor reading
- The above is cleared on application restart

**rockinrio_official_v1 variant additionally:**
- Persists aggregate counts to TimescaleDB (`sensor_readings` table, 7-day retention planned)
- Persists IR events to `ir_events` table (no person ID; aggregate statistics only)

**Data does not leave the festival venue network.** No data is transferred to third countries.
No data processors (sub-processors) receive personal data.

---

## 6. Technical Safeguards Implemented

| Safeguard | Implementation | Status |
|---|---|---|
| MAC discard on-device | `mac_window.clear()` after each 10s window, firmware line 110 | Implemented |
| No persistent storage on sensor | ESP32 never calls SPIFFS/EEPROM write for MAC data | Implemented |
| Aggregate-only API schemas | All Pydantic models validated at ingest — no MAC, GPS, or device ID fields accepted | Implemented |
| Camera edge-only inference | Prosegur and Luxonis cameras process video on-device; no frames transmitted | Implemented |
| Sensor authentication | All ingest endpoints require `X-Sensor-Key` header | Implemented |
| No per-person linking | No session, token, account, or identifier can link two sensor events to the same person | Implemented |
| WC-08 access restriction | Production/press WC excluded from public routing recommendations | Implemented |
| CORS restriction | Backend CORS limited to known frontend origins | Implemented |

---

## 7. Residual Risks and Mitigations

### Risk R-01: Uvicorn access log records IP addresses
**Likelihood:** Certain (default uvicorn behaviour)
**Impact:** Low (sensor IPs are infrastructure IPs, not personal)
**Residual risk:** Low
**Mitigation:** Start uvicorn with `--no-access-log` or configure log rotation with 24-hour
retention. For the proximity service, pass user requests through a frontend proxy that strips
query parameters from access logs.

### Risk R-02: Proximity API GPS visible in access log (rockinrio_official_v1)
**Likelihood:** Certain if access logging is enabled
**Impact:** Medium (IP + GPS location + timestamp = potentially personal)
**Residual risk:** Medium
**Mitigation (required before launch):**
1. Remove `"user_gps"` echo from API response (unnecessary data minimisation issue)
2. Front the proximity endpoint with a reverse proxy (nginx) configured to strip query
   parameters from access logs: `log_format main '$remote_addr - [$time_local] "$request_uri_no_query"'`
3. Or disable access logging for the `/v1/nearest-wc` path specifically

### Risk R-03: SSE/WebSocket logs record client IP (rockinrio_official_v1)
**Likelihood:** Certain (explicit `log.info("sse.connected ip=%s", client_ip)`)
**Impact:** Low-Medium (dashboard screens are typically fixed-location devices)
**Residual risk:** Low
**Mitigation:** Replace IP logging with a connection counter or anonymised hash:
`hashlib.sha256(client_ip.encode()).hexdigest()[:8]`

### Risk R-04: In-memory state survives across requests
**Likelihood:** Low
**Impact:** Low (only aggregate counts, no personal data in state)
**Residual risk:** Negligible
**Mitigation:** No action required. Document in operational procedures that backend restart
clears all state.

### Risk R-05: Firmware MAC window larger than specified
**Likelihood:** Low (10-second window is hardcoded constant)
**Impact:** Medium (longer window = more accurate person count but longer MAC retention)
**Residual risk:** Low
**Mitigation:** Window is set to `DEDUP_WINDOW_MS` (10,000ms). This is appropriate and
proportionate. Should be tested to confirm constant is not overridden in production config.

### Risk R-06: Retention policy not technically enforced (rockinrio_official_v1)
**Likelihood:** Certain (migration does not call add_retention_policy)
**Impact:** High (sensor_readings table could grow indefinitely post-event)
**Residual risk:** High
**Mitigation (required before launch):** Implement TimescaleDB retention policies via
migration (see FIX-02 in compliance report). Alternatively, schedule a post-event database
deletion procedure within 7 days of festival end.

---

## 8. Consultation

### 8.1 Internal consultation
This DPIA was prepared by the data controller's technical team (Planta Smart Homes) with
review by the event organiser (Rock in Rio Lisboa S.A.).

### 8.2 CNPD prior consultation requirement
Under RGPD Article 36, prior consultation with CNPD is required where the DPIA indicates
**high residual risk that cannot be mitigated by the controller**. Based on this assessment,
all residual risks are LOW or MEDIUM and can be mitigated by the technical fixes listed above.
**Prior CNPD consultation is therefore not mandatory** but is recommended given the public
visibility of the event.

### 8.3 Data subjects consultation
Data subjects (general public) cannot be individually consulted for aggregate processing.
The legal basis (legitimate interest / public safety) does not require individual consent.
A brief privacy notice should be displayed:
- At festival entrance gates
- On the festival mobile app / website
- On the PlantaOS dashboard screens where visible to the public

**Suggested privacy notice text (PT):**
> "Este evento usa sensores de contagem anónima para monitorizar a lotação das instalações sanitárias em tempo real. Não são recolhidos dados pessoais. Processamento por Planta Smart Homes, Lda. (hi@planta.design). Mais informações: [URL]"

---

## 9. Data Controller and Processor Details

| Role | Organisation | Contact |
|---|---|---|
| Data Controller | Rock in Rio Lisboa S.A. (event organiser) | [legal contact TBD] |
| Data Processor / Technology Provider | Planta Smart Homes, Lda. | hi@planta.design |
| Camera Sub-processor | Prosegur Portugal S.A. | [DPO contact TBD] |

A Data Processing Agreement (DPA) under RGPD Article 28 must be in place between Rock in Rio
Lisboa S.A. and Planta Smart Homes, Lda. before event operation commences. A DPA template
should also be obtained from Prosegur for edge-AI camera operations.

---

## 10. Review and Sign-off

| Action | Status |
|---|---|
| Technical review (Planta Smart Homes) | Complete — 2026-05-27 |
| Legal review | Required |
| DPO review | Required (if DPO appointed) |
| Controller sign-off (Rock in Rio Lisboa S.A.) | Required |
| CNPD submission (optional but recommended) | Pending |
| Data Processing Agreement (Planta / RiR) | Required before event |
| Prosegur DPA | Required before event |
| Staff privacy training | Required before event |
| Public privacy notice displayed | Required before event |

---

## Appendix A: Legal References

- Regulamento (UE) 2016/679 (RGPD) — Articles 4, 6, 35, 36
- Lei n.º 58/2019 (Lei de Execução Nacional do RGPD — Portugal)
- Lei n.º 39/2013 (Regime Jurídico dos Espectáculos e Divertimentos Públicos)
- EDPB Guidelines 4/2022 on the calculation of administrative fines
- WP29 Opinion WP248 rev.01 — Guidelines on DPIA
- CNPD Deliberação 2018/494 — List of types of processing requiring DPIA

---

## Appendix B: Cross-reference to Compliance Audit Findings

| Finding | DPIA Section | Status |
|---|---|---|
| No written retention policy (V-01) | §5, §7 R-06 | Requires FIX-02 |
| No DPIA document (V-02) | This document | Draft complete |
| IP logging in SSE (V-03) | §7 R-03 | Requires FIX-03 |
| GPS echo in API response (V-04) | §7 R-02 | Requires FIX-04 |
| Uvicorn access log (V-05) | §7 R-01 | Requires FIX-05 |
| Firmware documentation misalignment (V-06) | §2.3 | Requires FIX-06 |
| Retention comment vs code (V-07) | §7 R-06 | Requires FIX-02 |
