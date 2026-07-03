# ============================================================
# data/data_service.py — Chuẩn hóa dữ liệu đầu vào
#
# NHIỆM VỤ: Nhận UserInput thô, tính toán domain cho từng
# môn học (tức là list các TimeSlot có thể xếp), rồi đóng
# gói thành CSPProblem để Constraint Engine & Solver dùng.
#
# ĐÂY LÀ PHẦN AI: Bước mô hình hóa bài toán CSP —
# chọn domain sai là solver chạy ra kết quả sai.
# ============================================================

from data.models import (
    UserInput, CSPProblem, TimeSlot, FixedEvent,
    DAYS, TIME_SLOTS
)


class DataService:

    def normalize(self, user_input: UserInput) -> CSPProblem:
        """
        Chuyển UserInput → CSPProblem.

        Các bước:
        1. Xác định tất cả slot bị chiếm (fixed_slots)
        2. Với mỗi môn, tính domain = slot rảnh & phù hợp môn đó
        3. Tạo ra các biến theo giờ học (Giải tích_h0, Giải tích_h1...) và gán domain cho từng biến
        4. Đóng gói vào CSPProblem
        """
        # Tập hợp slot đã bị chiếm bởi lịch cố định
        fixed_slots = [event.slot for event in user_input.fixed_events]

        variables = []
        domains = {}
        for course in user_input.courses:
            # Tính domain chung cho môn học
            candidate_slots = self._compute_domain(
                course=course,
                fixed_slots=fixed_slots,
                blocked_slots=user_input.blocked_slots,
            )
            # Tạo biến cho từng giờ học của môn học đó
            for i in range(course.hours_per_week):
                var_name = f"{course.name}_h{i}"
                variables.append(var_name)
                domains[var_name] = list(candidate_slots)

        return CSPProblem(
            variables=variables,
            domains=domains,
            fixed_slots=fixed_slots,
            fixed_events=user_input.fixed_events,
            max_hours_per_day=user_input.max_hours_per_day,
            courses=user_input.courses,
        )

    def _compute_domain(self, course, fixed_slots, blocked_slots):

        candidate_slots = [
            TimeSlot(day=day, time=time)
            for day in DAYS
            for time in TIME_SLOTS
        ]

        # loại giờ cấm
        blocked_set = set(blocked_slots)

        candidate_slots = [
            s for s in candidate_slots
            if s not in blocked_set
        ]


        # loại lịch cố định
        fixed_set = set(fixed_slots)

        candidate_slots = [
            s for s in candidate_slots
            if s not in fixed_set
        ]

        

        if not candidate_slots:
            print(f"[Warning] Môn '{course.name}' không có slot khả dụng sau khi lọc!")
        
        return candidate_slots


    @staticmethod
    def generate_all_slots() -> list:
        """
        Tiện ích: sinh toàn bộ TimeSlot trong một tuần.
        Dùng khi test hoặc debug.
        """
        return [
            TimeSlot(day=day, time=time)
            for day in DAYS
            for time in TIME_SLOTS
        ]
