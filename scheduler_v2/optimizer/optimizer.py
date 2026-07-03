# ============================================================
# optimizer/optimizer.py — Chọn lịch tốt nhất
#
# NHIỆM VỤ: Nhận danh sách các Schedule hợp lệ từ Solver,
# tính điểm chất lượng cho từng lịch và trả về lịch tốt nhất.
#
# ĐÂY LÀ PHẦN AI: Hàm scoring là "objective function" —
# tương tự local search / greedy optimization. Có thể mở
# rộng thành Hill Climbing hoặc Simulated Annealing.
# ============================================================

from data.models import Schedule, Assignment
from typing import List
from data.models import TIME_SLOTS


class Optimizer:

    def __init__(self, schedules: List[Schedule]):
        self.schedules = schedules

    def select_best(self) -> Schedule:
        """
        Tính điểm tất cả các lịch và trả về lịch có điểm cao nhất.
        Điểm bắt đầu từ 100, trừ dần theo các tiêu chí chất lượng.
        """
        print("[Optimizer] Đang đánh giá các lịch hợp lệ...")

        for schedule in self.schedules:
            schedule.score = self._score(schedule)

        best = max(self.schedules, key=lambda s: s.score)
        print(f"[Optimizer] Lịch tốt nhất có điểm: {best.score:.1f}\n")
        return best

    # ----------------------------------------------------------
    # Hàm tính điểm tổng hợp (Objective Function)
    # ----------------------------------------------------------

    def _score(self, schedule: Schedule) -> float:
        """
        Tính điểm chất lượng cho một lịch.
        Điểm tối đa: 100. Trừ điểm theo các tiêu chí bên dưới.

        Tiêu chí:
          + Phân bổ đều theo ngày trong tuần
          + Ưu tiên buổi sáng
          - Phạt học quá nhiều slot liên tiếp
          - Phạt lịch dồn vào ít ngày
        """
        score = 100.0
        assignments = schedule.assignments

        score += self._bonus_even_spread(assignments)
        score += self._bonus_course_preferences(assignments)
        score += self._penalty_consecutive_slots(assignments)
        score += self._penalty_heavy_days(assignments)

        return max(0, min(score, 100))

    # ----------------------------------------------------------
    # Điểm thưởng (BONUS)
    # ----------------------------------------------------------

    def _bonus_even_spread(self, assignments: List[Assignment]) -> float:
        """
        Thưởng nếu lịch học được phân bổ đều theo ngày.
        Tối đa +20 điểm.

        Lý do: Học rải đều trong tuần giúp não có thời gian
        củng cố kiến thức qua giấc ngủ (spaced repetition).
        """
        if not assignments:
            return 0.0

        days_used = set(a.slot.day for a in assignments)
        # Càng nhiều ngày khác nhau → điểm càng cao
        bonus = len(days_used) * 2
        return bonus



    # ----------------------------------------------------------
    # Điểm phạt (PENALTY)
    # ----------------------------------------------------------

    def _bonus_course_preferences(
        self,
        assignments: List[Assignment]
    ) -> float:
        """
        Thưởng nếu môn có ít nhất 1 slot
        đúng ngày/giờ ưu tiên.

        Preferred là soft constraint:
        - Có thì cộng điểm
        - Không có vẫn hợp lệ
        """

        bonus = 0.0

        for a in assignments:
            course = a.course


            # ưu tiên ngày
            if course.preferred_days:
                if a.slot.day in course.preferred_days:
                    bonus += 1

            # ưu tiên giờ
            if course.preferred_times:
                if a.slot.time in course.preferred_times:
                    bonus += 1

        return min(bonus, 30)

    def _penalty_consecutive_slots(self, assignments: List[Assignment]) -> float:
        """
        Phạt nếu học liên tiếp quá 3 slot trong một ngày.
        -8 điểm cho mỗi slot vượt quá 3 liên tiếp.
        """
        penalty = 0.0
        by_day = {}
        for a in assignments:
            by_day.setdefault(a.slot.day, []).append(a.slot.time)

        for day, times in by_day.items():
            sorted_times = sorted(times, key=lambda t: int(t.split(":")[0]))
            streak = 1
            for i in range(1, len(sorted_times)):
                prev_hour = int(sorted_times[i - 1].split(":")[0])
                curr_hour = int(sorted_times[i].split(":")[0])
                if curr_hour - prev_hour == 1:
                    streak += 1
                    if streak > 3:
                        penalty -= 5.0
                else:
                    streak = 1
        return penalty


    def _penalty_heavy_days(self, assignments: List[Assignment]) -> float:
        """
        Phạt nếu một ngày có quá nhiều slot học (> 4 slot).
        -10 điểm cho mỗi slot vượt quá 4 trong một ngày.
        """
        penalty = 0.0
        by_day = {}
        for a in assignments:
            by_day.setdefault(a.slot.day, 0)
            by_day[a.slot.day] += 1

        for day, count in by_day.items():
            if count > 4:
                penalty -= 5.0 * (count - 4)
        return penalty

    # ----------------------------------------------------------
    # Tiện ích: xem tất cả điểm để debug
    # ----------------------------------------------------------

    def get_all_scores(self) -> List[tuple]:
        """
        Trả về danh sách (score, schedule) đã sắp xếp để debug.
        """
        return sorted(
            [(s.score, s) for s in self.schedules],
            key=lambda x: x[0],
            reverse=True
        )
    def score_all(self):
        for schedule in self.schedules:
            schedule.score = self._score(schedule)
