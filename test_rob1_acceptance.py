from decimal import Decimal
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine import (
    default_snapshot, simulate_rob_month, apply_approved_step,
    validate_snapshot_import, algebra2_foundation_breakeven,
    algebra2_applied_demand, algebra2_advanced_extra_shift,
)


def test_official_three_month_fixture():
    cash, stock = Decimal("5000"), 100
    fixture = [
        ("2027-01-31", 40, 30, 0, 30, "3600.00", "2550.00", "1050.00", "6950.00", 70),
        ("2027-02-28", 44, 30, 100, 30, "3600.00", "2650.00", "950.00", "8800.00", 40),
        ("2027-03-31", 36, 22, 0, 22, "2640.00", "2030.00", "610.00", "10070.00", 18),
    ]
    for day, requested, cap, ad, sold, revenue, expense, profit, closing_cash, end_stock in fixture:
        result = simulate_rob_month(
            {"base_price": 120, "requested": requested, "staff_hours": 90,
             "hours_per_unit": 3, "restock_units": 0, "defect_rate": 0, "ad_cost": ad},
            opening_cash=cash, opening_stock_units=stock, capacity_override=cap,
        )
        assert result["sold"] == sold
        assert result["revenue"] == Decimal(revenue)
        assert result["variable_expense"] + result["fixed_expense"] + result["marketing"] == Decimal(expense)
        assert result["operating_profit"] == Decimal(profit)
        assert result["ending_cash"] == Decimal(closing_cash)
        assert result["ending_stock_units"] == end_stock
        cash, stock = result["ending_cash"], result["ending_stock_units"]


def test_normal_capacity_and_zero_sales():
    result = simulate_rob_month({"requested": 0}, opening_cash=5000, opening_stock_units=100)
    assert result["capacity"] == 30
    assert result["revenue"] == Decimal("0.00")
    assert result["variable_expense"] == Decimal("0.00")
    assert result["operating_profit"] == Decimal("-600.00")


def test_low_inventory_business_specific_case():
    result = simulate_rob_month({"requested": 40}, opening_cash=5000, opening_stock_units=10)
    assert result["sold"] == 10
    assert result["revenue"] == Decimal("1200.00")
    assert result["variable_expense"] + result["fixed_expense"] == Decimal("1250.00")
    assert result["operating_profit"] == Decimal("-50.00")
    assert result["ending_stock_units"] == 0


def test_algebra_2_acceptance():
    be = algebra2_foundation_breakeven(120, 65, 600, capacity=30)
    assert be["whole_units"] == 11 and be["feasible"]
    infeasible = algebra2_foundation_breakeven(120, 65, 600, capacity=8)
    assert not infeasible["feasible"]
    no_be = algebra2_foundation_breakeven(65, 65, 600, capacity=30)
    assert not no_be["has_positive_breakeven"]
    assert algebra2_applied_demand(120, 120, 40) == Decimal("40")
    shift = algebra2_advanced_extra_shift(extra_hours=30, extra_hourly_rate=20,
                                          requested_demand=40)
    assert shift["base_capacity"] == 30
    assert shift["added_capacity"] == 10
    assert shift["new_capacity"] == 40
    assert shift["added_fixed_cost"] == Decimal("600.00")
    assert shift["new_profit"] == Decimal("1000.00")


def test_snapshot_duplicate_and_import_validation():
    snap = default_snapshot("TEAM-ROB1")
    updated, _, applied = apply_approved_step(
        snap, {"requested": 0, "loan_cash": "2000.00"},
        "2027-01-31", "RUN-LOAN-1"
    )
    assert applied
    again, _, applied_again = apply_approved_step(
        updated, {"requested": 0, "loan_cash": "2000.00"},
        "2027-01-31", "RUN-LOAN-1"
    )
    assert not applied_again
    assert len(again["ledger"]) == len(updated["ledger"])
    wrong_team = dict(updated, team_id="OTHER")
    assert validate_snapshot_import(wrong_team, updated)[0] is False
    stale = dict(updated, state_version=0)
    assert validate_snapshot_import(stale, updated)[0] is False
