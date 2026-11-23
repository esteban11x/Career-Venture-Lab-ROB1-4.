import json
from datetime import date
from decimal import Decimal
from pathlib import Path

import pandas as pd
import streamlit as st

from engine import (
    default_snapshot, simulate_rob_month, apply_approved_step,
    validate_snapshot_import, snapshot_json, money, money_str,
    algebra2_foundation_breakeven, algebra2_applied_demand,
    algebra2_advanced_extra_shift,
)

st.set_page_config(page_title="Career Venture Lab | ROB-1", page_icon="🤖", layout="wide")

if "snapshot" not in st.session_state:
    st.session_state.snapshot = default_snapshot()
if "preview" not in st.session_state:
    st.session_state.preview = None

snap = st.session_state.snapshot

st.title("🤖 Career Venture Lab")
st.subheader("ROB-1 | Robotics Kit & Repair Studio")
st.caption("Algebra 2 • Advanced • Stage 1 dashboard | Fictional teaching simulation")

with st.sidebar:
    st.header("Project information")
    st.write("**Pathway:** ROB-1")
    st.write("**Course:** Algebra 2")
    st.write("**Level:** Advanced")
    team_id = st.text_input("Team ID", value=snap["team_id"],
                            help="Replace TEAM-ROB1 with the team ID your teacher gave you.")
    if team_id != snap["team_id"]:
        st.warning("Changing the team ID changes the project identity.")
        if st.button("Apply team ID"):
            snap["team_id"] = team_id.strip() or "TEAM-ROB1"
            st.session_state.snapshot = snap
            st.rerun()
    st.divider()
    st.download_button("Download snapshot JSON", data=snapshot_json(snap),
                       file_name="rob1_snapshot.json", mime="application/json")
    uploaded = st.file_uploader("Restore snapshot JSON", type=["json"])
    if uploaded is not None and st.button("Validate and restore snapshot"):
        try:
            incoming = json.loads(uploaded.getvalue().decode("utf-8"))
            ok, message = validate_snapshot_import(incoming, snap)
            if ok:
                st.session_state.snapshot = incoming
                st.success(message)
                st.rerun()
            else:
                st.error(message)
        except Exception as exc:
            st.error(f"Could not read that JSON file: {exc}")
    if st.button("Reset simulation to opening baseline"):
        st.session_state.snapshot = default_snapshot(team_id=snap["team_id"])
        st.session_state.preview = None
        st.rerun()

tabs = st.tabs(["Overview", "Inputs & Funding", "Algebra 2 Math",
                "Dated Ledger & Fixture Replay", "Save & Restore"])

with tabs[0]:
    st.header("Business overview")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Spendable cash", money_str(snap["balances"]["cash"]))
    c2.metric("Component stock", f'{snap["balances"]["stock_units"]} sets')
    c3.metric("Inventory value", money_str(snap["balances"]["inventory_value"]))
    c4.metric("State version", str(snap["state_version"]))
    st.markdown("""
    **What this business does:** it sells introductory robot kits. Each kit uses one complete
    component set and takes staff time to assemble. The dashboard estimates sales, expenses,
    profit, cash, and remaining stock.
    """)
    st.info("Stage 1 only. Department assistants, report center, marketing studio, assessments, and storefront are later-stage features and are not built in this version.")
    st.subheader("Startup funding (handbook baseline)")
    st.dataframe(pd.DataFrame([
        ["Owner contribution", "$12,000", "Money provided by owner"],
        ["Equipment assets", "$4,000", "Tools and test equipment"],
        ["Opening inventory", "$3,000", "100 component sets at $30 each"],
        ["Opening spendable cash", "$5,000", "Cash available after startup purchases"],
    ], columns=["Item", "Amount", "Meaning"]), hide_index=True)
    st.subheader("Business cost structure")
    st.write("Variable cost per attempted kit: **$65** ($30 components + $20 labor + $10 packaging + $5 warranty supplies).")
    st.write("Fixed monthly costs: **$600** ($250 workspace + $100 software + $150 maintenance + $100 admin).")

