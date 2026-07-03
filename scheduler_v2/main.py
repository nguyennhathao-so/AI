# ============================================================
# main.py — Điểm khởi động của toàn bộ ứng dụng
# Chạy file này để bắt đầu: python main.py
# ============================================================

from data.data_service import DataService
from engine.constraint_engine import ConstraintEngine
from solver.backtrack_solver import BacktrackSolver
from optimizer.optimizer import Optimizer
from ui.cli_ui import CLIUI
from constraints.conflict_detector import detect_conflicts


def main():
    ui = CLIUI()

    # Bước 1: UI thu thập dữ liệu từ người dùng
    raw_input = ui.collect_input()

    # Chạy conflict detector để kiểm tra xung đột trước
    all_slots = DataService.generate_all_slots()
    fixed_slots = {event.slot for event in raw_input.fixed_events}
    available_slots = [s for s in all_slots if s not in fixed_slots]

    errors = detect_conflicts(raw_input, available_slots)
    if errors:
        ui.show_conflicts(errors)
        return

    # Bước 2: DataService chuẩn hóa thành bài toán CSP
    data_service = DataService()
    csp_problem = data_service.normalize(raw_input)

    # Bước 3: ConstraintEngine tạo và kiểm tra ràng buộc
    engine = ConstraintEngine(csp_problem)
    engine.build_constraints()

    # Bước 4: Solver tìm tất cả lịch hợp lệ bằng backtracking
    solver = BacktrackSolver(csp_problem, engine)
    valid_schedules = solver.solve()

    if not valid_schedules:
        ui.show_no_solution()
        return

    # Bước 5: Optimizer chọn lịch tốt nhất
    optimizer = Optimizer(valid_schedules)
    best_schedule = optimizer.select_best()

    # Bước 6: UI hiển thị kết quả
    ui.display_schedule(
        best_schedule,
        raw_input.fixed_events
    )



if __name__ == "__main__":
    main()
