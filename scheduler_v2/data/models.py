# ============================================================
# data/models.py — Định nghĩa các lớp dữ liệu dùng chung
#
# NHIỆM VỤ: Mô hình hóa thực thể trong bài toán lịch học.
# Tất cả module khác đều import từ file này.
# ============================================================

from dataclasses import dataclass, field
from typing import List, Optional


# ---- Các hằng số ngày trong tuần ----
DAYS = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7"]

# Các slot thời gian trong ngày (mỗi slot = 1 tiếng, mở rộng thêm buổi tối)
TIME_SLOTS = [
    "07:00", "08:00", "09:00", "10:00", "11:00",
    "13:00", "14:00", "15:00", "16:00", "17:00",
    "18:00", "19:00", "20:00", "21:00"
]


@dataclass
class TimeSlot:
    """
    Đại diện cho một ô thời gian cụ thể trong tuần.
    Ví dụ: Thứ 2, 08:00
    """
    day: str        # "Thứ 2" đến "Thứ 7"
    time: str       # "07:00" đến "21:00"

    def __repr__(self):
        return f"{self.day} {self.time}"

    def __eq__(self, other):
        return self.day == other.day and self.time == other.time

    def __hash__(self):
        return hash((self.day, self.time))


@dataclass
class Course:
    """
    Một môn học muốn tự học.
    """
    name: str                   # Tên môn, ví dụ: "Giải tích", "Lập trình"
    hours_per_week: int         # Số tiếng cần học mỗi tuần
    preferred_days: List[str] = field(default_factory=list)   # Ưu tiên học ngày nào
    max_hours_per_day: int = 2  # Số tiếng tối đa học môn này trong 1 ngày
    schedule_mode: str = "discrete" # "discrete" | "consecutive_daily" | "consecutive_weekly"
    preferred_times: List[str] = field(default_factory=list)   # Khung giờ ưu tiên trong ngày



@dataclass
class FixedEvent:
    """
    Sự kiện cố định không thể thay đổi.
    Ví dụ: lịch học trên trường, ca đi làm thêm.
    Đây là RÀNG BUỘC CỨNG trong CSP.
    """
    name: str           # Tên sự kiện
    slot: TimeSlot      # Slot thời gian bị chiếm


@dataclass
class UserInput:
    """
    Dữ liệu thô thu thập từ người dùng qua UI.
    DataService sẽ chuyển đổi object này thành CSPProblem.
    """
    courses: List[Course] = field(default_factory=list)
    fixed_events: List[FixedEvent] = field(default_factory=list)
    blocked_slots: List[TimeSlot] = field(default_factory=list)
    max_hours_per_day: int = 4   # Không muốn học quá N tiếng/ngày


@dataclass
class Assignment:
    """
    Một lần phân công: môn X học vào slot Y.
    Kết quả của solver là danh sách Assignment.
    """
    course: Course
    slot: TimeSlot
    var_name: str = ""   # e.g., "Giải tích_h0"


@dataclass
class Schedule:
    """
    Một lịch hoàn chỉnh trong tuần — tập hợp các Assignment.
    Optimizer sẽ so sánh nhiều Schedule và chọn cái tốt nhất.
    """
    assignments: List[Assignment] = field(default_factory=list)
    fixed_events: List[FixedEvent] = field(default_factory=list)
    score: float = 0.0   # Điểm chất lượng, do Optimizer tính

    def get_slots_used(self) -> List[TimeSlot]:
        return [a.slot for a in self.assignments]

    def __repr__(self):
        lines = [f"  {a.course.name:20s} → {a.slot}" for a in self.assignments]
        return "\n".join(lines)


@dataclass
class CSPProblem:
    """
    Bài toán CSP đã được mô hình hóa đầy đủ.
    - variables: danh sách các biến theo giờ cần xếp (e.g. ["Giải tích_h0", "Giải tích_h1", ...])
    - domains: mỗi môn có thể học ở slot nào
    - fixed_slots: slot đã bị chiếm (ràng buộc cứng)
    - max_hours_per_day: ràng buộc mềm về tải
    - courses: danh sách các Course gốc để tra cứu thông tin
    """
    variables: List[str] = field(default_factory=list)
    domains: dict = field(default_factory=dict)       # {var_name: [TimeSlot]}
    fixed_slots: List[TimeSlot] = field(default_factory=list)
    fixed_events: List[FixedEvent] = field(default_factory=list)
    max_hours_per_day: int = 4
    courses: List[Course] = field(default_factory=list)
    _courses_dict: dict = field(default_factory=dict, init=False, repr=False)
    
    def __post_init__(self):
        self._courses_dict = {c.name: c for c in self.courses}

    @property
    def courses_dict(self):
        return self._courses_dict


