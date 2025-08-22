# EnVVARCO

EnVVARCO is an open-source project designed to monitor and control electrical environmental variables, specifically for power system networks. The system leverages modern stack deployment (Docker, Docker Compose), time-series data storage, power system analysis tools, and advanced optimization algorithms for grid health and voltage management.

## Features
- Environmental variable monitoring and control
- Complete network processing from CIM files
- Automated power flow and state estimation (via updated PyVolt)
- Voltage optimization using fungal growth optimizer


## Visualization in Grafana
- Time-series storage in InfluxDB
- Dockerized deployment for ease of use
- Reactive power handling in updated PyVolt
- Optimized voltage regulation with automated shunt/capacitor switching


## Project Structure

```
main.py                     # Main application entry point
envvarco/                   # Volt-VAR control code
grafana/                    # Grafana configuration and provisioning files
influxdb/                   # InfluxDB data directories and configuration
network/                    # Network configuration scripts
ntp/                        # Network Topology Processor Module
pyvolt/                     # Updated PyVolt powerflow/state estimation module
fungal_growth_optimizer/    # Voltage control optimizer module
docker-compose.yml          # Orchestration file for all services
.gitmodules                 # Git submodules configuration
```

## Architecture & Workflow
- main.py is the main file and entry point for the application.
- The network topology processor ingests data from CIM files (standard utility network format).
- Using node-graph representations, it reconstructs the complete power network topology.
- This processed data is pushed to InfluxDB, where it’s stored for time-series analysis.
- Grafana visualizes all incoming and processed network data.
- The updated pyvolt module performs power flow analysis:
        - This version is based on the original LF Energy SOGNO-PyVolt module, but enhanced to add and subtract reactive power and to support more robust analysis and control.
        - Results are again updated in InfluxDB and visualized via Grafana.
- After running the power flow:
        - Voltages are automatically checked for over-voltage or under-voltage conditions.
        - If violations are found, the fungal_growth_optimizer module activates and resolves them by toggling shunt reactors or capacitor banks using intelligent optimization algorithms, to keep voltages within limits.
        - Post-optimization, the system updates InfluxDB again and Grafana visualizes the improved network operation.

# Getting Started

## Installation

1. Clone the repository:

```
git clone https://github.com/sede-open/EnVVARCO.git
cd EnVVARCO
```

2. Start the Stack:

```
docker-compose up -d
```

3. Access Grafana:
    Visit: http://localhost:3000
    Default login: 
        User: admin
        Password: admin

4. Access InfluxDB:
    Visit: http://localhost:8086
    Login:
        USERNAME: admin
        PASSWORD: 12345678

# PyVolt — Enhanced Version
This repository uses an updated version of PyVolt, originally developed by LF Energy SOGNO (sogno-platform/pyvolt).

## Enhancements:
- Handles both real and reactive power (modifies Q)
- Improved power flow capabilities
- Tighter integration with InfluxDB/Grafana