with tabs[1]:
    st.header("Inputs & Funding")
    st.write("Change the monthly assumptions below. First preview the result. It will not change your saved business record until you approve it.")
    col1, col2 = st.columns(2)
    with col1:
        price = st.number_input("Kit selling price ($)", min_value=0.01, value=120.0, step=5.0)
        requested = st.number_input("Customer requests this month", min_value=0, value=40, step=1)
        staff_hours = st.number_input("Productive staff hours", min_value=0.0, value=90.0, step=3.0)
        hours_per_unit = st.number_input("Hours needed per kit", min_value=0.01, value=3.0, step=0.5)
    with col2:
        restock = st.number_input("New component sets purchased", min_value=0, value=0, step=5)
        defect_pct = st.slider("Defect rate (%)", min_value=0, max_value=100, value=0)
        ad_cost = st.number_input("Advertising cost ($)", min_value=0.0, value=0.0, step=25.0)
        sim_date = st.date_input("Simulation date", value=date.today())
    inputs = {"base_price": price, "requested": int(requested),
              "staff_hours": staff_hours, "hours_per_unit": hours_per_unit,
              "restock_units": int(restock), "defect_rate": defect_pct / 100,
              "ad_cost": ad_cost}
    try:
        preview = simulate_rob_month(inputs,
                    opening_cash=snap["balances"]["cash"],
                    opening_stock_units=snap["balances"]["stock_units"])
        st.session_state.preview = (inputs, preview, sim_date.isoformat())
        st.subheader("Preview (not yet saved)")
        a, b, c, d = st.columns(4)
        a.metric("Kits sold", str(preview["sold"]))
        b.metric("Revenue", money_str(preview["revenue"]))
        c.metric("Profit", money_str(preview["operating_profit"]))
        d.metric("Ending cash", money_str(preview["ending_cash"]))
        st.write(f"Capacity: **{preview['capacity']} kits** | Attempted: **{preview['attempted']}** | Failed: **{preview['failed']}** | Lost demand: **{preview['lost_demand']}**")
        if st.button("Approve and record this month", type="primary"):
            run_id = f"RUN-{sim_date.strftime('%Y%m%d')}-{len(snap['ledger'])+1}"
            new_snap, result, applied = apply_approved_step(snap, inputs, sim_date.isoformat(), run_id)
            if applied:
                st.session_state.snapshot = new_snap
                st.success("This month was recorded in the dated ledger.")
                st.rerun()
            else:
                st.warning("This run ID was already used; no duplicate record was created.")
    except Exception as exc:
        st.error(f"Please check the inputs: {exc}")

with tabs[2]:
    st.header("Algebra 2 Math Skills")
    st.caption("The equations below use the ROB-1 handbook rules. Continuous model estimates are not the same as whole-kit transactions.")
    st.subheader("Foundation: revenue, cost, and break-even")
    st.latex(r"R(s)=120s")
    st.latex(r"C(s)=600+65s")
    st.write("Here, s means kits sold or attempted in the simple model. Revenue is $120 per kit. Cost includes $600 fixed costs and $65 variable cost per attempted kit.")
    be = algebra2_foundation_breakeven(120, 65, 600, capacity=30)
    st.write(f"Break-even = 600 ÷ (120 − 65) = **{be['break_even_exact']:.2f} kits**, so **{be['whole_units']} whole kits** are needed.")
    st.write(f"Capacity check: **{be['status_label']}** (normal baseline capacity is 30 kits).")
    st.subheader("Applied: demand changes with price")
    chosen_price = st.slider("Test a selling price ($)", 0, 240, 120, 5)
    demand = algebra2_applied_demand(chosen_price, 120, 40)
    st.write(f"Demand model: q(p) = max(0, 80 − p/3). At ${chosen_price}, estimated requested demand is **{demand:.2f} kits** before capacity limits.")
    st.write("Completed kits are capped by available staff hours and component sets.")
    prices = [60, 120, 180]
    rows = []
    for p in prices:
        q = algebra2_applied_demand(p, 120, 40)
        s = min(30, int(q))
        rev = Decimal(s) * Decimal(p)
        cost = Decimal(600) + Decimal(65) * s
        rows.append({"Price": f"${p}", "Model demand": f"{q:.1f}",
                     "Kits used for comparison": s, "Revenue": money_str(rev),
                     "Estimated profit": money_str(rev-cost)})
    st.dataframe(pd.DataFrame(rows), hide_index=True)
    st.subheader("Advanced: extra staffing shift")
    extra_hours = st.number_input("Extra shift hours", min_value=0.0, value=30.0, step=3.0)
    hourly_rate = st.number_input("Extra shift hourly cost ($)", min_value=0.0, value=20.0, step=1.0)
    plan = algebra2_advanced_extra_shift(extra_hours=extra_hours,
              extra_hourly_rate=hourly_rate, requested_demand=40)
    st.write(f"Current capacity: **{plan['base_capacity']} kits**")
    st.write(f"Added capacity: **{plan['added_capacity']} kits**")
    st.write(f"New capacity: **{plan['new_capacity']} kits**")
    st.write(f"Extra shift cost: **{money_str(plan['added_fixed_cost'])}**")
    st.write(f"Estimated profit with current demand: **{money_str(plan['new_profit'])}**")
    st.info("The quadratic or growth model stays off until your teacher approves it, as required by the Algebra 2 adapter.")

