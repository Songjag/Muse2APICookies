# Muse2APICookies

Chạy [muse2api](https://github.com/www222fff/muse2api) bằng cookie tài khoản muse.ai, với menu chọn phiên ngay trong terminal. Bạn có thể lưu nhiều phiên và chọn lại mỗi lần khởi động.

Dự án này bổ sung phần nhập, lưu và chọn cookie. Mã server và API được phát triển từ **muse2api của [www222fff](https://github.com/www222fff)**.

## Cài đặt

Cần **Python 3.10+**, **[uv](https://docs.astral.sh/uv/)** và **Chrome hoặc Chromium**.

```bash
git clone https://github.com/Songjag/Muse2APICookies.git
cd Muse2APICookies
uv sync --locked
uv run python main.py
```

## Nhập cookie

1. Đăng nhập muse.ai trên trình duyệt.
2. Mở DevTools → **Network**, tải lại trang rồi chọn một request gửi tới muse.ai.
3. Trong **Request Headers**, sao chép giá trị của header `Cookie`.
4. Chạy `main.py`, nhập `0` hoặc nhấn Enter để tạo phiên mới, rồi dán cookie.

Cookie cần có `hatch_sess` và `hatch_native_auth_device`. Khi dán vào terminal, nội dung sẽ không hiện ra; nhấn Enter để xác nhận.

Các phiên được lưu lần lượt trong `data/session_coookie_1.json`, `data/session_coookie_2.json`, … Lần sau chỉ cần chạy lại và nhập số phiên muốn dùng. Nhấn **Ctrl+C** để dừng server.

## Sử dụng

Sau khi chọn phiên, server mặc định chạy tại **http://127.0.0.1:18610**.

| Mục | Địa chỉ |
| --- | --- |
| Dashboard | http://127.0.0.1:18610/dashboard |
| API base URL | `http://127.0.0.1:18610/v1` |
| Swagger UI | http://127.0.0.1:18610/docs |

API key mặc định được tạo trong `data/api_key`. Dùng key này khi kết nối ứng dụng chat; cookie muse.ai dùng để đăng nhập tài khoản phía server.

Ví dụ gửi tin nhắn:

```bash
curl http://127.0.0.1:18610/v1/chat/completions \
  -H "Authorization: Bearer $(cat data/api_key)" \
  -H "Content-Type: application/json" \
  -d '{"model":"muse-chat","messages":[{"role":"user","content":"Xin chào!"}]}'
```

Xem [tài liệu API](docs/API.md) để sử dụng chat streaming, tạo ảnh, video và quản lý tài khoản.

## Cấu hình

Muốn đổi cổng, API key hoặc đường dẫn Chrome, sao chép file cấu hình mẫu:

```bash
cp .env.example .env
```

Chỉnh các giá trị trong `.env` rồi khởi động lại server. Nếu dùng cấu hình mặc định thì không cần tạo file này.

Cookie được lưu trong `data/`. Không chia sẻ thư mục này hoặc file `.env` chứa thông tin đăng nhập.

## Docker

Image Docker đã kèm Chromium:

```bash
docker compose build
docker compose run --rm --service-ports muse2api
```

Chọn hoặc tạo phiên trong terminal như khi chạy trực tiếp. Dữ liệu được lưu ở thư mục `data/` trên máy chủ. Nếu gặp lỗi quyền ghi trên Linux, kiểm tra quyền của thư mục này với UID `1000` trong container.

## Phát triển

`main.py` là điểm khởi động. Mã server nằm trong `muse2api/src/muse2api/`.

Chạy kiểm thử từ thư mục gốc:

```bash
uv sync --locked --extra dev
uv run --extra dev python -m pytest
```

## Credits

- **[www222fff/muse2api](https://github.com/www222fff/muse2api)** — dự án gốc, cung cấp server, các driver và API tương thích OpenAI.
- **[Songjag](https://github.com/Songjag)** — bổ sung launcher và quản lý phiên cookie cho Muse2APICookies.

Mã nguồn sử dụng giấy phép [MIT](LICENSE). Giữ nguyên thông tin bản quyền của tác giả muse2api trong dự án.
