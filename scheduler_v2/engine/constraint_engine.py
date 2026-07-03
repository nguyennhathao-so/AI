# ============================================================
# engine/constraint_engine.py — Bộ máy ràng buộc CSP
#
# NHIỆM VỤ: Định nghĩa và kiểm tra ràng buộc. Đây là
# trái tim của mô hình CSP:
#   - Ràng buộc cứng (HARD): vi phạm → lịch không hợp lệ
#   - Ràng buộc mềm (SOFT): vi phạm → trừ điểm chất lượng
#   - AC-3 propagation: thu hẹp domain trước khi solver chạy
#
# ĐÂY LÀ PHẦN AI CHÍNH: AC-3 là thuật toán lan truyền
# ràng buộc kinh điển trong TTNT, giúp cắt tỉa không gian
# tìm kiếm trước khi backtracking bắt đầu.
# ============================================================

from collections import deque
from data.models import CSPProblem, TimeSlot, Assignment
from typing import List


class ConstraintEngine:

    def __init__(self, problem: CSPProblem):
        self.problem = problem
        # Danh sách hàm ràng buộc cứng — mỗi hàm nhận assignment hiện tại
        # và assignment mới, trả về True nếu KHÔNG vi phạm
        self.hard_constraints = []
        # Danh sách hàm ràng buộc mềm — trả về penalty (số âm) nếu vi phạm
        self.soft_constraints = []

    # ----------------------------------------------------------
    # Bước khởi tạo: đăng ký tất cả ràng buộc
    # ----------------------------------------------------------

    def build_constraints(self):
        """
        Đăng ký toàn bộ ràng buộc và chạy AC-3 để thu hẹp domain.
        Gọi hàm này một lần trước khi solver bắt đầu.
        """
        # Ràng buộc cứng
        self.hard_constraints = [
            self._no_slot_overlap,               # Không xếp 2 môn cùng slot
            self._not_in_fixed_slot,             # Không đụng lịch cố định
            self._check_course_daily_limit,      # Không học quá số giờ tối đa/ngày của môn
            self._consecutive_daily_constraint,  # Học liên tục trong ngày (nếu yêu cầu)
            self._consecutive_weekly_constraint, # Học liên tục cả tuần (nếu yêu cầu)
        ]

        # Ràng buộc mềm
        self.soft_constraints = [
            self._penalty_consecutive,      # Phạt nếu học quá 3 slot liên tiếp
            self._penalty_over_daily_limit, # Phạt nếu vượt giới hạn giờ/ngày
            self._penalty_uneven_spread,    # Phạt nếu dồn lịch vào 1-2 ngày
        ]

        # Chạy AC-3 để cắt tỉa domain
        self.ac3()

    # ----------------------------------------------------------
    # Kiểm tra ràng buộc — Solver gọi hàm này khi thử 1 slot
    # ----------------------------------------------------------

    def is_consistent(self, current_assignments: List[Assignment], new_assignment: Assignment) -> bool:
        """
        Kiểm tra xem new_assignment có vi phạm ràng buộc cứng không.
        Trả về True = hợp lệ, False = vi phạm → backtrack.
        """
        for constraint in self.hard_constraints:
            if not constraint(current_assignments, new_assignment):
                return False
        return True

    def compute_soft_penalty(self, assignments: List[Assignment]) -> float:
        """
        Tính tổng penalty của lịch hiện tại.
        Optimizer dùng giá trị này để so sánh các lịch hợp lệ.
        Penalty càng thấp → lịch càng tốt.
        """
        total_penalty = 0.0
        for constraint in self.soft_constraints:
            total_penalty += constraint(assignments)
        return total_penalty

    # ----------------------------------------------------------
    # AC-3: Arc Consistency Algorithm (thuật toán TTNT)
    # ----------------------------------------------------------

    def ac3(self):
        """
        Thu hẹp domain của các biến bằng cách lan truyền ràng buộc.
        """
        variables = self.problem.variables
        domains = self.problem.domains

        # Tạo hàng đợi các cặp biến (arc) cần kiểm tra
        queue = deque()
        for i in range(len(variables)):
            for j in range(len(variables)):
                if i != j:
                    queue.append((variables[i], variables[j]))

        while queue:
            xi, xj = queue.popleft()

            # Kiểm tra và thu hẹp domain của xi so với xj
            if self._revise(xi, xj, domains):
                if len(domains[xi]) == 0:
                    print(f"  [AC-3] Domain của '{xi}' rỗng — không có lịch hợp lệ!")
                    return False
                for xk in variables:
                    if xk != xi and xk != xj:
                        queue.append((xk, xi))
        return True

    def _revise(self, xi, xj, domains) -> bool:
        """
        Thu hẹp domain của xi.
        """
        revised = False
        to_remove = []

        for slot_i in domains[xi]:
            can_find_compatible = any(
                slot_i != slot_j   # Ràng buộc cơ bản: không cùng slot
                for slot_j in domains[xj]
            )
            if not can_find_compatible:
                to_remove.append(slot_i)
                revised = True

        for slot in to_remove:
            domains[xi].remove(slot)

        return revised

    # ----------------------------------------------------------
    # Ràng buộc cứng mới (HARD CONSTRAINTS)
    # ----------------------------------------------------------

    def _check_course_daily_limit(self, current: List[Assignment], new: Assignment) -> bool:
        """
        HARD: Kiểm tra không cho học vượt quá số tiếng tối đa trong ngày của môn đó.
        """
        course_name = new.var_name.split("_h")[0]
        course = self.problem.courses_dict.get(course_name)
        if not course:
            return True

        day = new.slot.day
        count = sum(1 for a in current if a.var_name.split("_h")[0] == course_name and a.slot.day == day)

        if count + 1 > course.max_hours_per_day:
            return False
        return True

    def _consecutive_daily_constraint(self, current: List[Assignment], new: Assignment) -> bool:
        """
        HARD: Nếu môn yêu cầu học liên tục trong ngày, kiểm tra xem slot mới có liền kề
        các slot cũ cùng ngày hay không.
        """
        course_name = new.var_name.split("_h")[0]
        course = self.problem.courses_dict.get(course_name)
        if not course or course.schedule_mode != "consecutive_daily":
            return True

        day = new.slot.day
        times = [new.slot.time]
        for a in current:
            if a.var_name.split("_h")[0] == course_name and a.slot.day == day:
                times.append(a.slot.time)

        if len(times) <= 1:
            return True

        hours = sorted([int(t.split(":")[0]) for t in times])
        if hours[-1] - hours[0] == len(hours) - 1:
            return True
        return False

    def _consecutive_weekly_constraint(self, current: List[Assignment], new: Assignment) -> bool:
        """
        HARD: Nếu môn yêu cầu học liên tục cả tuần, tất cả slot trong tuần phải ở cùng 1 ngày
        và liền kề nhau.
        """
        course_name = new.var_name.split("_h")[0]
        course = self.problem.courses_dict.get(course_name)
        if not course or course.schedule_mode != "consecutive_weekly":
            return True

        course_assignments = [new]
        for a in current:
            if a.var_name.split("_h")[0] == course_name:
                course_assignments.append(a)

        # 1. Phải cùng ngày học
        day = new.slot.day
        if any(a.slot.day != day for a in course_assignments):
            return False

        if len(course_assignments) <= 1:
            return True

        # 2. Phải liên tục nhau
        hours = sorted([int(a.slot.time.split(":")[0]) for a in course_assignments])
        if hours[-1] - hours[0] == len(hours) - 1:
            return True
        return False


    # ----------------------------------------------------------
    # Ràng buộc cứng (HARD CONSTRAINTS)
    # ----------------------------------------------------------

    def _no_slot_overlap(self, current: List[Assignment], new: Assignment) -> bool:
        """
        HARD: Không được xếp 2 môn vào cùng 1 TimeSlot.
        Đây là ràng buộc cơ bản nhất — vi phạm = lịch vô nghĩa.
        """
        used_slots = {a.slot for a in current}
        return new.slot not in used_slots

    def _not_in_fixed_slot(self, current: List[Assignment], new: Assignment) -> bool:
        """
        HARD: Không được xếp vào slot đã bị chiếm bởi
        lịch trường hoặc ca làm thêm.
        """
        fixed_set = set(self.problem.fixed_slots)
        return new.slot not in fixed_set

    # ----------------------------------------------------------
    # Ràng buộc mềm (SOFT CONSTRAINTS — trả về penalty)
    # ----------------------------------------------------------

    def _penalty_consecutive(self, assignments: List[Assignment]) -> float:
        """
        SOFT: Phạt nếu học liên tiếp quá 3 slot trong cùng một ngày.
        Lý do: học liên tục > 3 tiếng không hiệu quả.
        Penalty: -10 điểm cho mỗi slot vượt quá 3 slot liên tiếp.
        """
        penalty = 0.0
        # Nhóm slot theo ngày
        by_day = {}
        for a in assignments:
            day = a.slot.day
            by_day.setdefault(day, []).append(a.slot.time)

        for day, times in by_day.items():
            times_sorted = sorted(times)
            # Đếm chuỗi liên tiếp
            streak = 1
            for i in range(1, len(times_sorted)):
                # Kiểm tra 2 slot có liền nhau không (cách nhau 1 tiếng)
                prev_idx = self._time_index(times_sorted[i - 1])
                curr_idx = self._time_index(times_sorted[i])
                if curr_idx - prev_idx == 1:
                    streak += 1
                    if streak > 3:
                        penalty -= 10.0  # Phạt mỗi slot vượt 3 liên tiếp
                else:
                    streak = 1
        return penalty

    def _penalty_over_daily_limit(self, assignments: List[Assignment]) -> float:
        """
        SOFT: Phạt nếu tổng số slot học trong ngày vượt max_hours_per_day.
        Penalty: -15 điểm cho mỗi slot vượt giới hạn.
        """
        penalty = 0.0
        limit = self.problem.max_hours_per_day
        by_day = {}
        for a in assignments:
            by_day.setdefault(a.slot.day, 0)
            by_day[a.slot.day] += 1

        for day, count in by_day.items():
            if count > limit:
                penalty -= 15.0 * (count - limit)
        return penalty

    def _penalty_uneven_spread(self, assignments: List[Assignment]) -> float:
        """
        SOFT: Phạt nếu lịch học bị dồn vào ít ngày.
        Lý do: phân bổ đều trong tuần giúp tiếp thu tốt hơn.
        Penalty: -5 điểm nếu số ngày học < một nửa số ngày có thể học.
        """
        if not assignments:
            return 0.0
        days_used = len(set(a.slot.day for a in assignments))
        total_days = 6  # Thứ 2 đến Thứ 7
        if days_used < total_days / 2:
            return -5.0 * (total_days // 2 - days_used)
        return 0.0

    # ----------------------------------------------------------
    # Tiện ích
    # ----------------------------------------------------------

    def _time_index(self, time_str: str) -> int:
        """
        Chuyển "07:00" → 7, "08:00" → 8, ... để so sánh thứ tự theo giờ thực tế.
        """
        try:
            return int(time_str.split(":")[0])
        except (ValueError, IndexError):
            return -1