with tabs[3]:
    st.header("Dated Ledger & Fixture Replay")
    st.write("The official fixture is a practice test. It deliberately uses capacity overrides; normal business mode calculates capacity from staff hours.")
    fixture_path = Path(__file__).parent / "sample_data" / "monthly_fixture.csv"
    fixture = pd.read_csv(fixture_path)
    st.dataframe(fixture, hide_index=True)
    if st.button("Reset & replay official ROB-1 3-month fixture"):
        replay = default_snapshot(team_id=snap["team_id"])
        replay_rows = []
        for row in fixture.to_dict(orient="records"):
            values = {"base_price": 120, "requested": int(row["requested"]),
                      "staff_hours": 90, "hours_per_unit": 3,
                      "restock_units": 0, "defect_rate": 0,
                      "ad_cost": float(row["ad_cost"])}
            result = simulate_rob_month(values, opening_cash=replay["balances"]["cash"],
                       opening_stock_units=replay["balances"]["stock_units"],
                       capacity_override=int(row["capacity_override"]))
            run_id = f"FIXTURE-{row['month']}"
            month_end = pd.Period(row["month"], freq="M").end_time.date().isoformat()
            replay, _, _ = apply_approved_step(replay, values, month_end,
                                                run_id, capacity_override=int(row["capacity_override"]))
            replay_rows.append({"Month": row["month"], "Sold": result["sold"],
                "Revenue": money_str(result["revenue"]),
                "Total expense": money_str(result["variable_expense"] + result["fixed_expense"] + result["marketing"]),
                "Profit": money_str(result["operating_profit"]),
                "Closing cash": money_str(result["ending_cash"]),
                "Ending stock": result["ending_stock_units"]})
        st.session_state.fixture_results = replay_rows
        st.session_state.fixture_snapshot = replay
    if "fixture_results" in st.session_state:
        st.success("Fixture replay completed. This is a separate practice replay; it did not replace your current simulation.")
        st.dataframe(pd.DataFrame(st.session_state.fixture_results), hide_index=True)
        last = st.session_state.fixture_results[-1]
        st.metric("Final fixture cash", last["Closing cash"])
        st.metric("Final fixture component stock", f'{last["Ending stock"]} sets')
    if snap["ledger"]:
        ledger_rows = []
        for entry in snap["ledger"]:
            ledger_rows.append({"Date": entry["date"], "Run ID": entry["transaction_id"],
                                "Units sold": entry["quantity"], "Revenue": entry["amount"],
                                "Version": entry["state_version"]})
        st.subheader("Your approved activity")
        st.dataframe(pd.DataFrame(ledger_rows), hide_index=True)
    else:
        st.info("No monthly activity has been approved yet.")

with tabs[4]:
    st.header("Save & Restore")
    st.write("Your snapshot JSON is your saved progress file. Download it before closing the project, and upload it later to restore the same team state.")
    st.code("1. Click Download snapshot JSON in the left sidebar.\n2. Keep the file somewhere you can find it.\n3. To continue later, upload it under Restore snapshot JSON.\n4. The app checks team ID and version before accepting it.")
    st.write("Current snapshot summary")
    st.json({"team_id": snap["team_id"], "snapshot_id": snap["snapshot_id"],
             "state_version": snap["state_version"],
             "simulation_date": snap["simulation_date"],
             "ledger_entries": len(snap["ledger"]),
             "cash": snap["balances"]["cash"],
             "stock_units": snap["balances"]["stock_units"]})
