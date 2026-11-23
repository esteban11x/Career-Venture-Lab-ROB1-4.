"""Deterministic business and Algebra 2 calculations for the ROB-1 simulator."""
from __future__ import annotations

from copy import deepcopy
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from math import floor
from typing import Any
import json
import uuid

CENT = Decimal("0.01")
ZERO = Decimal("0.00")
VARIABLE_PER_UNIT = Decimal("65.00")
NONCOMPONENT_CASH_PER_ATTEMPT = Decimal("35.00")
FIXED_MONTHLY = Decimal("600.00")
COMPONENT_COST = Decimal("30.00")
BASE_PRICE = Decimal("120.00")


def dec(value: Any) -> Decimal:
    return Decimal(str(value))


def money(value: Any) -> Decimal:
    return dec(value).quantize(CENT, rounding=ROUND_HALF_UP)


def money_str(value: Any) -> str:
    return f"${money(value):,.2f}"


def default_snapshot(team_id: str = "TEAM-ROB1") -> dict:
    return {
        "team_id": team_id,
        "course": "Algebra 2",
        "pathway_id": "ROB-1",
        "snapshot_id": f"ROB1-{uuid.uuid4().hex[:8].upper()}",
        "state_version": 1,
        "simulation_date": "2027-01-01",
        "base_period": "monthly",
        "working_days": 20,
        "currency": "USD",
        "level_by_skill": {
            "Break-even and piecewise profit": "Advanced",
            "Systems of linear inequalities": "Advanced",
            "Capacity and resource planning": "Advanced",
        },
        "assumptions": [
            "All business values are fictional teaching assumptions.",
            "One primary offering is active: Introductory robot kit.",
        ],
        "sources": ["Career Venture Lab Student Handbook, ROB package, pp. 78-82",
                    "Career Venture Lab Student Handbook, Algebra 2 adapter, p. 68"],
        "offerings": [{"offering_id": "ROB-KIT", "name": "Introductory robot kit",
                       "unit": "kit", "price": "120.00", "active": True}],
        "funding": [{"type": "owner_contribution", "amount": "12000.00"},
                    {"type": "equipment_assets", "amount": "4000.00"},
                    {"type": "opening_inventory", "amount": "3000.00"},
                    {"type": "opening_spendable_cash", "amount": "5000.00"}],
        "cost_lines": {
            "components_COGS": "30.00",
            "assembly_labor": "20.00",
            "packaging": "10.00",
            "warranty_consumables": "5.00",
            "workspace": "250.00",
            "software": "100.00",
            "equipment_maintenance": "150.00",
            "admin": "100.00",
            "advertising": "0.00",
        },
        "capacity": {"staff_hours": "90", "hours_per_unit": "3",
                     "opening_stock_units": 100, "component_unit_cost": "30.00"},
        "balances": {"cash": "5000.00", "stock_units": 100,
                     "inventory_value": "3000.00", "debt": "0.00",
                     "owner_equity": "12000.00"},
        "ledger": [],
        "campaigns": [],
        "decisions": [],
        "applied_run_ids": [],
    }


