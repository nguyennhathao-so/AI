# ============================================================
# demo.py — Chạy thử với dữ liệu mẫu (không cần nhập tay)
#
# Dùng để test nhanh toàn bộ pipeline:
#   python demo.py
#
# Dữ liệu mẫu: sinh viên có 3 môn tự học, 2 lịch cố định
# ============================================================

from data.models import (
    UserInput, Course, FixedEvent, TimeSlot
)
from data.data_service import DataService
from engine.constraint_engine import ConstraintEngine
from solver.backtrack_solver import BacktrackSolver
from optimizer.optimizer import Optimizer
from ui.cli_ui import CLIUI


def run_demo():
    print("=" * 55)
    print("   DEMO — Chạy với dữ liệu mẫu")
    print("=" * 55)

    # Môn học cần xếp (biến CSP)
    courses = [
        Course(
            name="Giải tích",
            hours_per_week=3,
            preferred_days=["Thứ 2", "Thứ 4"],
            schedule_mode="consecutive_weekly",  # 3 tiếng phải học liền nhau trong một ngày
            max_hours_per_day=3
        ),
        Course(
            name="Lập trình",
            hours_per_week=2,
            preferred_days=[],
            schedule_mode="consecutive_daily",   # 2 tiếng học trong ngày phải liền nhau
            max_hours_per_day=2
        ),
        Course(
            name="Tiếng Anh",
            hours_per_week=2,
            preferred_days=["Thứ 3", "Thứ 5"],
            schedule_mode="discrete",            # Có thể học rời rạc
            max_hours_per_day=2
        ),
    ]

    # Lịch cố định không thể thay đổi (ràng buộc cứng)
    fixed_events = [
        FixedEvent("Học Vật lý trên trường", TimeSlot("Thứ 2", "07:00"), "school"),
        FixedEvent("Học Hóa trên trường",    TimeSlot("Thứ 2", "08:00"), "school"),
        # Ca làm tối (giờ đó đêm đó - không được tranh slot)
        FixedEvent("Ca làm thêm tối",        TimeSlot("Thứ 6", "18:00"), "work"),
        FixedEvent("Ca làm thêm tối",        TimeSlot("Thứ 6", "19:00"), "work"),
        FixedEvent("Ca làm thêm tối",        TimeSlot("Thứ 6", "20:00"), "work"),
    ]


    user_input = UserInput(
        courses=courses,
        fixed_events=fixed_events,
        free_slots=[],           # Rỗng = dùng toàn bộ tuần
        max_hours_per_day=3,
    )

    # ---- Pipeline CSP ----
    print("\n[1/4] DataService: chuẩn hóa dữ liệu...")
    data_service = DataService()
    csp_problem = data_service.normalize(user_input)

    # In domain của từng biến
    for var_name in csp_problem.variables:
        domain_size = len(csp_problem.domains[var_name])
        print(f"      Domain '{var_name}': {domain_size} slot khả dụng")

    print("\n[2/4] ConstraintEngine: xây ràng buộc + AC-3...")
    engine = ConstraintEngine(csp_problem)
    engine.build_constraints()

    # In domain sau AC-3
    for var_name in csp_problem.variables:
        domain_size = len(csp_problem.domains[var_name])
        print(f"      Domain '{var_name}' sau AC-3: {domain_size} slot")


    print("\n[3/4] Solver: backtracking + MRV + LCV + Forward Checking...")
    solver = BacktrackSolver(csp_problem, engine, max_solutions=5)
    valid_schedules = solver.solve()

    if not valid_schedules:
        print("\n❌ Không tìm được lịch hợp lệ với dữ liệu mẫu này.")
        return

    print(f"[4/4] Optimizer: chọn lịch tốt nhất trong {len(valid_schedules)} lịch hợp lệ...")
    optimizer = Optimizer(valid_schedules)
    best = optimizer.select_best()

    # Hiển thị kết quả
    ui = CLIUI()
    ui.display_schedule(best)

    # Hiển thị điểm tất cả lịch để so sánh
    print("\n  Điểm tất cả lịch tìm được:")
    for score, sched in optimizer.get_all_scores():
        print(f"    Score: {score:.1f}")


if __name__ == "__main__":
    run_demo()
