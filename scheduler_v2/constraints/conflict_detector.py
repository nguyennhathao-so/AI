# ============================================================
# conflict_detector.py
#
# NHIỆM VỤ:
# Phát hiện conflict trước khi chạy CSP solver.
#
# MỤC TIÊU:
# - Giảm search space
# - Tránh backtracking vô ích
# - Giải thích vì sao không có nghiệm
#
# ĐÂY LÀ:
# Constraint preprocessing / pruning layer
#
# THUỘC:
# constraints/
# ============================================================


# ============================================================
# Kiểm tra tổng số giờ học có vượt quá slot rảnh không
# ============================================================

def check_total_hours(courses, available_slots):
    """
    Tổng số giờ yêu cầu của các môn
    không được lớn hơn số slot còn trống.

    Ví dụ:
        Cần học 20h
        Nhưng chỉ có 10 slot
        => impossible
    """

    # Tổng số giờ cần học
    required_hours = sum(course.hours_per_week for course in courses)

    # Tổng slot còn trống
    available_count = len(available_slots)

    # Conflict
    if required_hours > available_count:
        return (
            False,
            f"Tổng giờ học yêu cầu ({required_hours}) "
            f"lớn hơn số slot rảnh ({available_count})"
        )

    return (True, None)


# ============================================================
# Kiểm tra giới hạn giờ học tối đa mỗi ngày
# ============================================================

def check_daily_limit(courses, max_hours_per_day):
    """
    Kiểm tra:
    giới hạn học mỗi ngày có khả thi không.

    Ví dụ:
        max = 2h/ngày
        => tối đa tuần = 14h

        Nhưng cần học 20h
        => impossible
    """

    total_required = sum(course.hours_per_week for course in courses)

    max_weekly_capacity = max_hours_per_day * 7

    if total_required > max_weekly_capacity:
        return (
            False,
            f"Tổng giờ học ({total_required}) "
            f"vượt quá giới hạn tuần "
            f"({max_weekly_capacity} giờ)"
        )

    return (True, None)


# ============================================================
# Kiểm tra preferred days có hợp lệ không
# ============================================================

def check_preferred_days(courses, available_slots):
    """
    Kiểm tra:
    môn học có preferred_days
    nhưng không tồn tại slot phù hợp.

    Ví dụ:
        AI chỉ học Mon
        Nhưng Mon full
        => impossible
    """

    errors = []

    for course in courses:

        # Không có preferred day
        if not course.preferred_days:
            continue

        found = False

        # Tìm slot phù hợp
        for slot in available_slots:

            if slot.day in course.preferred_days:
                found = True
                break

        if not found:

            pref = ", ".join(course.preferred_days)

            errors.append(
                f"Môn '{course.name}' "
                f"không còn slot phù hợp "
                f"với preferred days: {pref}"
            )

    return errors


# ============================================================
# Kiểm tra duplicate slot
# ============================================================

def check_duplicate_fixed_events(fixed_events):
    """
    Kiểm tra:
    có lịch cố định nào bị trùng không.

    Ví dụ:
        Work -> Mon 8h
        School -> Mon 8h

    => conflict input
    """

    seen = set()
    errors = []

    for event in fixed_events:

        key = (event.slot.day, event.slot.time)

        if key in seen:
            errors.append(
                f"Conflict lịch cố định tại "
                f"{event.slot.day} {event.slot.time}"
            )

        seen.add(key)

    return errors


# ============================================================
# Hàm chính chạy toàn bộ conflict detection
# ============================================================

def detect_conflicts(user_input, available_slots):
    """
    Chạy toàn bộ bước conflict detection.

    INPUT:
        user_input
        available_slots

    OUTPUT:
        list lỗi conflict
    """

    errors = []

    # --------------------------------------------------------
    # 1. Tổng giờ học
    # --------------------------------------------------------

    ok, msg = check_total_hours(
        user_input.courses,
        available_slots
    )

    if not ok:
        errors.append(msg)

    # --------------------------------------------------------
    # 2. Giới hạn giờ/ngày
    # --------------------------------------------------------

    ok, msg = check_daily_limit(
        user_input.courses,
        user_input.max_hours_per_day
    )

    if not ok:
        errors.append(msg)

    # --------------------------------------------------------
    # 3. Preferred days
    # --------------------------------------------------------

    preferred_errors = check_preferred_days(
        user_input.courses,
        available_slots
    )

    errors.extend(preferred_errors)

    # --------------------------------------------------------
    # 4. Duplicate fixed events
    # --------------------------------------------------------

    duplicate_errors = check_duplicate_fixed_events(
        user_input.fixed_events
    )

    errors.extend(duplicate_errors)

    return errors