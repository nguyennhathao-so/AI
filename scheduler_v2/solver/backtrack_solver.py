# ============================================================
# solver/backtrack_solver.py — Thuật toán tìm kiếm backtracking
#
# NHIỆM VỤ: Tìm tất cả (hoặc một số) lịch hợp lệ thỏa mãn
# mọi ràng buộc cứng. Đây là core thuật toán TTNT của đề tài.
#
# ĐÂY LÀ PHẦN AI TRỌNG TÂM:
#   - Backtracking search: duyệt cây không gian tìm kiếm
#   - MRV (Minimum Remaining Values): heuristic chọn biến
#   - LCV (Least Constraining Value): heuristic chọn giá trị
#   - Forward Checking: kiểm tra sớm để cắt nhánh
#
# Nếu thầy hỏi "thuật toán AI nào?", đây là câu trả lời.
# ============================================================

from data.models import CSPProblem, Assignment, Schedule
from engine.constraint_engine import ConstraintEngine
from typing import List, Optional
import copy


class BacktrackSolver:

    def __init__(self, problem: CSPProblem, engine: ConstraintEngine, max_solutions: int = 10):
        self.problem = problem
        self.engine = engine
        self.max_solutions = max_solutions   # Giới hạn số lịch tìm được (tránh chạy mãi)
        self._solutions: List[Schedule] = []
        self._call_count = 0                 # Đếm số lần gọi đệ quy (để báo cáo)

    # ----------------------------------------------------------
    # Điểm vào chính
    # ----------------------------------------------------------

    def solve(self) -> List[Schedule]:
        """
        Bắt đầu backtracking từ trạng thái rỗng.
        Trả về danh sách các Schedule hợp lệ tìm được.
        """
        print("\n[Solver] Bắt đầu tìm kiếm backtracking...")
        self._solutions = []
        self._call_count = 0

        # Tạo bản sao domain để không ảnh hưởng bản gốc
        domains = {
            var_name: list(slots)
            for var_name, slots in self.problem.domains.items()
        }

        self._backtrack(assignments=[], domains=domains)

        print(f"[Solver] Kết thúc. Số lần đệ quy: {self._call_count}")
        print(f"[Solver] Tìm được {len(self._solutions)} lịch hợp lệ.\n")
        return self._solutions

    # ----------------------------------------------------------
    # Hàm backtracking đệ quy
    # ----------------------------------------------------------

    def _backtrack(self, assignments: List[Assignment], domains: dict):
        """
        Đệ quy backtracking:
        1. Nếu đã xếp xong tất cả môn → lưu kết quả
        2. Chọn môn tiếp theo bằng MRV heuristic
        3. Thử từng slot theo thứ tự LCV heuristic
        4. Nếu hợp lệ → đệ quy sâu hơn
        5. Nếu không hợp lệ → quay lui (backtrack)
        """
        self._call_count += 1

        # Điều kiện dừng: đã tìm đủ số lịch
        if len(self._solutions) >= self.max_solutions:
            return

        unassigned = self._get_unassigned(assignments)
        if not unassigned:
            schedule = Schedule(
                assignments=list(assignments),
                fixed_events=self.problem.fixed_events
            )
            # Kiểm tra trùng lặp trước khi lưu
            slots_new = set((a.course.name, a.slot.day, a.slot.time) for a in assignments)
            is_dup = any(
                slots_new == set((a.course.name, a.slot.day, a.slot.time) for a in s.assignments)
                    for s in self._solutions
            )
            if not is_dup:
                self._solutions.append(schedule)
            return

        # --- Bước 1: Chọn biến (giờ học) tiếp theo bằng MRV ---
        var_name = self._select_variable_mrv(unassigned, domains)

        # --- Bước 2: Thử từng giá trị (slot) theo LCV ---
        ordered_slots = self._order_values_lcv(var_name, assignments, domains)

        for slot in ordered_slots:
            course_name = var_name.split("_h")[0]
            course_obj = self.problem.courses_dict[course_name]
            new_assignment = Assignment(var_name=var_name, course=course_obj, slot=slot)

            # Kiểm tra ràng buộc cứng
            if not self.engine.is_consistent(assignments, new_assignment):
                continue  # Slot này vi phạm → thử slot khác

            # --- Forward Checking: thu hẹp domain của các môn chưa xếp ---
            new_domains = self._forward_check(new_assignment, domains, assignments)
            if new_domains is None:
                continue  # Forward check thất bại → cắt nhánh này

            # Hợp lệ → thêm vào và đệ quy sâu hơn
            assignments.append(new_assignment)
            self._backtrack(assignments, new_domains)
            assignments.pop()  # Backtrack: xóa assignment vừa thêm


    # ----------------------------------------------------------
    # MRV — Minimum Remaining Values Heuristic
    # ----------------------------------------------------------

    def _select_variable_mrv(self, unassigned_vars, domains):
        """
        Chọn biến (giờ học) có ít slot khả dụng nhất trong domain.
        """
        return min(
            unassigned_vars,
            key=lambda var_name: len(domains.get(var_name, []))
        )

    # ----------------------------------------------------------
    # LCV — Least Constraining Value Heuristic
    # ----------------------------------------------------------

    def _order_values_lcv(self, var_name, assignments: List[Assignment], domains: dict) -> list:
        """
        Sắp xếp các slot của môn theo thứ tự ưu tiên:
        slot ít ảnh hưởng đến các môn khác được thử trước.
        """
        def count_conflicts(slot):
            """
            Đếm số slot bị loại ở các biến khác nếu chọn slot này.
            """
            assigned_vars = {a.var_name for a in assignments}
            conflicts = 0
            for other_var in self.problem.variables:
                if other_var == var_name:
                    continue
                if other_var in assigned_vars:
                    continue
                # Slot bị loại nếu trùng với slot đang xét
                if slot in domains.get(other_var, []):
                    conflicts += 1
            return conflicts

        slots = domains.get(var_name, [])
        return sorted(slots, key=count_conflicts)

    # ----------------------------------------------------------
    # Forward Checking
    # ----------------------------------------------------------

    def _forward_check(self, new_assignment: Assignment, domains: dict, current: list):
        new_domains = copy.deepcopy(domains)
        assigned_vars = {a.var_name for a in current} | {new_assignment.var_name}

        for var in self.problem.variables:
            if var in assigned_vars:
                continue

            # Loại slot vừa dùng khỏi domain của biến này
            if new_assignment.slot in new_domains.get(var, []):
                new_domains[var].remove(new_assignment.slot)

            course_name = var.split("_h")[0]
            course = self.problem.courses_dict[course_name]

            # ===== Giới hạn giờ/ngày =====
            if var.startswith(course_name):          # FIX 1: toàn bộ block nằm trong if này
                count_same_course_day = 0
                for a in current + [new_assignment]:
                    if a.course.name == course_name:
                        if a.slot.day == new_assignment.slot.day:
                            count_same_course_day += 1

                if count_same_course_day >= course.max_hours_per_day:
                    new_domains[var] = [
                        s for s in new_domains[var]
                        if s.day != new_assignment.slot.day
                    ]

            # ===== Liên tục tuần =====
            if course.schedule_mode == "consecutive_weekly":
                chosen_day = new_assignment.slot.day
                chosen_hour = int(new_assignment.slot.time.split(":")[0])

                new_domains[var] = [                 # FIX 2: list comprehension thay vì remove trong loop
                    s for s in new_domains[var]
                    if s.day == chosen_day
                    and abs(int(s.time.split(":")[0]) - chosen_hour) <= 1
                ]

            # Domain rỗng → cắt nhánh
            if len(new_domains.get(var, [])) == 0:
                return None

        return new_domains

    # ----------------------------------------------------------
    # Tiện ích
    # ----------------------------------------------------------

    def _get_unassigned(self, assignments: List[Assignment]):
        """
        Trả về danh sách các biến (giờ học) chưa được xếp lịch.
        """
        assigned_vars = {a.var_name for a in assignments}
        return [v for v in self.problem.variables if v not in assigned_vars]

