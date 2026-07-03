# ============================================================
# ui/cli_ui.py — Giao diện dòng lệnh (Command Line Interface)
#
# NHIỆM VỤ: Thu thập dữ liệu từ người dùng và hiển thị kết quả.
# Đây là lớp giao tiếp giữa người dùng và hệ thống CSP bên trong.
# ============================================================

from data.models import (
    UserInput, Course, FixedEvent, TimeSlot,
    Schedule, DAYS, TIME_SLOTS
)


class CLIUI:

    def collect_input(self) -> UserInput:
        """
        Hướng dẫn người dùng nhập thông tin qua terminal.
        Trả về UserInput đã được validate cơ bản.
        """
        print("=" * 55)
        print("   HỆ THỐNG XẾP THỜI KHÓA BIỂU TỰ ĐỘNG (CSP)")
        print("=" * 55)

        courses = self._collect_courses()
        fixed_events = self._collect_fixed_events()
        blocked_slots = self._collect_blocked_slots()
        max_hours = self._collect_max_hours()

        return UserInput(
            courses=courses,
            fixed_events=fixed_events,
            blocked_slots=blocked_slots,
            max_hours_per_day=max_hours,
        )

    # ----------------------------------------------------------
    # Thu thập môn học
    # ----------------------------------------------------------

    def _collect_courses(self) -> list:
        """
        Thu thập danh sách môn cần tự học / học nhóm.
        """
        courses = []
        print("\n[BƯỚC 1] Nhập danh sách môn muốn tự học / học nhóm")
        print("  (Nhấn Enter để kết thúc)\n")

        while True:
            name = input("  Tên môn (Enter để kết thúc): ").strip()
            if not name:
                break

            hours = self._input_int(
                f"  Số tiếng/tuần cho '{name}': ",
                min_val=1, max_val=40
            )

            max_hours_daily = self._input_int(
                f"  Số tiếng tối đa trong một ngày cho '{name}': ",
                min_val=1, max_val=12, default=2
            )

            print("  Hình thức sắp xếp lịch:")
            print("    1. Rời rạc (có thể chia nhỏ các giờ học trong ngày/tuần)")
            print("    2. Liên tục theo ngày (các giờ học trong cùng một ngày phải liền nhau)")
            print("    3. Liên tục cả tuần (tất cả các giờ học trong tuần phải tập trung 1 buổi liền nhau)")
            mode_choice = self._input_int("  Chọn hình thức (1/2/3, Enter = Rời rạc): ", min_val=1, max_val=3, default=1)
            
            mode_map = {1: "discrete", 2: "consecutive_daily", 3: "consecutive_weekly"}
            schedule_mode = mode_map[mode_choice]

            print("  Khung giờ ưu tiên:")
            print("    1. Buổi sáng (07:00 - 12:00)")
            print("    2. Buổi chiều (13:00 - 18:00)")
            print("    3. Buổi tối (18:00 - 22:00)")
            print("    4. Bất kỳ lúc nào")
            time_choice = self._input_int("  Chọn khung giờ (1/2/3/4, Enter = Bất kỳ): ", min_val=1, max_val=4, default=4)
            
            pref_times = []
            if time_choice == 1:
                pref_times = ["07:00", "08:00", "09:00", "10:00", "11:00"]
            elif time_choice == 2:
                pref_times = ["13:00", "14:00", "15:00", "16:00", "17:00"]
            elif time_choice == 3:
                pref_times = ["18:00", "19:00", "20:00", "21:00"]

            pref_days = self._collect_preferred_days(name)

            courses.append(Course(
                name=name,
                hours_per_week=hours,
                max_hours_per_day=max_hours_daily,
                schedule_mode=schedule_mode,
                preferred_times=pref_times,
                preferred_days=pref_days,
            ))
            print(f"  ✓ Đã thêm: {name} ({hours} tiếng/tuần, hình thức: {schedule_mode})\n")

        return courses

    def _collect_preferred_days(self, course_name: str) -> list:
        """
        Chọn ngày ưu tiên bằng số.
        Đây là soft constraint, không bắt buộc.
        """

        print(f"\n  Chọn ngày ưu tiên cho '{course_name}'")
        print("  (Enter = bất kỳ ngày nào)")

        for i, day in enumerate(DAYS):
            print(f"    {i+1}. {day}")

        raw = input("  Chọn ngày (số): ").strip()

        if not raw:
            return []

        try:
            idx = int(raw)

            if idx < 1 or idx > len(DAYS):
                print("  Số không hợp lệ → bỏ qua")
                return []

            return [DAYS[idx - 1]]

        except ValueError:
            print("  Vui lòng nhập số → bỏ qua")
            return []

    # ----------------------------------------------------------
    # Thu thập lịch cố định
    # ----------------------------------------------------------

    def _collect_fixed_events(self) -> list:
        """
        Thu thập lịch học trên trường hoặc ca làm thêm.
        Đây là ràng buộc cứng — solver KHÔNG được xếp vào đây.
        """
        events = []
        print("\n[BƯỚC 2] Nhập lịch cố định (học trên trường, đi làm thêm, đi chơi...)")
        print("  (Nhấn Enter để bỏ qua)\n")

        while True:
            name = input("  Tên lịch cố định (Enter để kết thúc): ").strip()
            if not name:
                break

            # Chọn ngày
            print(f"\n  Chọn ngày cho '{name}':")
            for i, day in enumerate(DAYS):
                print(f"    {i+1}. {day}")
            raw_day = input("  Chọn ngày (số): ").strip()
            if not raw_day:
                continue
            try:
                day_idx = int(raw_day)
                if not (1 <= day_idx <= len(DAYS)):
                    print("  Số không hợp lệ.")
                    continue
            except ValueError:
                print("  Vui lòng nhập số.")
                continue
            day = DAYS[day_idx - 1]

            # Chọn giờ bắt đầu
            print(f"\n  Chọn giờ bắt đầu cho '{name}':")
            for i, t in enumerate(TIME_SLOTS):
                print(f"    {i+1}. {t}", end="  ")
                if (i + 1) % 5 == 0:
                    print()
            print()
            start_choice = self._input_int("  Giờ bắt đầu (số): ", min_val=1, max_val=len(TIME_SLOTS))
            if start_choice is None:
                continue
            start_time = TIME_SLOTS[start_choice - 1]

            # Chọn giờ kết thúc (phải sau giờ bắt đầu)
            start_hour = int(start_time.split(":")[0])
            
            # Liệt kê các giờ kết thúc hợp lý
            end_slots = []
            for t in TIME_SLOTS:
                h = int(t.split(":")[0])
                if h > start_hour:
                    end_slots.append(f"{h:02d}:00")
            
            # Giờ kết thúc cuối cùng (ví dụ: nếu slot cuối là 21:00, giờ kết thúc cuối cùng là 22:00)
            last_slot_hour = int(TIME_SLOTS[-1].split(":")[0])
            end_slots.append(f"{last_slot_hour + 1:02d}:00")

            print(f"\n  Chọn giờ kết thúc cho '{name}':")
            for i, t in enumerate(end_slots):
                print(f"    {i+1}. {t}", end="  ")
                if (i + 1) % 5 == 0:
                    print()
            print()
            end_choice = self._input_int("  Giờ kết thúc (số): ", min_val=1, max_val=len(end_slots))
            if end_choice is None:
                continue
            end_time = end_slots[end_choice - 1]
            end_hour = int(end_time.split(":")[0])

            # Sinh các slot 1 tiếng
            added_slots = []
            for hour in range(start_hour, end_hour):
                slot_time = f"{hour:02d}:00"
                if slot_time in TIME_SLOTS:
                    slot = TimeSlot(day=day, time=slot_time)
                    events.append(FixedEvent(name=name, slot=slot))
                    added_slots.append(slot_time)
            
            print(f"  ✓ Đã thêm: {name} — {day} từ {start_time} đến {end_time} (Tổng cộng {len(added_slots)} tiếng)\n")

        return events

    # ----------------------------------------------------------
    # Thu thập slot rảnh
    # ----------------------------------------------------------

    def _collect_blocked_slots(self) -> list:
        """
        Bước 3 — tùy chọn giới hạn khung giờ học.
        Mặc định: solver dùng toàn bộ tuần trừ lịch cố định.
        """
        print("\n[BƯỚC 3] Nhập giờ KHÔNG ĐƯỢC HỌC (tùy chọn)")
        print("  Mặc định: hệ thống tự xếp vào bất kỳ giờ nào trong tuần,")
        print("  trừ những lịch cố định bạn đã nhập ở Bước 2.")
        print("  Chọn y nếu muốn CHỈ học trong một số khung giờ nhất định.")
        use_free = input("\n  Giới hạn khung giờ học? (y/n, Enter = không): ").strip().lower()
        if use_free != "y":
            print("  → Hệ thống sẽ tự xếp lịch trong toàn bộ tuần.")
            return []

        blocked_slots = []
        print("\n  Nhập các khung giờ KHÔNG MUỐN HỌC:\n")
        while True:
            slot = self._collect_single_slot("  Khung giờ không muốn học")
            if slot is None:
                break
            blocked_slots.append(slot)
            print(f"  ✓ Đã thêm: {slot}")
            more = input("\n  Thêm khung giờ nữa? (y/Enter để kết thúc): ").strip().lower()
            if more != "y":
                break

        return blocked_slots

    def _collect_single_slot(self, label: str) -> TimeSlot:
        print(f"\n  {label}:")
    
        # Chọn ngày — vòng lặp đến khi hợp lệ hoặc Enter để thoát
        while True:
            for i, day in enumerate(DAYS):
                print(f"    {i+1}. {day}")
            print("    (Enter để kết thúc)")
            raw_day = input("    Chọn ngày (số): ").strip()
            if not raw_day:
                return None
            try:
                day_idx = int(raw_day)
                if 1 <= day_idx <= len(DAYS):
                    break
                print("    Số không hợp lệ, vui lòng nhập lại.")
            except ValueError:
                print("    Vui lòng nhập số nguyên.")

        day = DAYS[day_idx - 1]

        # Chọn giờ — vòng lặp đến khi hợp lệ
        while True:
            for i, time in enumerate(TIME_SLOTS):
                print(f"    {i+1}. {time}", end="  ")
                if (i + 1) % 5 == 0:
                    print()
            print()
            raw_time = input("    Chọn giờ (số): ").strip()
            try:
                time_idx = int(raw_time)
                if 1 <= time_idx <= len(TIME_SLOTS):
                    break
                print("    Số không hợp lệ, vui lòng nhập lại.")
            except ValueError:
                print("    Vui lòng nhập số nguyên.")

        time = TIME_SLOTS[time_idx - 1]
        return TimeSlot(day=day, time=time)

    # ----------------------------------------------------------
    # Thu thập giới hạn giờ học
    # ----------------------------------------------------------

    def _collect_max_hours(self) -> int:
        """
        Hỏi số tiếng học tối đa mỗi ngày.
        """
        print("\n[BƯỚC 4] Giới hạn học")
        return self._input_int(
            "  Số tiếng học tối đa tổng cộng mỗi ngày (mặc định 4): ",
            min_val=1, max_val=12,
            default=4
        )

    # ----------------------------------------------------------
    # Hiển thị kết quả
    # ----------------------------------------------------------

    def display_schedule(self, schedule: Schedule, fixed_events=None):
        """
        Hiển thị lịch kết quả theo dạng bảng tuần.
        Nhóm các môn theo ngày để dễ đọc, gộp các slot liên tục.
        """
        print("=" * 65)
        print("   LỊCH HỌC TỐI ƯU")
        print(f"   Điểm chất lượng: {schedule.score:.1f}/100")
        print("=" * 65)

        # Nhóm theo ngày
        by_day = {}
        for a in schedule.assignments:
             
            by_day.setdefault(a.slot.day, []).append(a)

        if fixed_events:
            for event in fixed_events:
                by_day.setdefault(event.slot.day, []).append(
                        event
                )

        for day in DAYS:
            if day not in by_day:
                continue
            print(f"\n  📅 {day}:")
            
            # Sắp xếp theo giờ học
            day_assignments = sorted(
                by_day[day],
                key=lambda a: int(a.slot.time.split(":")[0])
            )
            
            # Gộp các slot học liên tiếp của cùng một môn
            merged_slots = []

            for a in day_assignments:
                start_hour = int(a.slot.time.split(":")[0])
                end_hour = start_hour + 1
                
                if hasattr(a, "course"):
                    name = a.course.name
                else:
                    name = a.name + " (cố định)"

                if (merged_slots and 
                    merged_slots[-1]["course_name"] == name and 
                    merged_slots[-1]["end_hour"] == start_hour):
                    merged_slots[-1]["end_hour"] = end_hour
                else:
                    

                    merged_slots.append({
                        "course_name": name,
                        "start_hour": start_hour,
                        "end_hour": end_hour
                })
            
            # Hiển thị các block sau khi gộp
            for slot in merged_slots:
                start_str = f"{slot['start_hour']:02d}:00"
                end_str = f"{slot['end_hour']:02d}:00"
                print(f"     {start_str} - {end_str}  |  {slot['course_name']}")

        print("\n" + "=" * 65)

    def show_no_solution(self):
        """
        Hiển thị thông báo khi CSP không tìm được lịch hợp lệ.
        Gợi ý người dùng điều chỉnh ràng buộc.
        """
        print("\n" + "=" * 55)
        print("  ❌ KHÔNG TÌM ĐƯỢC LỊCH HỢP LỆ")
        print("=" * 55)
        print("""
  Có thể do:
  1. Quá nhiều lịch cố định chiếm hết slot rảnh
  2. Số tiếng yêu cầu vượt quá slot rảnh còn lại
  3. Slot rảnh khai báo quá ít

  Gợi ý:
  → Giảm số tiếng học/tuần của một số môn
  → Mở rộng khung giờ rảnh
  → Giảm giới hạn max giờ/ngày
        """)
        print("=" * 55)

    def show_conflicts(self, errors: list):
        """
        Hiển thị danh sách các lỗi xung đột đầu vào.
        """
        print("\n" + "=" * 55)
        print("  ❌ XUNG ĐỘT DỮ LIỆU ĐẦU VÀO")
        print("=" * 55)
        for err in errors:
            print(f"  - {err}")
        print("=" * 55)

    # ----------------------------------------------------------
    # Tiện ích nhập số
    # ----------------------------------------------------------

    def _input_int(self, prompt: str, min_val: int = None, max_val: int = None, default: int = None) -> int:
        """
        Nhập số nguyên có validate min/max và giá trị mặc định.
        """
        while True:
            raw = input(prompt).strip()
            if not raw and default is not None:
                return default
            try:
                val = int(raw)
                if min_val is not None and val < min_val:
                    print(f"    Vui lòng nhập số >= {min_val}")
                    continue
                if max_val is not None and val > max_val:
                    print(f"    Vui lòng nhập số <= {max_val}")
                    continue
                return val
            except ValueError:
                print("    Vui lòng nhập số nguyên.")

    def display_schedule_list(self, schedules, fixed_events=None):
        # Sắp xếp theo điểm giảm dần
        ranked = sorted(schedules, key=lambda s: s.score, reverse=True)

        print("\n" + "=" * 55)
        print("  TÌM ĐƯỢC CÁC LỊCH HỢP LỆ:")
        print("=" * 55)
        for i, s in enumerate(ranked):
            print(f"  {i+1}. Lịch #{i+1} — Điểm: {s.score:.1f}/100")
        print("=" * 55)

        while True:
            raw = input("\n  Chọn số để xem chi tiết (Enter để thoát): ").strip()
            if not raw:
                break
            try:
                idx = int(raw)
                if 1 <= idx <= len(ranked):
                    self.display_schedule(ranked[idx - 1], fixed_events)
                else:
                    print(f"  Vui lòng nhập số từ 1 đến {len(ranked)}")
            except ValueError:
                print("  Vui lòng nhập số nguyên.")
            