def simulate_rob_month(inputs: dict, opening_cash: Any = "5000.00",
                       opening_stock_units: int = 100,
                       capacity_override: int | None = None) -> dict:
    """Calculate one month. A capacity override is only for official fixture replay."""
    price = money(inputs.get("base_price", BASE_PRICE))
    requested = int(inputs.get("requested", 40))
    staff_hours = dec(inputs.get("staff_hours", 90))
    hours_per_unit = dec(inputs.get("hours_per_unit", 3))
    stock = int(opening_stock_units)
    restock = int(inputs.get("restock_units", 0))
    defect_rate = dec(inputs.get("defect_rate", 0))
    marketing = money(inputs.get("ad_cost", inputs.get("marketing", 0)))
    interest = money(inputs.get("interest", 0))
    principal = money(inputs.get("loan_principal", 0))
    loan_cash = money(inputs.get("loan_cash", 0))
    owner_cash = money(inputs.get("new_owner_cash", 0))
    capex = money(inputs.get("additional_capex", 0))
    refund = money(inputs.get("refund_amount", 0))

    if price <= 0:
        raise ValueError("Kit price must be greater than $0.")
    if requested < 0 or stock < 0 or restock < 0:
        raise ValueError("Requested units, stock, and restock cannot be negative.")
    if hours_per_unit <= 0 or staff_hours < 0:
        raise ValueError("Hours per unit must be greater than zero and staff hours cannot be negative.")
    if not (Decimal("0") <= defect_rate <= Decimal("1")):
        raise ValueError("Defect rate must be between 0 and 1.")
    if min(marketing, interest, principal, loan_cash, owner_cash, capex, refund) < 0:
        raise ValueError("Money inputs cannot be negative.")

    capacity = int(capacity_override) if capacity_override is not None else floor(staff_hours / hours_per_unit)
    if capacity < 0:
        raise ValueError("Capacity cannot be negative.")
    attempted = min(requested, capacity, stock + restock)
    failed = floor(Decimal(attempted) * defect_rate)
    sold = attempted - failed
    lost_demand = requested - attempted

    revenue_before_refund = price * sold
    refund_used = min(refund, revenue_before_refund)
    revenue = money(revenue_before_refund - refund_used)
    variable_expense = money(Decimal(attempted) * VARIABLE_PER_UNIT)
    fixed_expense = FIXED_MONTHLY
    operating_profit = money(revenue - variable_expense - fixed_expense - marketing)
    net_profit = money(operating_profit - interest)

    # Components were already paid for when opening inventory was purchased.
    # Cash is paid only for this month's restock; other $35/unit costs are paid per attempt.
    noncomponent_cash = money(Decimal(attempted) * NONCOMPONENT_CASH_PER_ATTEMPT)
    ending_cash = money(
        dec(opening_cash) + revenue - Decimal(restock) * COMPONENT_COST
        - noncomponent_cash - fixed_expense - marketing - interest
        - principal - capex + owner_cash + loan_cash
    )
    ending_stock = stock + restock - attempted
    if ending_stock < 0:
        raise ValueError("Inventory cannot become negative.")
    ending_inventory_value = money(Decimal(ending_stock) * COMPONENT_COST)

    return {
        "capacity": capacity, "requested": requested, "attempted": attempted,
        "failed": failed, "sold": sold, "lost_demand": lost_demand,
        "revenue": money(revenue), "refund": money(refund_used),
        "variable_expense": variable_expense, "fixed_expense": fixed_expense,
        "marketing": marketing, "interest": interest,
        "operating_profit": operating_profit, "net_profit": net_profit,
        "noncomponent_cash_cost": noncomponent_cash,
        "restock_cash_cost": money(Decimal(restock) * COMPONENT_COST),
        "ending_cash": ending_cash, "ending_stock_units": ending_stock,
        "ending_inventory_value": ending_inventory_value,
        "build_hours_used": dec(attempted) * hours_per_unit,
        "stock_cover_units": ending_stock,
        "rework_units": failed,
        "loan_cash": loan_cash, "loan_principal": principal,
        "new_owner_cash": owner_cash, "additional_capex": capex,
    }


def apply_approved_step(snapshot: dict, inputs: dict, sim_date: str,
                        run_id: str | None = None,
                        capacity_override: int | None = None) -> tuple[dict, dict, bool]:
    """Apply a month once. Reusing a run_id cannot duplicate a ledger entry."""
    snap = deepcopy(snapshot)
    run_id = run_id or f"RUN-{uuid.uuid4().hex[:10].upper()}"
    if run_id in snap.get("applied_run_ids", []):
        return snap, {}, False
    date.fromisoformat(sim_date)
    result = simulate_rob_month(
        inputs,
        opening_cash=snap["balances"]["cash"],
        opening_stock_units=int(snap["balances"]["stock_units"]),
        capacity_override=capacity_override,
    )
    snap["balances"]["cash"] = str(result["ending_cash"])
    snap["balances"]["stock_units"] = result["ending_stock_units"]
    snap["balances"]["inventory_value"] = str(result["ending_inventory_value"])
    snap["balances"]["debt"] = str(money(dec(snap["balances"]["debt"]) +
                                               result["loan_cash"] - result["loan_principal"]))
    snap["state_version"] = int(snap["state_version"]) + 1
    snap["simulation_date"] = sim_date
    snap["applied_run_ids"].append(run_id)
    snap["ledger"].append({
        "transaction_id": run_id, "date": sim_date, "event_type": "monthly_simulation",
        "category": "robot_kit_sales", "amount": str(result["revenue"]),
        "quantity": result["sold"], "unit_price": str(money(inputs.get("base_price", BASE_PRICE))),
        "offering_id": "ROB-KIT", "campaign_id": None,
        "financing_type": "none", "state_version": snap["state_version"],
        "results": {k: str(v) if isinstance(v, Decimal) else v for k, v in result.items()},
    })
    return snap, result, True


