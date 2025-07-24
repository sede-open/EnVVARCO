import logging
from flask import Flask, request
from pathlib import Path
import cimpy
from pyvolt import network, nv_powerflow
from src.oma_algorithm import fungal_growth_optimizer, capacitor_objective_function, shunt_reactor_objective_function
from src.grid_exporter import export_grid_to_excel  # <-- Reuse your existing Excel export logic

# Flask setup
app = Flask(__name__)

# Logging configuration
logging.basicConfig(filename='envvarco.log', level=logging.INFO)
logging.info("🚀 Volt/VAR Control Module Started...")

@app.route("/optimize", methods=["POST"])
def optimize_powerflow():
    try:
        base_apparent_power = request.json.get("base_apparent_power", 25)
        # Load system data
        this_file_folder = Path(__file__).resolve().parent
        xml_path = this_file_folder / "network"
        xml_files = [str(xml_path / fname) for fname in [
            "Rootnet_FULL_NE_06J16h_DI.xml",
            "Rootnet_FULL_NE_06J16h_EQ.xml",
            "Rootnet_FULL_NE_06J16h_SV.xml",
            "Rootnet_FULL_NE_06J16h_TP.xml"
        ]]
        res = cimpy.cim_import(xml_files, "cgmes_v2_4_15")
        system = network.System()
        system.load_cim_data(res["topology"], base_apparent_power)
        # Volt/VAR optimization logic — copy from your alternating optimizer
        capacitor_reactive_power = {"N10": 5.0}
        shunt_reactor_reactive_power = {"N9": 8, "N6": 5, "N3": 2}
        activated_capacitors = []
        activated_reactors = []

        def classify_nodes(results_pf):
            node_voltages = {node.topology_node.name: abs(node.voltage_pu) for node in results_pf.nodes}
            under = {n: v for n, v in node_voltages.items() if v < 0.95}
            over = {n: v for n, v in node_voltages.items() if v > 1.05}
            return under, over

        for _ in range(10):
            results_pf, _ = nv_powerflow.solve(system)
            under_nodes, over_nodes = classify_nodes(results_pf)

            if not under_nodes and not over_nodes:
                logging.info("✅ All voltages within limits.")
                break

            if under_nodes:
                def cap_obj(sol):
                    return capacitor_objective_function(sol, system, capacitor_reactive_power, base_apparent_power)
                _, best_sol = fungal_growth_optimizer(
                    50, 20, [1]*len(capacitor_reactive_power), [0]*len(capacitor_reactive_power), len(capacitor_reactive_power), cap_obj
                )
                binary_solution = [1 if s >= 0.5 else 0 for s in best_sol[:-2]]
                for idx, (node_name, q_mvar) in enumerate(capacitor_reactive_power.items()):
                    if binary_solution[idx] == 1:
                        node = system.get_node_by_uuid(node_name)
                        node.reactive_power = (q_mvar / base_apparent_power)
                        activated_capacitors.append((node_name, q_mvar))

            if over_nodes:
                def reactor_obj(sol):
                    return shunt_reactor_objective_function(sol, system, shunt_reactor_reactive_power, base_apparent_power)
                _, best_sol = fungal_growth_optimizer(
                    50, 20, [1]*len(shunt_reactor_reactive_power), [0]*len(shunt_reactor_reactive_power), len(shunt_reactor_reactive_power), reactor_obj
                )
                binary_solution = [1 if s >= 0.5 else 0 for s in best_sol[:-2]]
                for idx, (node_name, q_mvar) in enumerate(shunt_reactor_reactive_power.items()):
                    if binary_solution[idx] == 1:
                        node = system.get_node_by_uuid(node_name)
                        node.reactive_power = -(q_mvar / base_apparent_power)
                        activated_reactors.append((node_name, q_mvar))

        # Final PF and export
        results_pf, _ = nv_powerflow.solve(system)
        for solved_node in results_pf.nodes:
            node = system.get_node_by_uuid(solved_node.topology_node.uuid)
            node.voltage = solved_node.voltage
            node.voltage_pu = solved_node.voltage / node.baseVoltage
            node.power = solved_node.power
            node.power_pu = solved_node.power / node.base_apparent_power

        export_grid_to_excel(system)

        return {
            "status": "success",
            "activated_capacitors": activated_capacitors,
            "activated_reactors": activated_reactors
        }, 200

    except Exception as e:
        logging.error(f"❌ Optimization failed: {e}")
        return {"status": "error", "message": str(e)}, 500

@app.route("/health", methods=["GET"])
def health_check():
    return "🟢 Volt/VAR control module is live on port 4002", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4002)