# Weather MCP Server — FastMCP Implementation

MCP Server cung cấp dữ liệu thời tiết thời gian thực và dự báo nhiều ngày cho các trợ lý AI (Claude Code, Claude Desktop, Cursor, Google ADK Agent,...).

---

## 1. Mô tả bài toán & Công việc thực tế giải quyết

- **Vấn đề thực tế**: Các mô hình ngôn ngữ lớn (LLM) không có quyền truy cập Internet trực tiếp và không biết dữ liệu thời tiết theo thời gian thực hoặc dự báo tương lai. Khi người dùng hỏi *"Thời tiết Hà Nội hôm nay thế nào?"* hoặc *"Có nên tổ chức sự kiện ngoài trời ở Tokyo vào ngày mai không?"*, LLM không thể trả lời chính xác nếu không có công cụ bên ngoài.
- **Giải pháp của MCP Server**:
  - Tích hợp chuẩn **Model Context Protocol (MCP)** qua **FastMCP**.
  - Đóng gói logic gọi API thời tiết chuyên nghiệp ([WeatherAPI.com](https://www.weatherapi.com/)) thành các MCP Tools có schema rõ ràng.
  - Tự động fallback sang dữ liệu mô phỏng (Mock Data) khi mất kết nối hoặc chạy offline, đảm bảo hệ thống không bao giờ bị sập.
  - Hỗ trợ cả 2 phương thức truyền thông: **Streamable HTTP** (cho ứng dụng qua mạng/Web) và **stdio** (cho Claude Code, CLI, Claude Desktop).

---

## 2. Danh sách MCP Tools & Chi tiết Input / Output

Server cung cấp **3 công cụ chính**:

### 🛠️ 1. `get_current_weather`
- **Mục đích**: Lấy thông tin điều kiện thời tiết hiện tại của một thành phố.
- **Input parameters**:
  - `city` (*string*, bắt buộc): Tên thành phố cần tra cứu (ví dụ: `"Hanoi"`, `"Danang"`, `"Tokyo"`, `"Brisbane"`).
- **Output format**: Chuỗi văn bản có cấu trúc bao gồm:
  - Tên thành phố, khu vực, quốc gia
  - Nhiệt độ hiện tại (°C và °F)
  - Nhiệt độ cảm nhận (Feels like)
  - Tình trạng thời tiết (Condition text)
  - Độ ẩm (%), Tốc độ và hướng gió (km/h, mph)
  - Áp suất khí quyển (mb), Chỉ số UV, Tầm nhìn xa (km)
  - Thời điểm cập nhật dữ liệu.

### 🛠️ 2. `get_forecast`
- **Mục đích**: Lấy dự báo thời tiết chi tiết từ 1 đến 3 ngày tới cho một thành phố.
- **Input parameters**:
  - `city` (*string*, bắt buộc): Tên thành phố cần dự báo.
  - `days` (*integer*, tùy chọn, mặc định: `3`, tối đa: `3` đối với gói Free): Số ngày muốn xem dự báo (1-3).
- **Output format**: Danh sách chi tiết từng ngày bao gồm:
  - Ngày dự báo (`YYYY-MM-DD`)
  - Nhiệt độ cao nhất / thấp nhất (High / Low)
  - Tình trạng thời tiết dự kiến
  - Xác suất mưa (`daily_chance_of_rain %`)
  - Tốc độ gió cực đại và chỉ số UV.

### 🛠️ 3. `health_check`
- **Mục đích**: Kiểm tra tình trạng hoạt động và tính sẵn sàng của MCP Server.
- **Input parameters**: Không có (`None`).
- **Output format**: Thông điệp xác nhận trạng thái hoạt động: `"✅ Weather MCP Server is running!..."`.

---

## 3. Hướng dẫn Cài đặt và Chạy Server

### Yêu cầu tiên quyết:
- Python >= 3.10
- Trình quản lý gói `uv` (hoặc `pip`)

### Các bước cài đặt:

```bash
# 1. Di chuyển vào thư mục mcp-server
cd 04-lab/mcp-server

# 2. Cài đặt các thư viện cần thiết
uv sync
# Hoặc dùng pip: pip install -r requirements.txt (nếu dùng venv thông thường)

# 3. Tạo file cấu hình .env (tùy chọn nếu muốn dùng live API key)
# Sao chép từ .env.example:
cp .env.example .env
```

Nội dung file `.env`:
```env
WEATHERAPI_KEY=your_weatherapi_key_here
PORT=8085
```

### Các chế độ chạy Server:

#### A. Chế độ Streamable HTTP (Mặc định - Cổng 8085):
Phục vụ cho Google ADK Client hoặc các kết nối từ xa:
```powershell
uv run python weather.py
```
> Server sẽ lắng nghe tại: `http://localhost:8085/mcp`

#### B. Chế độ `stdio` (Dành cho CLI / Claude Code):
```powershell
uv run python weather.py --stdio
```

---

## 4. Hướng dẫn Đăng ký MCP Server với Claude Code

Bạn có thể kết nối MCP Server này trực tiếp vào **Claude Code** để Claude tự động tra cứu thời tiết khi bạn chat trong terminal.

### Cách 1: Đăng ký qua lệnh `claude mcp add` (Khuyên dùng)

#### Chạy qua `stdio` (Không cần bật server trước, Claude Code sẽ tự khởi chạy):
```bash
claude mcp add weather -- uv --directory /đường_dẫn_tuyệt_đối_tới/04-lab/mcp-server run python weather.py --stdio
```
*Ví dụ trên Windows PowerShell:*
```powershell
claude mcp add weather -- uv --directory "d:/VinAI/Lab/Phase 2/Lab 26/Day26-MCP-Tools-Integration/04-lab/mcp-server" run python weather.py --stdio
```

#### Chạy qua HTTP SSE (Khi server đang chạy ngầm ở port 8085):
```bash
claude mcp add weather-http http://localhost:8085/mcp
```

---

### Cách 2: Đăng ký qua file cấu hình `.mcp.json` hoặc Claude Desktop

Thêm cấu hình sau vào file cấu hình Claude Desktop (`claude_desktop_config.json`) hoặc `.mcp.json`:

```json
{
  "mcpServers": {
    "weather": {
      "command": "uv",
      "args": [
        "--directory",
        "d:/VinAI/Lab/Phase 2/Lab 26/Day26-MCP-Tools-Integration/04-lab/mcp-server",
        "run",
        "python",
        "weather.py",
        "--stdio"
      ],
      "env": {
        "WEATHERAPI_KEY": "0ed5ac073a5149699be103008262808"
      }
    }
  }
}
```

---

## 5. Bằng chứng & Hướng dẫn Kiểm tra Hoạt động của Tools

### Cách 1: Kiểm tra tự động qua script `verify_setup.py`
```powershell
cd ../mcp-client
uv run python verify_setup.py
```
**Kết quả kiểm tra:**
```text
🔍 Checking environment configuration...
✅ GOOGLE_API_KEY configured
🔍 Checking dependencies...
✅ Google ADK
✅ MCP
✅ FastMCP
🔍 Checking MCP server connectivity...
✅ MCP server reachable at http://localhost:8085/mcp (HTTP 400)
🔍 Checking agent import...
✅ Agent imported successfully: weather_agent
============================================================
✅ All checks passed!
```

### Cách 2: Log thực tế khi gọi tool từ Agent / API

#### Bằng chứng 1 — Gọi tool `get_current_weather(city='Hanoi')`:
```text
[FastMCP Server Log]
Processing request of type CallToolRequest: get_current_weather
HTTP Request: GET https://api.weatherapi.com/v1/current.json?q=Hanoi "HTTP/1.1 200 OK"

[Agent Output]:
Thời tiết hiện tại ở Hà Nội:
- Nhiệt độ: 33.1°C (Cảm giác như 41.1°C)
- Tình trạng: Có mưa rải rác ở một số khu vực lân cận
- Độ ẩm: 66%
- Tốc độ gió: 11.9 km/h (Hướng Đông Nam)
- Tầm nhìn xa: 10 km
- Chỉ số UV: 0.6
```

#### Bằng chứng 2 — Gọi tool `get_forecast(city='Tokyo', days=3)`:
```text
[FastMCP Server Log]
Processing request of type CallToolRequest: get_forecast
HTTP Request: GET https://api.weatherapi.com/v1/forecast.json?q=Tokyo&days=3 "HTTP/1.1 200 OK"

[Agent Output]:
Dự báo thời tiết 3 ngày tới tại Tokyo, Nhật Bản:
- Ngày 28/08/2026: 24.9°C – 31.9°C | Nhiều mây / Âm u | Khả năng mưa: 66% | Gió: 15.1 km/h | UV: 8.1
- Ngày 29/08/2026: 23.0°C – 27.3°C | Mưa rải rác vài nơi | Khả năng mưa: 55% | Gió: 18.4 km/h | UV: 6.0
- Ngày 30/08/2026: 23.2°C – 29.5°C | Nhiều mây / Âm u   | Khả năng mưa: 27% | Gió: 18.0 km/h | UV: 7.0
```