def validate_snapshot_import(incoming: dict, current: dict) -> tuple[bool, str]:
    required = ["team_id", "course", "pathway_id", "snapshot_id", "state_version",
                "balances", "ledger", "applied_run_ids"]
    if not isinstance(incoming, dict) or any(k not in incoming for k in required):
        return False, "Snapshot is missing required fields."
    if incoming["team_id"] != current["team_id"]:
        return False, "team_id mismatch."
    if incoming["pathway_id"] != "ROB-1" or incoming["course"] != "Algebra 2":
        return False, "This app accepts only the ROB-1 Algebra 2 snapshot."
    try:
        if int(incoming["state_version"]) < int(current["state_version"]):
            return False, "stale state_version."
        if int(incoming["balances"]["stock_units"]) < 0:
            return False, "Stock cannot be negative."
        money(incoming["balances"]["cash"])
        ids = [x["transaction_id"] for x in incoming["ledger"]]
        if len(ids) != len(set(ids)):
            return False, "Duplicate transaction IDs in ledger."
    except (KeyError, TypeError, ValueError):
        return False, "Snapshot fields have invalid types or values."
    return True, "Snapshot accepted."


def snapshot_json(snapshot: dict) -> str:
    return json.dumps(snapshot, indent=2)


def algebra2_foundation_breakeven(p0: Any = 120, v: Any = 65,
                                  fixed_cost: Any = 600,
                                  capacity: int = 30) -> dict:
    p, variable, fixed = dec(p0), dec(v), dec(fixed_cost)
    if p <= variable:
        return {"has_positive_breakeven": False, "feasible": False,
                "break_even_exact": None, "whole_units": None,
                "status_label": "No positive break-even: price must exceed variable cost."}
    exact = fixed / (p - variable)
    whole = int(exact.to_integral_value(rounding="ROUND_CEILING"))
    feasible = whole <= int(capacity)
    return {"has_positive_breakeven": True, "feasible": feasible,
            "break_even_exact": exact, "whole_units": whole,
            "status_label": "FEASIBLE" if feasible else "INFEASIBLE: break-even is above capacity."}


def algebra2_applied_demand(price: Any, p0: Any = 120, d0: int = 40) -> Decimal:
    p, base = dec(price), dec(p0)
    if base <= 0:
        raise ValueError("Base price must be positive.")
    if p < 0 or p > 2 * base:
        raise ValueError("Price must be between 0 and twice the base price.")
    return max(Decimal("0"), Decimal(2 * d0) - (Decimal(d0) / base) * p)


def algebra2_advanced_extra_shift(staff_hours: Any = 90,
                                  hours_per_unit: Any = 3,
                                  extra_hours: Any = 30,
                                  extra_hourly_rate: Any = 20,
                                  p0: Any = 120, v: Any = 65,
                                  fixed_cost: Any = 600,
                                  requested_demand: int = 40) -> dict:
    hours, per_unit = dec(staff_hours), dec(hours_per_unit)
    extra, rate = dec(extra_hours), dec(extra_hourly_rate)
    if per_unit <= 0 or min(hours, extra, rate) < 0:
        raise ValueError("Hours per unit must be positive; other values cannot be negative.")
    base_capacity = floor(hours / per_unit)
    added = floor(extra / per_unit)
    new_capacity = base_capacity + added
    extra_cost = money(extra * rate)
    price, variable, fixed = dec(p0), dec(v), dec(fixed_cost)
    base_sold = min(base_capacity, requested_demand)
    new_sold = min(new_capacity, requested_demand)
    base_profit = money(price * base_sold - variable * base_sold - fixed)
    new_profit = money(price * new_sold - variable * new_sold - fixed - extra_cost)
    return {"base_capacity": base_capacity, "added_capacity": added,
            "new_capacity": new_capacity, "added_fixed_cost": extra_cost,
            "base_profit": base_profit, "new_profit": new_profit}
