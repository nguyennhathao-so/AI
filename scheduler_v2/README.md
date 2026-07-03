# Hệ thống Xếp Thời Khóa Biểu Tự Động
## Đề tài 3 — CSP Scheduling (Môn Trí Tuệ Nhân Tạo)

---

## Cấu trúc thư mục & Phân công

```
scheduler/
│
├── main.py              # Điểm khởi động — gọi các service theo thứ tự
├── demo.py              # Chạy thử không cần nhập tay (dùng để test)
│
├── data/                ══ NGƯỜI 2: Data Model & Storage ══
│   ├── models.py        # Định nghĩa TimeSlot, Course, CSPProblem, Schedule...
│   └── data_service.py  # Chuẩn hóa UserInput → CSPProblem, tính domain
│
├── engine/              ══ NGƯỜI 3: Constraint Engine ══
│   └── constraint_engine.py  # Ràng buộc cứng/mềm + thuật toán AC-3
│
├── solver/              ══ NGƯỜI 4: Search Algorithm ══
│   └── backtrack_solver.py   # Backtracking + MRV + LCV + Forward Checking
│
├── optimizer/           ══ NGƯỜI 5: Optimization & Export ══
│   └── optimizer.py          # Scoring function, chọn lịch tốt nhất
│
└── ui/                  ══ NGƯỜI 1: UI/UX ══
    └── cli_ui.py             # Thu thập input, hiển thị kết quả, xử lý lỗi
```

---

## Phân công chi tiết — Phần AI của mỗi người

### Người 1 — UI/UX (`ui/`)
- Xây dựng giao diện nhập liệu (CLI hoặc nâng cấp lên GUI/web)
- Validate input: phát hiện conflict ngay khi nhập (ví dụ: số giờ yêu cầu > slot rảnh)
- Đọc output từ Solver: nếu CSP fail, hiển thị **lý do cụ thể** (slot nào bị chiếm, môn nào không có domain)
- **Phần AI**: Parse và visualize kết quả của CSP solver

### Người 2 — Data Model & Storage (`data/`)
- Định nghĩa các class dữ liệu: `TimeSlot`, `Course`, `FixedEvent`, `CSPProblem`, `Schedule`
- Viết `DataService.normalize()`: chuyển input thô thành bài toán CSP chuẩn
- **Phần AI**: Tính domain cho từng biến CSP — đây là bước **mô hình hóa bài toán**
- Có thể thêm: lưu/load lịch ra file JSON hoặc SQLite

### Người 3 — Constraint Engine (`engine/`)
- Viết các hàm ràng buộc cứng: `_no_slot_overlap`, `_not_in_fixed_slot`
- Viết các hàm ràng buộc mềm: penalty liên tiếp, penalty vượt giờ, penalty dồn ngày
- **Phần AI CHÍNH**: Cài đặt thuật toán **AC-3** (Arc Consistency Algorithm)
  - Thu hẹp domain trước khi solver chạy
  - Giảm không gian tìm kiếm đáng kể

### Người 4 — Search Algorithm (`solver/`)
- Cài đặt **Backtracking Search** đệ quy
- **Phần AI CHÍNH**: Các heuristic tối ưu hóa tìm kiếm:
  - **MRV** (Minimum Remaining Values): chọn biến có domain nhỏ nhất trước
  - **LCV** (Least Constraining Value): chọn giá trị ít ảnh hưởng nhất
  - **Forward Checking**: kiểm tra domain tương lai sau mỗi lần gán
- Đây là phần thầy sẽ hỏi nhiều nhất trong buổi báo cáo

### Người 5 — Optimizer & Export (`optimizer/`)
- Viết **scoring function** (objective function): tính điểm chất lượng cho lịch
  - Thưởng: phân bổ đều các ngày, ưu tiên buổi sáng
  - Phạt: học liên tiếp, dồn ngày, vượt giờ/ngày
- **Phần AI**: Greedy selection hoặc có thể nâng cấp lên Local Search
- Thêm tính năng: xuất lịch ra file `.ics` (Google Calendar), `.csv`, `.pdf`

---

## Cách chạy

```bash
# Cài Python 3.8+, không cần thư viện ngoài

# Chạy demo với dữ liệu mẫu (khuyên dùng để test trước)
python demo.py

# Chạy ứng dụng thật (nhập dữ liệu bằng tay)
python main.py
```

---

## Luồng hoạt động

```
UserInput (UI thu thập)
    ↓
DataService.normalize()       → CSPProblem (variables, domains, constraints)
    ↓
ConstraintEngine.build()      → AC-3 thu hẹp domain
    ↓
BacktrackSolver.solve()       → List[Schedule] hợp lệ (backtracking + MRV/LCV)
    ↓
Optimizer.select_best()       → Schedule tốt nhất (scoring function)
    ↓
CLIUI.display_schedule()      → In ra terminal
```

---

## Thuật toán AI sử dụng

| Thuật toán | File | Mô tả |
|---|---|---|
| CSP Modeling | `data/data_service.py` | Mô hình hóa bài toán thành biến + domain |
| AC-3 | `engine/constraint_engine.py` | Arc Consistency, thu hẹp domain |
| Backtracking | `solver/backtrack_solver.py` | Tìm kiếm đệ quy có quay lui |
| MRV Heuristic | `solver/backtrack_solver.py` | Chọn biến ràng buộc nhất trước |
| LCV Heuristic | `solver/backtrack_solver.py` | Chọn giá trị ít xung đột nhất |
| Forward Checking | `solver/backtrack_solver.py` | Cắt nhánh sớm khi domain rỗng |
| Scoring / Greedy | `optimizer/optimizer.py` | Đánh giá và chọn lịch tốt nhất |

---

## Gợi ý nâng cấp để có điểm cao hơn

- **Người 1**: Thêm giao diện web bằng Flask hoặc Streamlit
- **Người 2**: Lưu lịch vào SQLite, cho phép load lại lịch cũ
- **Người 3**: Thêm ràng buộc học nhóm (nhiều người phải cùng rảnh)
- **Người 4**: Thêm giới hạn thời gian cho solver (timeout nếu tìm quá lâu)
- **Người 5**: Xuất ra file `.ics` để import vào Google Calendar
