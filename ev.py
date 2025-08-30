# import random

# list_of_cell = []
# for i in range(0, 8):
#     list_of_cell.append(
#         input(f"Enter your cell type #{i+1} (e.g., lfp/nmc): ").strip().lower()
#     )
# print("\nList of entered cell types:", list_of_cell)

# cells_data = {}

# for idx, cell_type in enumerate(list_of_cell, start=1):
#     cell_key = f"cell_{idx}_{cell_type}"

#     voltage = 3.2 if cell_type == "lfp" else 3.6
#     min_voltage = 2.8 if cell_type == "lfp" else 3.2
#     max_voltage = 3.6 if cell_type == "lfp" else 4.0
#     current = 0.0
#     temp = round(random.uniform(25, 40), 1)
#     capacity = round(voltage * current, 2)

#     cells_data[cell_key] = {
#         "voltage": voltage,
#         "current": current,
#         "temp": temp,
#         "capacity": capacity,
#         "min_voltage": min_voltage,
#         "max_voltage": max_voltage,
#     }

# print("\n--- Enter current (in Amperes) for each cell ---")
# for key in cells_data:
#     try:
#         current = float(input(f"Enter current for {key}: "))
#     except ValueError:
#         print("Invalid input. Setting current to 0.")
#         current = 0.0

#     voltage = cells_data[key]["voltage"]
#     cells_data[key]["current"] = current
#     cells_data[key]["capacity"] = round(voltage * current, 2)


# print("\n--- Updated Cell Data ---")
# for key, values in cells_data.items():
#     print(f"{key}: {values}")

#! =================================================================================================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import random
from datetime import datetime, timedelta
import io

