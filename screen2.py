import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ortools.sat.python import cp_model
from datetime import datetime, timedelta

# Page configuration
st.set_page_config(page_title="OR-Tools Schedule Optimizer", layout="wide", initial_sidebar_state="collapsed")

# Custom CSS - Matching original dashboard theme
st.markdown("""
<style>
    .main {
        background-color: #1a1d2e;
        color: #ffffff;
    }
    .stApp {
        background-color: #1a1d2e;
    }
    h1, h2, h3, h4, p, label {
        color: #ffffff !important;
    }
    .metric-box {
        background-color: #2d3250;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin: 10px 0;
    }
    .metric-card {
        background-color: #2d3250;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin: 10px;
    }
    .metric-title {
        font-size: 18px;
        font-weight: 600;
        margin-bottom: 15px;
        color: #ffffff;
    }
    .metric-value {
        font-size: 36px;
        font-weight: 700;
        color: #ffffff;
    }
    .metric-label {
        font-size: 14px;
        margin-top: 5px;
        color: #b0b0b0;
    }
    .stButton>button {
        width: 100%;
        background-color: #4a5578;
        color: white;
        border: none;
        padding: 12px;
        border-radius: 5px;
        margin: 5px 0;
        font-weight: 500;
    }
    .stButton>button:hover {
        background-color: #5a6588;
    }
    .insight-box {
        background-color: #2d3250;
        padding: 20px;
        border-radius: 10px;
        margin-top: 20px;
    }
    div[data-testid="stMetricValue"] {
        font-size: 36px;
        color: #ffffff;
    }
    .stSelectbox {
        color: #ffffff;
    }
    div[data-testid="stDataFrame"] {
        background-color: #2d3250;
    }
    .stDataFrame {
        color: #ffffff;
    }
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #1a1d2e;
    }
    section[data-testid="stSidebar"] > div {
        background-color: #1a1d2e;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# INPUT DATA - MODIFY THESE VARIABLES
# ============================================================================

# Crews available
CREWS = ['C01', 'C02', 'C03', 'C04', 'C05', 'C06', 'C07', 'C08', 'C09']

# Flights that need to be assigned (Flight ID, Start Time Hour, Duration Hours, Priority)
FLIGHTS = [
    {'id': 'F101', 'start': 6.0, 'duration': 3.5, 'priority': 1},
    {'id': 'F102', 'start': 7.0, 'duration': 3.5, 'priority': 1},
    {'id': 'F203', 'start': 10.5, 'duration': 2.5, 'priority': 2},
    {'id': 'F204', 'start': 13.0, 'duration': 3.0, 'priority': 2},
    {'id': 'F305', 'start': 13.0, 'duration': 5.0, 'priority': 1},
    {'id': 'F108', 'start': 12.0, 'duration': 2.0, 'priority': 1},
    {'id': 'F109', 'start': 14.0, 'duration': 2.5, 'priority': 2},
    {'id': 'F112', 'start': 9.0, 'duration': 2.0, 'priority': 1},
    {'id': 'F505', 'start': 15.0, 'duration': 3.0, 'priority': 1},
    {'id': 'F601', 'start': 6.0, 'duration': 1.0, 'priority': 1},
    {'id': 'F602', 'start': 7.5, 'duration': 4.0, 'priority': 2},
    {'id': 'F701', 'start': 11.0, 'duration': 3.0, 'priority': 1},
    {'id': 'F702', 'start': 15.0, 'duration': 3.0, 'priority': 2},
    {'id': 'F801', 'start': 8.0, 'duration': 2.0, 'priority': 1},
    {'id': 'F802', 'start': 10.5, 'duration': 2.5, 'priority': 2},
    {'id': 'F803', 'start': 10.0, 'duration': 2.0, 'priority': 1},
    {'id': 'F901', 'start': 13.0, 'duration': 3.0, 'priority': 1},
    {'id': 'F902', 'start': 16.5, 'duration': 1.5, 'priority': 2},
]

# Constraints
MAX_DUTY_HOURS = 9.0  # Maximum duty hours per crew per day
MIN_REST_HOURS = 0.5  # Minimum rest between flights (in hours)
MAX_FLIGHTS_PER_CREW = 4  # Maximum flights per crew

# ============================================================================

# Initialize session state
if 'optimized_solution' not in st.session_state:
    st.session_state.optimized_solution = None
if 'optimization_stats' not in st.session_state:
    st.session_state.optimization_stats = None

def optimize_schedule(flights, crews, max_duty, min_rest, max_flights):
    """
    Optimize crew schedule using Google OR-Tools CP-SAT Solver
    """
    model = cp_model.CpModel()
    
    # Decision variables: assignment[f, c] = 1 if flight f is assigned to crew c
    assignments = {}
    for f_idx, flight in enumerate(flights):
        for c_idx, crew in enumerate(crews):
            assignments[(f_idx, c_idx)] = model.NewBoolVar(f'flight_{f_idx}_crew_{c_idx}')
    
    # Constraint 1: Each flight must be assigned to exactly one crew
    for f_idx in range(len(flights)):
        model.Add(sum(assignments[(f_idx, c_idx)] for c_idx in range(len(crews))) == 1)
    
    # Constraint 2: Maximum duty hours per crew
    for c_idx in range(len(crews)):
        total_duty = sum(
            assignments[(f_idx, c_idx)] * int(flights[f_idx]['duration'] * 100)
            for f_idx in range(len(flights))
        )
        model.Add(total_duty <= int(max_duty * 100))
    
    # Constraint 3: Maximum flights per crew
    for c_idx in range(len(crews)):
        model.Add(
            sum(assignments[(f_idx, c_idx)] for f_idx in range(len(flights))) <= max_flights
        )
    
    # Constraint 4: No overlapping flights for same crew (with rest time)
    for c_idx in range(len(crews)):
        for f1_idx in range(len(flights)):
            for f2_idx in range(f1_idx + 1, len(flights)):
                f1 = flights[f1_idx]
                f2 = flights[f2_idx]
                
                f1_end = f1['start'] + f1['duration']
                f2_end = f2['start'] + f2['duration']
                
                # Check if flights overlap (considering rest time)
                if not (f1_end + min_rest <= f2['start'] or f2_end + min_rest <= f1['start']):
                    # If they overlap, they cannot both be assigned to the same crew
                    model.Add(assignments[(f1_idx, c_idx)] + assignments[(f2_idx, c_idx)] <= 1)
    
    # Objective: Minimize total cost (prioritize high-priority flights and balance workload)
    objective_terms = []
    
    # Cost for not utilizing crews (encourage balanced distribution)
    for c_idx in range(len(crews)):
        crew_flights = sum(assignments[(f_idx, c_idx)] for f_idx in range(len(flights)))
        # Penalty for very low utilization
        objective_terms.append(crew_flights * 10)
    
    # Bonus for assigning high-priority flights
    for f_idx, flight in enumerate(flights):
        for c_idx in range(len(crews)):
            objective_terms.append(assignments[(f_idx, c_idx)] * flight['priority'] * 5)
    
    model.Maximize(sum(objective_terms))
    
    # Solve
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10.0
    status = solver.Solve(model)
    
    # Extract solution
    solution = []
    stats = {
        'status': 'OPTIMAL' if status == cp_model.OPTIMAL else 'FEASIBLE' if status == cp_model.FEASIBLE else 'INFEASIBLE',
        'solve_time': solver.WallTime(),
        'violations': 0,
        'total_duty_hours': 0,
        'crew_utilization': {}
    }
    
    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        for f_idx, flight in enumerate(flights):
            for c_idx, crew in enumerate(crews):
                if solver.Value(assignments[(f_idx, c_idx)]) == 1:
                    solution.append({
                        'Crew': crew,
                        'Flight': flight['id'],
                        'Start': flight['start'],
                        'Duration': flight['duration'],
                        'End': flight['start'] + flight['duration'],
                        'Priority': flight['priority']
                    })
                    
                    # Update stats
                    if crew not in stats['crew_utilization']:
                        stats['crew_utilization'][crew] = 0
                    stats['crew_utilization'][crew] += flight['duration']
        
        # Calculate total duty hours
        stats['total_duty_hours'] = sum(stats['crew_utilization'].values())
        
        # Check for violations
        for crew in crews:
            if crew in stats['crew_utilization']:
                if stats['crew_utilization'][crew] > max_duty:
                    stats['violations'] += 1
    
    return solution, stats

# Header
st.markdown("<h1>Crew Schedule Optimizer</h1>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Sidebar - Configuration
with st.sidebar:
    st.markdown("<h2>⚙️ Schedule Settings</h2>", unsafe_allow_html=True)
    
    st.markdown("### Constraints")
    max_duty_input = st.number_input("Max Duty Hours per Crew", min_value=6.0, max_value=12.0, value=MAX_DUTY_HOURS, step=0.5)
    min_rest_input = st.number_input("Min Rest Between Flights (hours)", min_value=0.0, max_value=2.0, value=MIN_REST_HOURS, step=0.25)
    max_flights_input = st.number_input("Max Flights per Crew", min_value=1, max_value=6, value=MAX_FLIGHTS_PER_CREW, step=1)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("🚀 Generate Schedule", type="primary", use_container_width=True):
        with st.spinner("Generating optimized schedule..."):
            solution, stats = optimize_schedule(
                FLIGHTS, 
                CREWS, 
                max_duty_input, 
                min_rest_input, 
                max_flights_input
            )
            st.session_state.optimized_solution = solution
            st.session_state.optimization_stats = stats
        
        if stats['status'] in ['OPTIMAL', 'FEASIBLE']:
            st.success(f"✅ Schedule generated successfully! Status: {stats['status']}")
        else:
            st.error(f"❌ Schedule generation failed: {stats['status']}")
    
    if st.button("🔄 Reset", use_container_width=True):
        st.session_state.optimized_solution = None
        st.session_state.optimization_stats = None
        st.rerun()

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("<h3>Input Flights</h3>", unsafe_allow_html=True)
    
    # Display input flights
    df_flights = pd.DataFrame(FLIGHTS)
    df_flights['Start Time'] = df_flights['start'].apply(lambda x: f"{int(x):02d}:{int((x % 1) * 60):02d}")
    df_flights['End Time'] = df_flights.apply(lambda row: f"{int(row['start'] + row['duration']):02d}:{int(((row['start'] + row['duration']) % 1) * 60):02d}", axis=1)
    df_flights_display = df_flights[['id', 'Start Time', 'End Time', 'duration', 'priority']]
    df_flights_display.columns = ['Flight ID', 'Start', 'End', 'Duration (h)', 'Priority']
    
    st.dataframe(df_flights_display, use_container_width=True, hide_index=True)

with col2:
    st.markdown("<h3>Available Crews</h3>", unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="metric-card" style="background-color: #3d5a4c; height: 120px; display: flex; flex-direction: column; justify-content: center;">
        <div class="metric-title">Total Crews</div>
        <div class="metric-value" style="color: #4ade80;">{len(CREWS)}</div>
        <div class="metric-label">Available</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="metric-card" style="background-color: #8b6f47; height: 120px; display: flex; flex-direction: column; justify-content: center;">
        <div class="metric-title">Total Flights</div>
        <div class="metric-value">{len(FLIGHTS)}</div>
        <div class="metric-label">To Assign</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)

# Display schedule results
if st.session_state.optimized_solution is not None and st.session_state.optimization_stats is not None:
    solution = st.session_state.optimized_solution
    stats = st.session_state.optimization_stats
    
    # Metrics
    st.markdown("<h3>📊 Schedule Results</h3>", unsafe_allow_html=True)
    
    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    
    with metric_col1:
        st.markdown(f"""
        <div class="metric-card" style="background-color: #3d5a4c; height: 140px; display: flex; flex-direction: column; justify-content: center;">
            <div class="metric-title">Status</div>
            <div class="metric-value" style="color: #4ade80;">{stats['status']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with metric_col2:
        st.markdown(f"""
        <div class="metric-card" style="background-color: #4a5578; height: 140px; display: flex; flex-direction: column; justify-content: center;">
            <div class="metric-title">Solve Time</div>
            <div class="metric-value">{stats['solve_time']:.2f}<span style="font-size: 20px;">s</span></div>
        </div>
        """, unsafe_allow_html=True)
    
    with metric_col3:
        violation_color = '#3d5a4c' if stats['violations'] == 0 else '#6b3a3a'
        violation_text_color = '#4ade80' if stats['violations'] == 0 else '#ef4444'
        st.markdown(f"""
        <div class="metric-card" style="background-color: {violation_color}; height: 140px; display: flex; flex-direction: column; justify-content: center;">
            <div class="metric-title">Violations</div>
            <div class="metric-value" style="color: {violation_text_color};">{stats['violations']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with metric_col4:
        avg_utilization = (stats['total_duty_hours'] / (len(CREWS) * max_duty_input)) * 100
        st.markdown(f"""
        <div class="metric-card" style="background-color: #8b6f47; height: 140px; display: flex; flex-direction: column; justify-content: center;">
            <div class="metric-title">Avg Utilization</div>
            <div class="metric-value">{avg_utilization:.1f}<span style="font-size: 20px;">%</span></div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📅 Gantt Chart", "👥 Crew Assignments", "📋 Flight Details", "📊 Crew Utilization"])
    
    with tab1:
        st.markdown("<h4>Optimized Schedule - Gantt Chart</h4>", unsafe_allow_html=True)
        
        # Create Gantt chart
        fig = go.Figure()
        
        colors = {1: '#4ade80', 2: '#fb923c', 3: '#dc2626'}
        
        for assignment in solution:
            fig.add_trace(go.Bar(
                y=[assignment['Crew']],
                x=[assignment['Duration']],
                base=assignment['Start'],
                orientation='h',
                marker=dict(color=colors.get(assignment['Priority'], '#4ade80')),
                showlegend=False,
                hovertemplate=f"<b>{assignment['Crew']} - {assignment['Flight']}</b><br>" +
                              f"Start: {assignment['Start']:.1f}h<br>" +
                              f"Duration: {assignment['Duration']}h<br>" +
                              f"Priority: {assignment['Priority']}<extra></extra>"
            ))
        
        fig.update_layout(
            barmode='stack',
            height=500,
            plot_bgcolor='#1a1d2e',
            paper_bgcolor='#1a1d2e',
            font=dict(color='#ffffff'),
            xaxis=dict(
                title="Time of Day (hours)",
                tickmode='array',
                tickvals=[6, 8, 10, 12, 14, 16, 18],
                ticktext=['6:00', '8:00', '10:00', '12:00', '14:00', '16:00', '18:00'],
                gridcolor='#2d3250',
                range=[5, 19]
            ),
            yaxis=dict(
                title="Crew",
                gridcolor='#2d3250',
                categoryorder='array',
                categoryarray=CREWS[::-1]
            ),
            margin=dict(l=60, r=20, t=20, b=50),
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("""
        <div style='display: flex; gap: 20px; justify-content: center; font-size: 13px;'>
            <span><span style='color: #4ade80;'>■</span> Priority 1</span>
            <span><span style='color: #fb923c;'>■</span> Priority 2</span>
            <span><span style='color: #dc2626;'>■</span> Priority 3</span>
        </div>
        """, unsafe_allow_html=True)
    
    with tab2:
        st.markdown("<h4>Crew Assignments Overview</h4>", unsafe_allow_html=True)
        
        # Group assignments by crew
        crew_assignments = {}
        for assignment in solution:
            crew = assignment['Crew']
            if crew not in crew_assignments:
                crew_assignments[crew] = []
            crew_assignments[crew].append(assignment)
        
        # Sort crews
        sorted_crews = sorted(crew_assignments.keys())
        
        # Create columns for crew cards
        num_cols = 3
        for i in range(0, len(sorted_crews), num_cols):
            cols = st.columns(num_cols)
            for j, col in enumerate(cols):
                if i + j < len(sorted_crews):
                    crew = sorted_crews[i + j]
                    flights = crew_assignments[crew]
                    total_hours = sum([f['Duration'] for f in flights])
                    num_flights = len(flights)
                    
                    with col:
                        # Crew card
                        st.markdown(f"""
                        <div class="insight-box" style="margin: 10px 0;">
                            <h3 style="color: #4ade80; margin: 0 0 15px 0;">{crew}</h3>
                            <div style="display: flex; justify-content: space-between; margin-bottom: 15px;">
                                <div>
                                    <p style="color: #b0b0b0; margin: 0; font-size: 12px;">Flights</p>
                                    <p style="color: #ffffff; margin: 5px 0; font-size: 20px; font-weight: 600;">{num_flights}</p>
                                </div>
                                <div>
                                    <p style="color: #b0b0b0; margin: 0; font-size: 12px;">Duty Hours</p>
                                    <p style="color: #ffffff; margin: 5px 0; font-size: 20px; font-weight: 600;">{total_hours:.1f}h</p>
                                </div>
                            </div>
                            <div style="background-color: #1a1d2e; padding: 10px; border-radius: 5px;">
                        """, unsafe_allow_html=True)
                        
                        # List flights for this crew
                        for flight in sorted(flights, key=lambda x: x['Start']):
                            priority_color = '#4ade80' if flight['Priority'] == 1 else '#fb923c' if flight['Priority'] == 2 else '#dc2626'
                            st.markdown(f"""
                            <div style="display: flex; justify-content: space-between; align-items: center; margin: 5px 0; padding: 8px; background-color: #2d3250; border-radius: 5px;">
                                <div>
                                    <span style="color: #ffffff; font-weight: 600;">{flight['Flight']}</span>
                                    <span style="color: #b0b0b0; font-size: 12px; margin-left: 10px;">{flight['Start']:.0f}:{int((flight['Start'] % 1) * 60):02d}-{flight['End']:.0f}:{int((flight['End'] % 1) * 60):02d}</span>
                                </div>
                                <span style="background-color: {priority_color}; color: #ffffff; padding: 3px 8px; border-radius: 10px; font-size: 11px;">P{flight['Priority']}</span>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        st.markdown("</div></div>", unsafe_allow_html=True)
        
        # Unassigned crews
        unassigned_crews = [c for c in CREWS if c not in crew_assignments]
        if unassigned_crews:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("""
            <div class="insight-box" style="background-color: #4d3a1e; border-left: 4px solid #fb923c;">
                <h4 style="color: #fb923c; margin: 0;">⚠️ Unassigned Crews</h4>
            """, unsafe_allow_html=True)
            st.markdown(f"<p style='color: #ffffff; margin: 10px 0;'>{', '.join(unassigned_crews)}</p>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
    
    with tab3:
        st.markdown("<h4>Flight Assignments</h4>", unsafe_allow_html=True)
        
        # Create assignment table
        df_solution = pd.DataFrame(solution)
        df_solution['Start Time'] = df_solution['Start'].apply(lambda x: f"{int(x):02d}:{int((x % 1) * 60):02d}")
        df_solution['End Time'] = df_solution['End'].apply(lambda x: f"{int(x):02d}:{int((x % 1) * 60):02d}")
        df_solution_display = df_solution[['Crew', 'Flight', 'Start Time', 'End Time', 'Duration', 'Priority']]
        df_solution_display = df_solution_display.sort_values(['Crew', 'Start Time'])
        
        st.dataframe(df_solution_display, use_container_width=True, hide_index=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Add quick search/filter
        st.markdown("<h4>Search Assignments</h4>", unsafe_allow_html=True)
        search_col1, search_col2 = st.columns(2)
        
        with search_col1:
            search_crew = st.selectbox("Filter by Crew:", ['All'] + CREWS, key="search_crew_tab")
        
        with search_col2:
            search_flight = st.text_input("Search Flight ID:", placeholder="e.g., F101", key="search_flight_tab")
        
        # Apply filters
        filtered_df = df_solution_display.copy()
        if search_crew != 'All':
            filtered_df = filtered_df[filtered_df['Crew'] == search_crew]
        if search_flight:
            filtered_df = filtered_df[filtered_df['Flight'].str.contains(search_flight, case=False)]
        
        if len(filtered_df) > 0:
            st.dataframe(filtered_df, use_container_width=True, hide_index=True)
        else:
            st.info("No matching flights found")
    
    with tab4:
        st.markdown("<h4>Crew Utilization Analysis</h4>", unsafe_allow_html=True)
        
        # Create utilization chart
        utilization_data = []
        for crew in CREWS:
            hours = stats['crew_utilization'].get(crew, 0)
            utilization_pct = (hours / max_duty_input) * 100
            utilization_data.append({
                'Crew': crew,
                'Hours': hours,
                'Utilization': utilization_pct,
                'Available': max_duty_input - hours
            })
        
        df_util = pd.DataFrame(utilization_data)
        
        fig_util = go.Figure()
        
        fig_util.add_trace(go.Bar(
            x=df_util['Crew'],
            y=df_util['Hours'],
            name='Used Hours',
            marker_color='#4ade80',
            text=df_util['Hours'].apply(lambda x: f'{x:.1f}h'),
            textposition='inside'
        ))
        
        fig_util.add_trace(go.Bar(
            x=df_util['Crew'],
            y=df_util['Available'],
            name='Available Hours',
            marker_color='#2d3250',
            text=df_util['Available'].apply(lambda x: f'{x:.1f}h'),
            textposition='inside'
        ))
        
        fig_util.update_layout(
            barmode='stack',
            height=400,
            plot_bgcolor='#1a1d2e',
            paper_bgcolor='#1a1d2e',
            font=dict(color='#ffffff'),
            xaxis=dict(title='Crew', gridcolor='#2d3250'),
            yaxis=dict(title='Hours', gridcolor='#2d3250'),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            margin=dict(l=60, r=20, t=60, b=50)
        )
        
        st.plotly_chart(fig_util, use_container_width=True)
        
        st.dataframe(df_util[['Crew', 'Hours', 'Utilization', 'Available']], use_container_width=True, hide_index=True)

else:
    st.markdown("""
    <div class="insight-box">
        <h3 style="color: #ffffff; margin-top: 0;">👈 Click 'Generate Schedule' to Start</h3>
        <p style="color: #b0b0b0; line-height: 1.8;">
            Use the sidebar to configure constraints and run the OR-Tools optimization engine.
        </p>
    </div>
    """, unsafe_allow_html=True)