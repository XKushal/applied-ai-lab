# Chiller System Overview — Building 7

## Purpose
The Building 7 chiller plant provides chilled water for HVAC cooling loads across floors 1–12. Two YMC2 magnetic-bearing centrifugal chillers operate in lead/lag configuration with a third unit on standby.

## Normal operating parameters
- Chilled water supply temperature: 44 °F ± 1 °F
- Chilled water return temperature: 54 °F ± 2 °F
- Condenser water supply temperature: 85 °F (varies with cooling tower setpoint)
- Compressor head pressure: 130–160 psig depending on load
- Minimum load per chiller: 15% (below this, sequence to a single chiller)

## Sequencing logic
The lead chiller starts when the building automation system (BAS) detects chilled water demand. The lag chiller starts when:
- Lead chiller load exceeds 90% for more than 10 minutes, OR
- Chilled water supply temperature drifts above setpoint by more than 2 °F for more than 5 minutes.

Lead/lag rotation occurs weekly to equalize runtime hours.

## Common alarms
- **E47 — Low refrigerant pressure**: typically indicates a refrigerant leak or a stuck expansion valve. Lock out the affected chiller and dispatch a refrigeration technician.
- **E12 — High condenser temperature**: check cooling tower fan operation and condenser water flow rate. Confirm the cooling tower bypass valve is not stuck open.
- **W08 — Low chilled water flow**: differential pressure across evaporator below 4 psid. Verify primary pump operation and confirm decoupler valve position.

## Energy considerations
Each chiller draws roughly 0.55 kW per ton of cooling at design conditions. The plant feeds a primary–secondary loop; the secondary loop variable-speed pumps are controlled by differential pressure setpoint reset based on critical-zone valve position.