# Page configuration
st.set_page_config(
    page_title="Battery Cell Monitoring System",
    page_icon="🔋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Enhanced Custom CSS
st.markdown(
    """
<style>
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
        color: #212529;
    }
    .warning-card {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        color: #856404;
    }
    .danger-card {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        color: #721c24;
    }
    .success-card {
        background-color: #d1edff;
        border-left: 4px solid #28a745;
        color: #155724;
    }
    .info-card {
        background-color: #d1ecf1;
        border-left: 4px solid #17a2b8;
        color: #0c5460;
    }
    .alert-critical {
        background-color: #f8d7da;
        border: 2px solid #dc3545;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        color: #721c24 !important;
    }
    .alert-warning {
        background-color: #fff3cd;
        border: 2px solid #ffc107;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        color: #856404 !important;
    }
    .alert-info {
        background-color: #d1ecf1;
        border: 2px solid #17a2b8;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        color: #0c5460 !important;
    }
    .cell-status-healthy {
        background: linear-gradient(90deg, #28a745, #34ce57);
        color: white;
        padding: 10px;
        border-radius: 8px;
        text-align: center;
        font-weight: bold;
    }
    .cell-status-warning {
        background: linear-gradient(90deg, #ffc107, #ffcd39);
        color: #212529;
        padding: 10px;
        border-radius: 8px;
        text-align: center;
        font-weight: bold;
    }
    .cell-status-critical {
        background: linear-gradient(90deg, #dc3545, #e55368);
        color: white;
        padding: 10px;
        border-radius: 8px;
        text-align: center;
        font-weight: bold;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Initialize session state
if "cells_data" not in st.session_state:
    st.session_state.cells_data = {}
if "historical_data" not in st.session_state:
    st.session_state.historical_data = []
if "last_update" not in st.session_state:
    st.session_state.last_update = datetime.now()
if "alerts" not in st.session_state:
    st.session_state.alerts = []

# Generate some sample historical data for better visualization
if "sample_data_generated" not in st.session_state:
    st.session_state.sample_data_generated = False


def generate_sample_data():
    """Generate sample historical data for demonstration"""
    if not st.session_state.sample_data_generated and st.session_state.cells_data:
        base_time = datetime.now() - timedelta(hours=2)

        for i in range(50):  # Generate 50 historical data points
            timestamp = base_time + timedelta(minutes=i * 2)
            record = {"timestamp": timestamp}

            for cell_id, cell_data in st.session_state.cells_data.items():
                # Add some realistic variation to the data
                voltage_noise = random.uniform(-0.1, 0.1)
                current_noise = random.uniform(-0.5, 0.5)
                temp_noise = random.uniform(-2, 2)

                record[f"{cell_id}_voltage"] = max(
                    2.5, min(4.2, cell_data["voltage"] + voltage_noise)
                )
                record[f"{cell_id}_current"] = cell_data["current"] + current_noise
                record[f"{cell_id}_temp"] = max(
                    15, min(60, cell_data["temp"] + temp_noise)
                )
                record[f"{cell_id}_power"] = (
                    record[f"{cell_id}_voltage"] * record[f"{cell_id}_current"]
                )

            st.session_state.historical_data.append(record)

        st.session_state.sample_data_generated = True


# Cell specifications
CELL_SPECS = {
    "lfp": {
        "name": "Lithium Iron Phosphate (LFP)",
        "nominal_voltage": 3.2,
        "min_voltage": 2.8,
        "max_voltage": 3.6,
        "max_temp": 60,
        "min_temp": -20,
        "color": "#2E8B57",
    },
    "nmc": {
        "name": "Nickel Manganese Cobalt (NMC)",
        "nominal_voltage": 3.6,
        "min_voltage": 3.0,
        "max_voltage": 4.2,
        "max_temp": 45,
        "min_temp": -10,
        "color": "#FF6347",
    },
    "lto": {
        "name": "Lithium Titanate (LTO)",
        "nominal_voltage": 2.4,
        "min_voltage": 1.5,
        "max_voltage": 2.8,
        "max_temp": 55,
        "min_temp": -30,
        "color": "#4169E1",
    },
    "nca": {
        "name": "Nickel Cobalt Aluminum (NCA)",
        "nominal_voltage": 3.6,
        "min_voltage": 3.0,
        "max_voltage": 4.2,
        "max_temp": 45,
        "min_temp": -10,
        "color": "#FF1493",
    },
}


def get_cell_status(cell_data, cell_type):
    """Determine cell status based on operating parameters"""
    specs = CELL_SPECS[cell_type]
    voltage = cell_data["voltage"]
    temp = cell_data["temp"]

    # Check voltage range
    if voltage < specs["min_voltage"] * 0.95 or voltage > specs["max_voltage"] * 1.05:
        return "critical"
    elif voltage < specs["min_voltage"] * 1.05 or voltage > specs["max_voltage"] * 0.95:
        return "warning"

    # Check temperature range
    if temp < specs["min_temp"] or temp > specs["max_temp"]:
        return "critical"
    elif temp < specs["min_temp"] + 5 or temp > specs["max_temp"] - 5:
        return "warning"

    return "healthy"


def calculate_soc(voltage, cell_type):
    """Calculate State of Charge based on voltage"""
    specs = CELL_SPECS[cell_type]
    min_v = specs["min_voltage"]
    max_v = specs["max_voltage"]

    soc = ((voltage - min_v) / (max_v - min_v)) * 100
    return max(0, min(100, soc))


def add_alert(message, alert_type="info"):
    """Add alert to session state"""
    alert = {"timestamp": datetime.now(), "message": message, "type": alert_type}
    st.session_state.alerts.insert(0, alert)
    # Keep only last 10 alerts
    st.session_state.alerts = st.session_state.alerts[:10]


def update_historical_data():
    """Update historical data with current cell states"""
    if st.session_state.cells_data:
        record = {
            "timestamp": datetime.now(),
            **{
                f"{cell_id}_{param}": value
                for cell_id, cell_data in st.session_state.cells_data.items()
                for param, value in cell_data.items()
            },
        }
        st.session_state.historical_data.append(record)
        # Keep only last 100 records
        st.session_state.historical_data = st.session_state.historical_data[-100:]


def create_cell_wise_eda():
    """Create comprehensive EDA charts for each cell"""
    if not st.session_state.cells_data:
        return

    generate_sample_data()  # Generate sample data if not exists

    for cell_id, cell_data in st.session_state.cells_data.items():
        cell_type = cell_id.split("_")[2]
        cell_name = cell_id.replace("_", " ").title()

        st.markdown(f"## 📊 {cell_name} - Complete Analysis")

        # Current Status Overview
        col1, col2, col3, col4 = st.columns(4)

        status = get_cell_status(cell_data, cell_type)
        soc = calculate_soc(cell_data["voltage"], cell_type)

        with col1:
            status_class = f"cell-status-{status}"
            st.markdown(
                f"""
            <div class="{status_class}">
                Status: {status.upper()}
            </div>
            """,
                unsafe_allow_html=True,
            )

        with col2:
            st.metric("State of Charge", f"{soc:.1f}%")

        with col3:
            st.metric("Efficiency", f"{random.uniform(85, 98):.1f}%")

        with col4:
            st.metric("Health Score", f"{random.uniform(90, 100):.1f}%")

        # Detailed metrics in columns
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("### ⚡ Electrical Parameters")
            st.metric(
                "Voltage",
                f"{cell_data['voltage']:.3f} V",
                f"{cell_data['voltage'] - CELL_SPECS[cell_type]['nominal_voltage']:.3f}",
            )
            st.metric("Current", f"{cell_data['current']:.3f} A")
            st.metric("Power", f"{cell_data['power']:.3f} W")
            st.metric("Internal Resistance", f"{random.uniform(10, 50):.1f} mΩ")

        with col2:
            st.markdown("### 🌡️ Thermal Parameters")
            st.metric(
                "Temperature",
                f"{cell_data['temp']:.1f} °C",
                f"{cell_data['temp'] - 25:.1f}",
            )
            st.metric("Heat Generation", f"{abs(cell_data['power']) * 0.05:.2f} W")
            st.metric("Thermal Efficiency", f"{random.uniform(92, 99):.1f}%")

        with col3:
            st.markdown("### 📈 Performance Metrics")
            specs = CELL_SPECS[cell_type]
            voltage_util = (cell_data["voltage"] / specs["max_voltage"]) * 100
            st.metric("Voltage Utilization", f"{voltage_util:.1f}%")
            st.metric("Capacity Retention", f"{random.uniform(85, 98):.1f}%")
            st.metric("Cycle Count", f"{random.randint(100, 1000)}")

        # Historical Analysis Charts
        if st.session_state.historical_data:
            df = pd.DataFrame(st.session_state.historical_data)

            # Multi-parameter time series
            fig_multi = make_subplots(
                rows=2,
                cols=2,
                subplot_titles=(
                    f"{cell_name} - Voltage Over Time",
                    f"{cell_name} - Current Over Time",
                    f"{cell_name} - Temperature Over Time",
                    f"{cell_name} - Power Over Time",
                ),
                specs=[
                    [{"secondary_y": False}, {"secondary_y": False}],
                    [{"secondary_y": False}, {"secondary_y": False}],
                ],
            )

            voltage_col = f"{cell_id}_voltage"
            current_col = f"{cell_id}_current"
            temp_col = f"{cell_id}_temp"
            power_col = f"{cell_id}_power"

            if voltage_col in df.columns:
                fig_multi.add_trace(
                    go.Scatter(
                        x=df["timestamp"],
                        y=df[voltage_col],
                        name="Voltage",
                        line=dict(color="blue", width=2),
                    ),
                    row=1,
                    col=1,
                )

            if current_col in df.columns:
                fig_multi.add_trace(
                    go.Scatter(
                        x=df["timestamp"],
                        y=df[current_col],
                        name="Current",
                        line=dict(color="red", width=2),
                    ),
                    row=1,
                    col=2,
                )

            if temp_col in df.columns:
                fig_multi.add_trace(
                    go.Scatter(
                        x=df["timestamp"],
                        y=df[temp_col],
                        name="Temperature",
                        line=dict(color="orange", width=2),
                    ),
                    row=2,
                    col=1,
                )

            if power_col in df.columns:
                fig_multi.add_trace(
                    go.Scatter(
                        x=df["timestamp"],
                        y=df[power_col],
                        name="Power",
                        line=dict(color="green", width=2),
                    ),
                    row=2,
                    col=2,
                )

            fig_multi.update_layout(height=600, showlegend=False)
            fig_multi.update_xaxes(title_text="Time")
            fig_multi.update_yaxes(title_text="Voltage (V)", row=1, col=1)
            fig_multi.update_yaxes(title_text="Current (A)", row=1, col=2)
            fig_multi.update_yaxes(title_text="Temperature (°C)", row=2, col=1)
            fig_multi.update_yaxes(title_text="Power (W)", row=2, col=2)

            st.plotly_chart(fig_multi, use_container_width=True)

            # Distribution Analysis
            col1, col2 = st.columns(2)

            with col1:
                if voltage_col in df.columns:
                    fig_hist = px.histogram(
                        df,
                        x=voltage_col,
                        nbins=20,
                        title=f"{cell_name} - Voltage Distribution",
                        color_discrete_sequence=["#1f77b4"],
                    )
                    fig_hist.add_vline(
                        x=cell_data["voltage"],
                        line_dash="dash",
                        line_color="red",
                        annotation_text="Current",
                    )
                    st.plotly_chart(fig_hist, use_container_width=True)

            with col2:
                if temp_col in df.columns:
                    fig_temp_hist = px.histogram(
                        df,
                        x=temp_col,
                        nbins=20,
                        title=f"{cell_name} - Temperature Distribution",
                        color_discrete_sequence=["#ff7f0e"],
                    )
                    fig_temp_hist.add_vline(
                        x=cell_data["temp"],
                        line_dash="dash",
                        line_color="red",
                        annotation_text="Current",
                    )
                    st.plotly_chart(fig_temp_hist, use_container_width=True)

            # Statistical Summary Table
            st.markdown("### 📊 Statistical Summary")

            stats_data = []
            for param in ["voltage", "current", "temp", "power"]:
                col_name = f"{cell_id}_{param}"
                if col_name in df.columns:
                    data = df[col_name]
                    stats_data.append(
                        {
                            "Parameter": param.title(),
                            "Current": f"{cell_data[param]:.3f}",
                            "Mean": f"{data.mean():.3f}",
                            "Std Dev": f"{data.std():.3f}",
                            "Min": f"{data.min():.3f}",
                            "Max": f"{data.max():.3f}",
                            "Range": f"{data.max() - data.min():.3f}",
                        }
                    )

            if stats_data:
                stats_df = pd.DataFrame(stats_data)
                st.dataframe(stats_df, use_container_width=True)

            # Correlation Analysis
            st.markdown("### 🔗 Parameter Correlations")

            cell_columns = [
                col
                for col in df.columns
                if col.startswith(cell_id) and col != f"{cell_id}_timestamp"
            ]
            if len(cell_columns) > 1:
                corr_data = df[cell_columns].corr()

                fig_corr = px.imshow(
                    corr_data,
                    title=f"{cell_name} - Parameter Correlation Matrix",
                    color_continuous_scale="RdBu_r",
                    aspect="auto",
                )
                fig_corr.update_layout(height=400)
                st.plotly_chart(fig_corr, use_container_width=True)

        st.markdown("---")


# Sidebar
with st.sidebar:
    st.title("🔋 Battery Monitor")

    page = st.selectbox(
        "Navigation",
        [
            "Dashboard",
            "Cell Configuration",
            "Real-time Monitoring",
            "Cell-wise EDA",
            "Alerts & Safety",
            "Data Export",
        ],
    )

    st.markdown("---")

    # System Status
    if st.session_state.cells_data:
        total_cells = len(st.session_state.cells_data)
        healthy_cells = sum(
            1
            for cell_id, cell_data in st.session_state.cells_data.items()
            if get_cell_status(cell_data, cell_id.split("_")[2]) == "healthy"
        )

        st.metric("Total Cells", total_cells)
        st.metric("Healthy Cells", f"{healthy_cells}/{total_cells}")

        if total_cells > 0:
            health_percentage = (healthy_cells / total_cells) * 100
            if health_percentage == 100:
                st.success("All systems operational")
            elif health_percentage >= 75:
                st.warning("Some cells need attention")
            else:
                st.error("Critical system status")

# Main content based on selected page
if page == "Dashboard":
    st.title("🔋 Battery Management System Dashboard")

    if not st.session_state.cells_data:
        st.info(
            "👆 Please configure your cells first using the 'Cell Configuration' page."
        )
    else:
        # System Overview Metrics
        col1, col2, col3, col4 = st.columns(4)

        total_power = sum(
            cell["power"] for cell in st.session_state.cells_data.values()
        )
        avg_temp = np.mean(
            [cell["temp"] for cell in st.session_state.cells_data.values()]
        )
        avg_voltage = np.mean(
            [cell["voltage"] for cell in st.session_state.cells_data.values()]
        )
        total_current = sum(
            cell["current"] for cell in st.session_state.cells_data.values()
        )

        with col1:
            st.metric("Total Power", f"{total_power:.2f} W", f"{total_power-50:.1f}")
        with col2:
            st.metric("Average Temperature", f"{avg_temp:.1f}°C", f"{avg_temp-35:.1f}")
        with col3:
            st.metric("Average Voltage", f"{avg_voltage:.2f} V")
        with col4:
            st.metric("Total Current", f"{total_current:.2f} A")

        # Generate sample data for charts
        generate_sample_data()

        # System Overview Charts
        st.subheader("System Overview Charts")

        col1, col2 = st.columns(2)

        with col1:
            # Enhanced voltage comparison with status colors
            cell_names = list(st.session_state.cells_data.keys())
            voltages = [
                st.session_state.cells_data[cell]["voltage"] for cell in cell_names
            ]
            colors = [CELL_SPECS[cell.split("_")[2]]["color"] for cell in cell_names]

            fig_voltage = go.Figure(
                data=go.Bar(
                    x=cell_names, y=voltages, marker_color=colors, name="Voltage"
                )
            )
            fig_voltage.update_layout(
                title="Cell Voltages Comparison",
                yaxis_title="Voltage (V)",
                xaxis_tickangle=-45,
            )
            st.plotly_chart(fig_voltage, use_container_width=True)

        with col2:
            # Enhanced temperature comparison
            temps = [st.session_state.cells_data[cell]["temp"] for cell in cell_names]

            fig_temp = go.Figure(
                data=go.Bar(
                    x=cell_names, y=temps, marker_color=colors, name="Temperature"
                )
            )
            fig_temp.update_layout(
                title="Cell Temperatures Comparison",
                yaxis_title="Temperature (°C)",
                xaxis_tickangle=-45,
            )
            st.plotly_chart(fig_temp, use_container_width=True)

        # System Power Distribution
        st.subheader("Power Distribution Analysis")

        powers = [st.session_state.cells_data[cell]["power"] for cell in cell_names]

        col1, col2 = st.columns(2)

        with col1:
            fig_power_pie = px.pie(
                values=powers,
                names=cell_names,
                title="Power Distribution Across Cells",
                color_discrete_sequence=px.colors.qualitative.Set3,
            )
            st.plotly_chart(fig_power_pie, use_container_width=True)

        with col2:
            fig_power_bar = go.Figure(
                data=go.Bar(x=cell_names, y=powers, marker_color=colors, name="Power")
            )
            fig_power_bar.update_layout(
                title="Individual Cell Power Output",
                yaxis_title="Power (W)",
                xaxis_tickangle=-45,
            )
            st.plotly_chart(fig_power_bar, use_container_width=True)

        # Cell Status Grid
        st.subheader("Cell Status Overview")

        cols = st.columns(4)
        for idx, (cell_id, cell_data) in enumerate(st.session_state.cells_data.items()):
            col_idx = idx % 4
            cell_type = cell_id.split("_")[2]
            status = get_cell_status(cell_data, cell_type)
            soc = calculate_soc(cell_data["voltage"], cell_type)

            with cols[col_idx]:
                status_class = f"cell-status-{status}"
                st.markdown(
                    f"""
                <div class="{status_class}">
                    <h4>{cell_id.replace('_', ' ').title()}</h4>
                    <p><strong>Voltage:</strong> {cell_data['voltage']:.2f}V</p>
                    <p><strong>Current:</strong> {cell_data['current']:.2f}A</p>
                    <p><strong>Temperature:</strong> {cell_data['temp']:.1f}°C</p>
                    <p><strong>SOC:</strong> {soc:.1f}%</p>
                    <p><strong>Power:</strong> {cell_data['power']:.2f}W</p>
                </div>
                """,
                    unsafe_allow_html=True,
                )

elif page == "Cell Configuration":
    st.title("⚙️ Cell Configuration")

    st.info(
        "Configure your 8 battery cells by selecting their types and setting initial parameters."
    )

    # Preset configurations
    st.subheader("Quick Setup Presets")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("All LFP Pack", use_container_width=True):
            for i in range(8):
                cell_id = f"cell_{i+1}_lfp"
                specs = CELL_SPECS["lfp"]
                st.session_state.cells_data[cell_id] = {
                    "voltage": specs["nominal_voltage"],
                    "current": 0.0,
                    "temp": round(random.uniform(25, 35), 1),
                    "power": 0.0,
                    "min_voltage": specs["min_voltage"],
                    "max_voltage": specs["max_voltage"],
                }
            st.success("LFP pack configured!")

    with col2:
        if st.button("All NMC Pack", use_container_width=True):
            for i in range(8):
                cell_id = f"cell_{i+1}_nmc"
                specs = CELL_SPECS["nmc"]
                st.session_state.cells_data[cell_id] = {
                    "voltage": specs["nominal_voltage"],
                    "current": 0.0,
                    "temp": round(random.uniform(25, 35), 1),
                    "power": 0.0,
                    "min_voltage": specs["min_voltage"],
                    "max_voltage": specs["max_voltage"],
                }
            st.success("NMC pack configured!")

    with col3:
        if st.button("Mixed Pack 1", use_container_width=True):
            types = ["lfp", "lfp", "lfp", "lfp", "nmc", "nmc", "nmc", "nmc"]
            for i, cell_type in enumerate(types):
                cell_id = f"cell_{i+1}_{cell_type}"
                specs = CELL_SPECS[cell_type]
                st.session_state.cells_data[cell_id] = {
                    "voltage": specs["nominal_voltage"],
                    "current": 0.0,
                    "temp": round(random.uniform(25, 35), 1),
                    "power": 0.0,
                    "min_voltage": specs["min_voltage"],
                    "max_voltage": specs["max_voltage"],
                }
            st.success("Mixed pack configured!")

    with col4:
        if st.button("Clear All", use_container_width=True):
            st.session_state.cells_data = {}
            st.session_state.sample_data_generated = False
            st.success("All cells cleared!")

    st.markdown("---")

    # Individual cell configuration
    st.subheader("Individual Cell Configuration")

    cols = st.columns(2)

    for i in range(8):
        col_idx = i % 2

        with cols[col_idx]:
            st.markdown(f"**Cell {i+1}**")

            cell_type = st.selectbox(
                f"Cell {i+1} Type",
                options=list(CELL_SPECS.keys()),
                format_func=lambda x: CELL_SPECS[x]["name"],
                key=f"cell_type_{i}",
                index=0,
            )

            specs = CELL_SPECS[cell_type]
            cell_id = f"cell_{i+1}_{cell_type}"

            # Initialize or update cell data
            if cell_id not in st.session_state.cells_data:
                st.session_state.cells_data[cell_id] = {
                    "voltage": specs["nominal_voltage"],
                    "current": 0.0,
                    "temp": round(random.uniform(25, 35), 1),
                    "power": 0.0,
                    "min_voltage": specs["min_voltage"],
                    "max_voltage": specs["max_voltage"],
                }

            # Remove old cell data if type changed
            old_cells = [
                k
                for k in st.session_state.cells_data.keys()
                if k.startswith(f"cell_{i+1}_") and k != cell_id
            ]
            for old_cell in old_cells:
                del st.session_state.cells_data[old_cell]

            col_a, col_b = st.columns(2)
            with col_a:
                st.info(f"Voltage: {specs['min_voltage']}-{specs['max_voltage']}V")
            with col_b:
                st.info(f"Temp: {specs['min_temp']}°C to {specs['max_temp']}°C")

            st.markdown("---")

elif page == "Real-time Monitoring":
    st.title("📊 Real-time Monitoring")

    if not st.session_state.cells_data:
        st.warning("Please configure cells first in the 'Cell Configuration' page.")
    else:
        # Manual refresh button
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🔄 Refresh Data", use_container_width=True):
                st.success("Data refreshed!")

        with col2:
            if st.button("📝 Log Current State", use_container_width=True):
                update_historical_data()
                st.success("Data logged!")

        # Current input section
        st.subheader("Current Input Controls")

        cols = st.columns(2)

        for idx, (cell_id, cell_data) in enumerate(st.session_state.cells_data.items()):
            col_idx = idx % 2

            with cols[col_idx]:
                st.markdown(f"**{cell_id.replace('_', ' ').title()}**")

                current = st.slider(
                    f"Current (A)",
                    min_value=-10.0,
                    max_value=10.0,
                    value=cell_data["current"],
                    step=0.1,
                    key=f"current_{cell_id}",
                )

                # Update cell data
                st.session_state.cells_data[cell_id]["current"] = current
                st.session_state.cells_data[cell_id]["power"] = round(
                    cell_data["voltage"] * current, 2
                )

                # Simulate voltage drop under load
                base_voltage = CELL_SPECS[cell_id.split("_")[2]]["nominal_voltage"]
                voltage_drop = abs(current) * 0.05  # Simple internal resistance model
                new_voltage = base_voltage - voltage_drop
                st.session_state.cells_data[cell_id]["voltage"] = round(new_voltage, 2)

                # Display current values
                st.metric(
                    "Power", f"{st.session_state.cells_data[cell_id]['power']:.2f} W"
                )
                st.metric("Voltage", f"{new_voltage:.2f} V")

        st.markdown("---")

        # Real-time gauges
        st.subheader("Live SOC Gauges")

        gauge_cols = st.columns(4)
        cell_items = list(st.session_state.cells_data.items())

        for i in range(min(4, len(cell_items))):
            cell_id, cell_data = cell_items[i]
            cell_type = cell_id.split("_")[2]
            soc = calculate_soc(cell_data["voltage"], cell_type)

            with gauge_cols[i]:
                fig_gauge = go.Figure(
                    go.Indicator(
                        mode="gauge+number+delta",
                        value=soc,
                        domain={"x": [0, 1], "y": [0, 1]},
                        title={"text": f"{cell_id}<br>SOC (%)"},
                        delta={"reference": 80},
                        gauge={
                            "axis": {"range": [None, 100]},
                            "bar": {"color": "darkblue"},
                            "steps": [
                                {"range": [0, 25], "color": "lightgray"},
                                {"range": [25, 50], "color": "yellow"},
                                {"range": [50, 85], "color": "lightgreen"},
                                {"range": [85, 100], "color": "green"},
                            ],
                            "threshold": {
                                "line": {"color": "red", "width": 4},
                                "thickness": 0.75,
                                "value": 90,
                            },
                        },
                    )
                )

                fig_gauge.update_layout(height=300)
                st.plotly_chart(fig_gauge, use_container_width=True)

        # More gauges for remaining cells if more than 4
        if len(cell_items) > 4:
            gauge_cols2 = st.columns(4)
            for i in range(4, min(8, len(cell_items))):
                cell_id, cell_data = cell_items[i]
                cell_type = cell_id.split("_")[2]
                soc = calculate_soc(cell_data["voltage"], cell_type)

                with gauge_cols2[i - 4]:
                    fig_gauge = go.Figure(
                        go.Indicator(
                            mode="gauge+number+delta",
                            value=soc,
                            domain={"x": [0, 1], "y": [0, 1]},
                            title={"text": f"{cell_id}<br>SOC (%)"},
                            delta={"reference": 80},
                            gauge={
                                "axis": {"range": [None, 100]},
                                "bar": {"color": "darkblue"},
                                "steps": [
                                    {"range": [0, 25], "color": "lightgray"},
                                    {"range": [25, 50], "color": "yellow"},
                                    {"range": [50, 85], "color": "lightgreen"},
                                    {"range": [85, 100], "color": "green"},
                                ],
                                "threshold": {
                                    "line": {"color": "red", "width": 4},
                                    "thickness": 0.75,
                                    "value": 90,
                                },
                            },
                        )
                    )

                    fig_gauge.update_layout(height=300)
                    st.plotly_chart(fig_gauge, use_container_width=True)

        # Temperature simulation
        st.subheader("Environmental Simulation")

        temp_col1, temp_col2, temp_col3 = st.columns(3)

        with temp_col1:
            if st.button("🔥 Simulate Heat Up", use_container_width=True):
                for cell_id in st.session_state.cells_data:
                    current_temp = st.session_state.cells_data[cell_id]["temp"]
                    new_temp = min(current_temp + random.uniform(5, 15), 70)
                    st.session_state.cells_data[cell_id]["temp"] = round(new_temp, 1)
                    if new_temp > 45:
                        add_alert(
                            f"{cell_id} temperature high: {new_temp:.1f}°C", "warning"
                        )
                st.success("Temperature increased!")

        with temp_col2:
            if st.button("❄️ Simulate Cool Down", use_container_width=True):
                for cell_id in st.session_state.cells_data:
                    current_temp = st.session_state.cells_data[cell_id]["temp"]
                    new_temp = max(current_temp - random.uniform(5, 10), 15)
                    st.session_state.cells_data[cell_id]["temp"] = round(new_temp, 1)
                st.success("Temperature decreased!")

        with temp_col3:
            if st.button("🎲 Random Load Test", use_container_width=True):
                for cell_id in st.session_state.cells_data:
                    random_current = random.uniform(-5, 5)
                    st.session_state.cells_data[cell_id]["current"] = round(
                        random_current, 2
                    )
                    st.session_state.cells_data[cell_id]["power"] = round(
                        st.session_state.cells_data[cell_id]["voltage"]
                        * random_current,
                        2,
                    )
                st.success("Random loads applied!")

elif page == "Cell-wise EDA":
    st.title("🔬 Cell-wise Exploratory Data Analysis")

    if not st.session_state.cells_data:
        st.warning("Please configure cells first in the 'Cell Configuration' page.")
    else:
        create_cell_wise_eda()

elif page == "Alerts & Safety":
    st.title("🚨 Alerts & Safety Monitoring")

    # Real-time safety checks
    st.subheader("Safety Status Dashboard")

    if st.session_state.cells_data:
        safety_issues = []

        for cell_id, cell_data in st.session_state.cells_data.items():
            cell_type = cell_id.split("_")[2]
            specs = CELL_SPECS[cell_type]

            # Check voltage limits
            if cell_data["voltage"] > specs["max_voltage"]:
                safety_issues.append(
                    {
                        "Cell": cell_id,
                        "Issue": "Overvoltage",
                        "Value": f"{cell_data['voltage']:.2f}V",
                        "Limit": f"{specs['max_voltage']}V",
                        "Severity": "critical",
                    }
                )
            elif cell_data["voltage"] < specs["min_voltage"]:
                safety_issues.append(
                    {
                        "Cell": cell_id,
                        "Issue": "Undervoltage",
                        "Value": f"{cell_data['voltage']:.2f}V",
                        "Limit": f"{specs['min_voltage']}V",
                        "Severity": "critical",
                    }
                )

            # Check temperature limits
            if cell_data["temp"] > specs["max_temp"]:
                safety_issues.append(
                    {
                        "Cell": cell_id,
                        "Issue": "Overtemperature",
                        "Value": f"{cell_data['temp']:.1f}°C",
                        "Limit": f"{specs['max_temp']}°C",
                        "Severity": "critical",
                    }
                )
            elif cell_data["temp"] < specs["min_temp"]:
                safety_issues.append(
                    {
                        "Cell": cell_id,
                        "Issue": "Undertemperature",
                        "Value": f"{cell_data['temp']:.1f}°C",
                        "Limit": f"{specs['min_temp']}°C",
                        "Severity": "warning",
                    }
                )

        if safety_issues:
            st.error(f"🚨 {len(safety_issues)} safety issue(s) detected!")

            for issue in safety_issues:
                severity_icon = {"critical": "🔴", "warning": "🟡", "info": "🔵"}
                alert_class = f"alert-{issue['Severity']}"

                st.markdown(
                    f"""
                <div class="{alert_class}">
                    <strong>{severity_icon[issue['Severity']]} {issue['Severity'].upper()}: {issue['Issue']}</strong><br><br>
                    <strong>Cell:</strong> {issue['Cell']}<br>
                    <strong>Current Value:</strong> {issue['Value']}<br>
                    <strong>Safety Limit:</strong> {issue['Limit']}
                </div>
                """,
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                """
            <div class="alert-info">
                <strong>✅ ALL SYSTEMS NORMAL</strong><br><br>
                All cells are operating within safe parameters.
            </div>
            """,
                unsafe_allow_html=True,
            )

        # Safety thresholds configuration
        st.subheader("Safety Thresholds Configuration")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Temperature Monitoring**")
            temp_alert_high = st.slider("High Temperature Alert (°C)", 40, 70, 50)
            temp_alert_low = st.slider("Low Temperature Alert (°C)", -20, 10, 0)

        with col2:
            st.markdown("**Voltage Monitoring**")
            voltage_tolerance = st.slider("Voltage Tolerance (%)", 1, 10, 5)
            current_limit = st.slider("Current Limit (A)", 5, 20, 10)

        # Emergency actions
        st.subheader("Emergency Actions")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🛑 Emergency Stop", use_container_width=True):
                for cell_id in st.session_state.cells_data:
                    st.session_state.cells_data[cell_id]["current"] = 0.0
                    st.session_state.cells_data[cell_id]["power"] = 0.0
                add_alert(
                    "Emergency stop activated - all currents set to zero", "critical"
                )
                st.success("Emergency stop activated!")

        with col2:
            if st.button("⚖️ Balance Cells", use_container_width=True):
                if st.session_state.cells_data:
                    # Simple balancing - bring all voltages to average
                    voltages = [
                        cell["voltage"] for cell in st.session_state.cells_data.values()
                    ]
                    avg_voltage = np.mean(voltages)

                    for cell_id in st.session_state.cells_data:
                        cell_type = cell_id.split("_")[2]
                        specs = CELL_SPECS[cell_type]
                        balanced_voltage = min(avg_voltage, specs["max_voltage"])
                        balanced_voltage = max(balanced_voltage, specs["min_voltage"])
                        st.session_state.cells_data[cell_id]["voltage"] = round(
                            balanced_voltage, 2
                        )

                    add_alert("Cell balancing completed", "info")
                    st.success("Cell balancing completed!")

        with col3:
            if st.button("🔄 Reset Alerts", use_container_width=True):
                st.session_state.alerts = []
                st.success("Alert history cleared!")

    # Alert history
    st.subheader("Alert History")

    if st.session_state.alerts:
        for alert in st.session_state.alerts:
            alert_class = f"alert-{alert['type']}"
            severity_icons = {"critical": "🔴", "warning": "🟡", "info": "🔵"}

            st.markdown(
                f"""
            <div class="{alert_class}">
                <strong>{severity_icons.get(alert['type'], '🔵')} {alert['timestamp'].strftime('%H:%M:%S')}</strong><br>
                {alert['message']}
            </div>
            """,
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            """
        <div class="alert-info">
            <strong>📋 NO ALERTS</strong><br>
            No alerts in history. System operating normally.
        </div>
        """,
            unsafe_allow_html=True,
        )

elif page == "Data Export":
    st.title("💾 Data Export & Management")

    # Export current state
    st.subheader("Export Current Cell Data")

    if st.session_state.cells_data:
        # Prepare current data for export
        export_data = []
        for cell_id, cell_data in st.session_state.cells_data.items():
            cell_type = cell_id.split("_")[2]
            soc = calculate_soc(cell_data["voltage"], cell_type)
            status = get_cell_status(cell_data, cell_type)

            export_data.append(
                {
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Cell_ID": cell_id,
                    "Cell_Type": cell_type.upper(),
                    "Voltage_V": cell_data["voltage"],
                    "Current_A": cell_data["current"],
                    "Power_W": cell_data["power"],
                    "Temperature_C": cell_data["temp"],
                    "SOC_Percent": round(soc, 1),
                    "Status": status,
                    "Min_Voltage": cell_data["min_voltage"],
                    "Max_Voltage": cell_data["max_voltage"],
                }
            )

        current_df = pd.DataFrame(export_data)

        col1, col2 = st.columns(2)

        with col1:
            csv = current_df.to_csv(index=False)
            st.download_button(
                label="📄 Download Current State (CSV)",
                data=csv,
                file_name=f"battery_status_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True,
            )

        with col2:
            # Excel export
            buffer = io.BytesIO()
            try:
                with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                    current_df.to_excel(
                        writer, sheet_name="Current_Status", index=False
                    )

                    # Add historical data if available
                    if st.session_state.historical_data:
                        historical_df = pd.DataFrame(st.session_state.historical_data)
                        historical_df.to_excel(
                            writer, sheet_name="Historical_Data", index=False
                        )

                st.download_button(
                    label="📊 Download Complete Report (Excel)",
                    data=buffer.getvalue(),
                    file_name=f"battery_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )
            except:
                st.info(
                    "Excel export requires openpyxl. Install with: pip install openpyxl"
                )

        # Preview data
        st.subheader("Current Data Preview")
        st.dataframe(current_df, use_container_width=True)

    # Export historical data
    if st.session_state.historical_data:
        st.subheader("Historical Data Export")

        historical_df = pd.DataFrame(st.session_state.historical_data)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Records", len(historical_df))

        with col2:
            if len(historical_df) > 0:
                time_span = (
                    historical_df["timestamp"].max() - historical_df["timestamp"].min()
                )
                st.metric("Time Span", f"{time_span.total_seconds()/60:.1f} min")

        with col3:
            data_size = len(str(historical_df)) / 1024  # Rough size estimate
            st.metric("Data Size", f"{data_size:.1f} KB")

        # Historical data download
        historical_csv = historical_df.to_csv(index=False)
        st.download_button(
            label="📈 Download Historical Data (CSV)",
            data=historical_csv,
            file_name=f"battery_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

        # Historical data preview
        st.subheader("Historical Data Preview (Last 10 Records)")
        st.dataframe(historical_df.tail(10), use_container_width=True)

    # Configuration backup
    st.subheader("Configuration Backup")

    if st.session_state.cells_data:
        config_data = {
            "configuration": {
                "cells": {
                    k: {
                        param: (float(v) if isinstance(v, (int, float)) else v)
                        for param, v in cell_data.items()
                    }
                    for k, cell_data in st.session_state.cells_data.items()
                },
                "backup_time": datetime.now().isoformat(),
                "total_cells": len(st.session_state.cells_data),
                "cell_types": list(
                    set(
                        cell_id.split("_")[2]
                        for cell_id in st.session_state.cells_data.keys()
                    )
                ),
            }
        }

        import json

        config_json = json.dumps(config_data, indent=2)

        st.download_button(
            label="⚙️ Backup Configuration (JSON)",
            data=config_json,
            file_name=f"battery_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True,
        )

    # Data management
    st.subheader("Data Management")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🗑️ Clear Historical Data", use_container_width=True):
            st.session_state.historical_data = []
            st.session_state.sample_data_generated = False
            st.success("Historical data cleared!")

    with col2:
        if st.button("🔄 Reset All Data", use_container_width=True):
            st.session_state.cells_data = {}
            st.session_state.historical_data = []
            st.session_state.alerts = []
            st.session_state.sample_data_generated = False
            st.success("All data reset!")

    with col3:
        if st.button("📊 Generate Sample Data", use_container_width=True):
            if st.session_state.cells_data:
                st.session_state.sample_data_generated = False
                generate_sample_data()
                st.success("Sample historical data generated!")

# Footer
st.markdown("---")

# System status footer
if st.session_state.cells_data:
    total_power = sum(cell["power"] for cell in st.session_state.cells_data.values())
    avg_temp = np.mean([cell["temp"] for cell in st.session_state.cells_data.values()])
    system_status = (
        "🟢 Operational"
        if all(
            get_cell_status(cell_data, cell_id.split("_")[2]) == "healthy"
            for cell_id, cell_data in st.session_state.cells_data.items()
        )
        else "🟡 Attention Required"
    )
else:
    total_power = 0
    avg_temp = 0
    system_status = "🔴 Not Configured"

st.markdown(
    f"""
<div style='text-align: center; color: #666; padding: 20px; background-color: #f8f9fa; border-radius: 10px;'>
    <strong>🔋 Battery Management System v2.0</strong><br>
    Built with Streamlit | Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
    Cells: {len(st.session_state.cells_data)} | Total Power: {total_power:.2f}W | Avg Temp: {avg_temp:.1f}°C | Status: {system_status}
</div>
""",
    unsafe_allow_html=True,
)
