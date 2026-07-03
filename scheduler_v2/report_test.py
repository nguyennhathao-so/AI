# Script chạy thử dữ liệu báo cáo Chương 4
from data.models import UserInput, Course, FixedEvent, TimeSlot, DAYS, TIME_SLOTS
from data.data_service import DataService
from engine.constraint_engine import ConstraintEngine
from solver.backtrack_solver import BacktrackSolver
from optimizer.optimizer import Optimizer
from ui.cli_ui import CLIUI


def build_report_input():
    courses = [
        Course(name="Toán", hours_per_week=10, preferred_days=[], schedule_mode="discrete", max_hours_per_day=4),
        Course(name="Văn", hours_per_week=4, preferred_days=[], schedule_mode="discrete", max_hours_per_day=3),
        Course(name="Anh", hours_per_week=5, preferred_days=[], schedule_mode="discrete", max_hours_per_day=3),
    ]

    fixed_events = [
        FixedEvent("Toiec", TimeSlot("Thứ 5", "18:00")),
        FixedEvent("Toiec", TimeSlot("Thứ 5", "19:00")),
        FixedEvent("IELTS", TimeSlot("Thứ 6", "18:00")),
        FixedEvent("IELTS", TimeSlot("Thứ 6", "19:00")),
        FixedEvent("IELTS", TimeSlot("Thứ 6", "20:00")),
        FixedEvent("Gym", TimeSlot("Thứ 7", "07:00")),
        FixedEvent("Gym", TimeSlot("Thứ 7", "08:00")),
    ]

    # Một vài blocked slot (không học buổi tối Thứ 2, Thứ 3)
    blocked_slots = [
        TimeSlot("Thứ 2", "20:00"),
        TimeSlot("Thứ 2", "21:00"),
        TimeSlot("Thứ 3", "20:00"),
        TimeSlot("Thứ 3", "21:00"),
    ]

    return UserInput(
        courses=courses,
        fixed_events=fixed_events,
        blocked_slots=blocked_slots,
        max_hours_per_day=4,
    )


def print_csp_stats(csp_problem, label=""):
    total_slots = len(DAYS) * len(TIME_SLOTS)
    print(f"\n=== CSP Stats {label} ===")
    print(f"Tổng slot trong tuần: {total_slots}")
    print(f"Số biến CSP: {len(csp_problem.variables)}")
    print(f"Tổng giờ cần xếp: {sum(c.hours_per_week for c in csp_problem.courses)}")
    print(f"Lịch cố định chiếm: {len(csp_problem.fixed_slots)} slot")
    for var in csp_problem.variables:
        print(f"  {var}: domain = {len(csp_problem.domains[var])} slot")


def run_with_heuristics(use_mrv_lcv=True, max_solutions=10):
    user_input = build_report_input()
    ds = DataService()
    csp = ds.normalize(user_input)
    print_csp_stats(csp, "ban đầu (trước AC-3)")

    engine = ConstraintEngine(csp)
    engine.build_constraints()
    print_csp_stats(csp, "sau AC-3")

    solver = BacktrackSolver(csp, engine, max_solutions=max_solutions)
    if not use_mrv_lcv:
        solver._select_variable_mrv = lambda unassigned, domains: unassigned[0]
        solver._order_values_lcv = lambda var_name, assignments, domains: domains.get(var_name, [])

    schedules = solver.solve()
    if schedules:
        opt = Optimizer(schedules)
        best = opt.select_best()
        print("\nĐiểm tất cả lịch:")
        for score, _ in opt.get_all_scores():
            print(f"  {score:.1f}")
        ui = CLIUI()
        ui.display_schedule(best, user_input.fixed_events)
    return solver._call_count, len(schedules), schedules


if __name__ == "__main__":
    print("=" * 60)
    print("  BÁO CÁO TEST — Dữ liệu Chương 4")
    print("=" * 60)
    print("\n--- Với MRV + LCV + Forward Checking ---")
    calls_with, count_with, _ = run_with_heuristics(use_mrv_lcv=True)
    print(f"\n>>> Kết quả: đệ quy={calls_with}, lịch hợp lệ={count_with}")

    print("\n\n--- KHÔNG dùng MRV/LCV (chọn biến/giá trị theo thứ tự) ---")
    calls_without, count_without, _ = run_with_heuristics(use_mrv_lcv=False)
    print(f"\n>>> Kết quả: đệ quy={calls_without}, lịch hợp lệ={count_without}")
    print(f"\n>>> Tăng số lần đệ quy khi bỏ heuristic: {calls_without - calls_with} ({calls_without/max(calls_with,1):.1f}x)")
