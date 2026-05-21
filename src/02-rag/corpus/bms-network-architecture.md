# BMS Network Architecture

## Topology overview
The Building Management System (BMS) is a three-tier hierarchy:

1. **Field bus tier** — sensors, actuators, VAV controllers communicate over BACnet MS/TP (RS-485, 76.8 kbps) and Modbus RTU. Up to 32 devices per segment with biased termination.
2. **Supervisory tier** — building controllers (Niagara JACE 8000s) aggregate field-bus data and run local control logic. They speak BACnet/IP northbound and BACnet MS/TP southbound.
3. **Enterprise tier** — central BMS server (Niagara Supervisor) running on-premises VMs, with a Postgres time-series store for trend logs and an MQTT broker for cloud-bound telemetry forwarding.

## Naming and addressing
- BACnet device instance numbers follow the format `BBBFFNN` where BBB = building number, FF = floor, NN = device sequence on that floor.
- Modbus device addresses are flat (1–247 per segment); a tag spreadsheet maps each address to a friendly name.

## Cloud telemetry
Trend logs are forwarded via the MQTT broker to the enterprise data lake (Azure Data Lake Gen2). Topic structure: `bms/{site}/{building}/{system}/{point}`. Retention is 1 year hot, 7 years cold.

## Security posture
- All Niagara JACEs are on an isolated VLAN with no inbound internet access.
- Outbound MQTT is allowed to the cloud broker only, with mutual TLS using device certificates rotated every 90 days.
- Local credentials follow least-privilege; no shared admin accounts. Every config change is logged to the audit appliance.

## Failure modes
- **MS/TP segment offline** (fault E901) — usually caused by a missing termination resistor at one end of the trunk, or a cut cable. Bus arbitration cannot complete and all devices on the segment drop offline.
- **MQTT broker unreachable** — telemetry buffers locally on each JACE for up to 24 hours; beyond that, data loss begins. Alarm fires at 4 hours of buffered backlog.
- **Time drift** (fault W910) — controllers free-run between NTP syncs. Drift over 30s causes trend logs to misalign across systems; investigate the NTP server VM.

## Why this matters for AI integrations
Any AI assistant for building ops must:
- Use the BACnet device instance numbers (not friendly names) as the canonical IDs in tool calls.
- Read telemetry from the cloud data lake, not directly from JACEs (network policy).
- Route any actuation commands (setpoint changes, schedule overrides) through the BMS Supervisor's audited API, never directly to field devices.
