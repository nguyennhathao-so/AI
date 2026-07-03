# Verify exact data from Chuong4 docx
from data.models import UserInput, Course, FixedEvent, TimeSlot
from data.data_service import DataService
from engine.constraint_engine import ConstraintEngine
from solver.backtrack_solver import BacktrackSolver
from optimizer.optimizer import Optimizer
from ui.cli_ui import CLIUI


def build_docx_input():
    courses = [
        Course(name="Toán", hours_per_week=10, preferred_days=[], schedule_mode="discrete", max_hours_per_day=2),
        Course(name="Văn", hours_per_week=4, preferred_days=[], schedule_mode="discrete", max_hours_per_day=2),
        Course(name="Anh", hours_per_week=5, preferred_days=[], schedule_mode="discrete", max_hours_per_day=2),
    ]
    fixed_events = [
        FixedEvent("TOEIC", TimeSlot("Thứ 5", "07:00")),
        FixedEvent("TOEIC", TimeSlot("Thứ 5", "08:00")),
        FixedEvent("IELTS", TimeSlot("Thứ 6", "07:00")),
        FixedEvent("IELTS", TimeSlot("Thứ 6", "08:00")),
        FixedEvent("Gym", TimeSlot("Thứ 7", "07:00")),
        FixedEvent("Gym", TimeSlot("Thứ 7", "08:00")),
    ]
    blocked_slots = [
        TimeSlot("Thứ 2", "13:00"),
        TimeSlot("Thứ 3", "21:00"),
    ]
    return UserInput(
        courses=courses,
        fixed_events=fixed_events,
        blocked_slots=blocked_slots,
        max_hours_per_day=4,
    )


def run(use_mrv_lcv=True):
    user_input = build_docx_input()
    ds = DataService()
    csp = ds.normalize(user_input)
    print(f"Variables: {len(csp.variables)}")
    print(f"Fixed slots: {len(csp.fixed_slots)}")
    print(f"Domain size: {len(csp.domains[csp.variables[0]])}")
    engine = ConstraintEngine(csp)
    engine.build_constraints()
    print(f"Domain after AC-3: {len(csp.domains[csp.variables[0]])}")
    solver = BacktrackSolver(csp, engine, max_solutions=10)
    if not use_mrv_lcv:
        solver._select_variable_mrv = lambda u, d: u[0]
        solver._order_values_lcv = lambda vn, a, d: d.get(vn, [])
    schedules = solver.solve()
    if schedules:
        opt = Optimizer(schedules)
        best = opt.select_best()
        scores = [s[0] for s in opt.get_all_scores()]
        print(f"Scores: {scores}")
        ui = CLIUI()
        ui.display_schedule(best, user_input.fixed_events)
    return solver._call_count, len(schedules)


if __name__ == "__main__":
    print("=== DOCX DATA ===")
    c1, n1 = run(True)
    print(f"WITH heuristics: recursion={c1}, solutions={n1}")
    c2, n2 = run(False)
    print(f"WITHOUT heuristics: recursion={c2}, solutions={n2}")
