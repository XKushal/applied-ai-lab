# Fault Codes Reference — HVAC & BMS

## Format
Fault codes use the prefix `E` (error, requires manual reset) or `W` (warning, auto-clears when condition resolves). Numbers follow no semantic pattern — refer to this document.

## Chiller faults
| Code | Meaning | Typical action |
|---|---|---|
| E47 | Low refrigerant pressure | Lock out chiller; dispatch refrigeration tech to check for leaks and inspect expansion valve. |
| E12 | High condenser temperature | Verify cooling tower fans, condenser water flow rate, and tower bypass valve. |
| W08 | Low chilled water flow | Check primary pump status and decoupler valve position. |
| E22 | Compressor overcurrent trip | Likely bearing wear or refrigerant overcharge. Do not auto-reset; investigate. |
| W31 | Oil filter differential pressure high | Schedule oil filter replacement at next maintenance window. |

## Air-handling unit (AHU) faults
| Code | Meaning | Typical action |
|---|---|---|
| E101 | Supply fan VFD overcurrent | Inspect belt, bearings, and damper actuator. |
| E104 | Mixed-air temperature sensor out of range | Replace sensor or check wiring continuity to BACnet controller. |
| W210 | Filter differential pressure high | Replace pre-filters and final filters. |
| E215 | Smoke detector trip | Fan stops automatically. Investigate before reset; coordinate with fire safety. |

## Variable air volume (VAV) faults
| Code | Meaning | Typical action |
|---|---|---|
| W301 | Zone temperature sensor offline | Check Modbus or BACnet network segment for the zone. |
| W305 | Damper position feedback mismatch | Recalibrate actuator; if persistent, replace actuator. |

## BMS network faults
| Code | Meaning | Typical action |
|---|---|---|
| E901 | BACnet MS/TP segment offline | Check trunk wiring, termination resistors, and segment switch. |
| E902 | Modbus RTU CRC errors above threshold | Inspect for noise sources, verify baud rate and parity match across devices. |
| W910 | NTP time drift > 30 seconds | Re-sync controllers to building time server. |

## When to escalate
Any E-class fault on a life-safety system (smoke detection, emergency ventilation, generator transfer) is automatically escalated to facilities management on call. Do not silence these alarms without resolution.
