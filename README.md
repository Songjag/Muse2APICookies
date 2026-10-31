# Muse2APICookies

Chạy mọi lệnh bên dưới tại thư mục gốc `Muse2APICookies`, không cần vào `muse2api/`.
Cần Python 3.10+, uv và Chrome/Chromium khi chạy trực tiếp.

## Chạy server

```bash
uv sync --locked
uv run python main.py
```

Chọn số phiên đã lưu, hoặc nhập `0` / Enter để nhập cookie mới (nội dung nhập được ẩn).
Cookie header phải có `hatch_sess` và `hatch_native_auth_device`.
Mỗi phiên lưu ở `data/session_coookie_1.json`, `data/session_coookie_2.json`, ...
Server dùng phiên được chọn và lưu cookie gia hạn vào đúng file đó.
Ctrl+C để dừng, chạy lại để chọn phiên khác.

- Server: http://127.0.0.1:18610
- Dashboard: http://127.0.0.1:18610/dashboard
- API key mặc định: `data/api_key` (khác với cookie muse.ai).

Để tùy chỉnh cổng, đường dẫn Chrome hoặc các tùy chọn khác, sao chép `.env.example`
thành `.env` rồi chỉnh sửa. Không cần tạo `.env` để chạy với cấu hình mặc định.

## Docker

Docker đã kèm Chromium. Chạy tương tác để chọn hoặc tạo phiên:

```bash
docker compose build
docker compose run --rm --service-ports muse2api
```

`data/` được giữ trên máy chủ qua volume. Nếu dùng Linux và volume mới không ghi được,
hãy cấp quyền ghi thư mục `data/` cho UID 1000 của container.

## Tài liệu API

Các ví dụ bên dưới chạy khi server đang hoạt động. Đặt key trong terminal của bạn (thay các giá trị mẫu):

```bash
export MUSE_API_KEY='THAY_BANG_API_KEY'
export MUSE_ADMIN_KEY='THAY_BANG_ADMIN_KEY'
```

Ví dụ chat hoàn chỉnh:

```bash
curl -N http://127.0.0.1:18610/v1/chat/completions \
  -H "Authorization: Bearer $MUSE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"muse-chat","messages":[{"role":"user","content":"Xin chào!"}],"stream":true}'
```

### Quy ước và xác thực

Các đường dẫn dưới đây tính từ `http://127.0.0.1:18610`, không tự thêm `/v1` trước `/admin` hoặc `/healthz`. Body dùng JSON và `Content-Type: application/json`, riêng chỉnh sửa ảnh dùng multipart.

| Nhóm | Xác thực |
| --- | --- |
| Chat, Responses, models, ảnh, video | API key chính, key được tạo qua dashboard hoặc admin key |
| `/admin/*` | Chỉ admin key; nếu không đặt `MUSE2API_ADMIN_KEY` thì dùng API key chính |
| `/healthz`, `/readyz`, `/dashboard`, `/v1/media/{name}` | Không yêu cầu key |

Gửi `Authorization: Bearer <KEY>`. Server cũng nhận `X-API-Key: <KEY>` khi không có Bearer header. Key được tạo qua `/admin/keys` không có quyền quản trị.

Có thể xem schema trực tiếp khi server chạy: [Swagger UI](http://127.0.0.1:18610/docs), [ReDoc](http://127.0.0.1:18610/redoc), [OpenAPI JSON](http://127.0.0.1:18610/openapi.json). Route multipart `/v1/images/edits` tự đọc form nên schema tự sinh không liệt kê đầy đủ các trường upload.

Trong ví dụ quản trị, đặt `MUSE_ADMIN_KEY` thành admin key của bạn. Các ID như `task_xxx`, `acc_xxx`, `key_xxx` là giá trị minh họa, cần thay bằng ID trả về thực tế.

### Kiểm tra server và danh sách model

| Endpoint | Phản hồi và ý nghĩa |
| --- | --- |
| `GET /healthz` | `{"ok":true,"version":"..."}` — ứng dụng đang phản hồi |
| `GET /readyz` | `{"ready":true,"driver":{...},"accounts":{...}}` — trạng thái driver và pool |
| `GET /v1/models` | `{"object":"list","data":[...]}` — model gốc và alias |
| `GET /dashboard` | Trang HTML quản trị; các thao tác trên trang gọi Admin API có xác thực |

`/readyz` vẫn trả HTTP 200 khi `ready` là `false`; trình giám sát cần đọc body. Với driver yêu cầu tài khoản, trạng thái sẵn sàng cần driver khỏe và ít nhất một tài khoản khả dụng.

Ba model gốc là `muse-chat`, `muse-image`, `muse-video`. Mỗi phần tử model có `id`, `object`, `created`, `owned_by`, `kind`; alias có thêm `alias_of`. Alias như `gpt-4o` trỏ về `muse-chat`, không xác nhận model thực trên muse.ai. Bỏ trống hoặc gửi tên không được nhận diện sẽ dùng model mặc định của loại yêu cầu; gửi model đã biết nhưng sai loại sẽ bị lỗi 400.

### `POST /v1/chat/completions` — chat

| Trường | Bắt buộc / mặc định | Cách dùng |
| --- | --- | --- |
| `messages` | Bắt buộc, ít nhất 1 phần tử | Mỗi phần tử có `role` và `content`; nội dung là chuỗi hoặc danh sách phần văn bản/ảnh |
| `model` | `muse-chat` | Tên model hoặc alias chat |
| `stream` | `false` | `true` để nhận SSE |
| `user` | Không bắt buộc | ID hội thoại ổn định để driver browser tiếp tục thread; được phân biệt theo API key |
| `stream_options` | Không bắt buộc | `{"include_usage":true}` để thêm chunk usage vào stream |
| `temperature`, `top_p`, `max_tokens`, `tools`, `tool_choice` | Không bắt buộc | Được nhận để tương thích client nhưng không điều khiển sampling, giới hạn token hay gọi tool |

Ảnh trong `content` dùng cấu trúc như sau:

```json
{"role":"user","content":[{"type":"text","text":"Mô tả ảnh này"},{"type":"image_url","image_url":{"url":"data:image/png;base64,..."}}]}
```

Khi `stream:false`, kết quả có `id`, `object:"chat.completion"`, `created`, `model`, `choices` và `usage`. Đọc câu trả lời tại `choices[0].message.content`; `finish_reason` là `stop`. Số token trong `usage` là **ước lượng từ độ dài văn bản**, không phải số đo do upstream trả về.

Khi `stream:true`, phản hồi có kiểu `text/event-stream`, mỗi bản tin là `data: {...}`. Ghép nội dung tại `choices[0].delta.content`; stream kết thúc bằng `data: [DONE]`. Nếu bật heartbeat, có thể xuất hiện dòng chú thích SSE `: keepalive`.

Không truyền `user` thì mỗi request mở một thread mới và gửi lịch sử `messages`. Dùng một `user` riêng cho từng cuộc hội thoại khi cần tái sử dụng thread.

### `POST /v1/responses` — giao diện Responses

| Trường | Bắt buộc / mặc định | Cách dùng |
| --- | --- | --- |
| `input` | Cần có nội dung hợp lệ | Chuỗi văn bản hoặc danh sách message có `role`, `content`; hỗ trợ nội dung văn bản/ảnh |
| `instructions` | Không bắt buộc | Chỉ dẫn hệ thống |
| `model` | `muse-chat` | Model/alias chat |
| `stream` | `false` | Bật SSE |
| `user` | Không bắt buộc | Khóa hội thoại tương tự Chat Completions |
| `max_output_tokens` | Không bắt buộc | Được nhận nhưng chưa dùng để giới hạn đầu ra |

Phản hồi thường có `object:"response"`, `status`, `output`, `usage`. Văn bản nằm tại `output[0].content[0].text`. Streaming phát các sự kiện như `response.created`, `response.in_progress`, `response.output_text.delta`, `response.completed`; đọc loại sự kiện qua trường `type` trong JSON.

Endpoint này dùng chung gateway chat. Các input item như `function_call`, `function_call_output`, `reasoning`, `computer_call`, `file_search_call`, `web_search_call` bị từ chối với lỗi 400. Đây không phải triển khai đầy đủ mọi chức năng Responses; mã hiện tại không dùng `previous_response_id` để nối hội thoại.

### `POST /v1/images/generations` — tạo ảnh

| Trường | Bắt buộc / mặc định | Cách dùng |
| --- | --- | --- |
| `prompt` | Bắt buộc, chuỗi không rỗng | Mô tả ảnh cần tạo |
| `model` | `muse-image` | Model/alias ảnh |
| `n` | `1`, từ 1 đến 4 | Số ảnh yêu cầu |
| `size` | Không bắt buộc | Chuỗi kích thước/tỉ lệ, ví dụ `16:9`; kết quả phụ thuộc driver/upstream |
| `response_format` | `url` | `url` hoặc `b64_json` |
| `image` | Không bắt buộc | Một chuỗi hoặc danh sách tối đa 4 ảnh tham chiếu; nhận data URL, URL HTTP(S), base64 |
| `background` | Không bắt buộc | `auto`, `opaque`, `transparent`; `transparent` tách nền cục bộ, cần dependency `matting` |
| `async` | `false` | `true` trả tác vụ ngay để truy vấn sau |
| `user` | Không bắt buộc | Schema nhận trường này nhưng luồng tạo ảnh hiện chưa sử dụng |

Phản hồi đồng bộ minh họa:

```json
{"created":1730000000,"data":[{"url":"http://127.0.0.1:18610/v1/media/img_example.png","revised_prompt":null}]}
```

Với `response_format:"b64_json"`, mỗi phần tử dùng `b64_json` thay cho `url`. Với `async:true`, server luôn lưu kết quả bằng **URL**, kể cả khi yêu cầu `b64_json`.

```bash
curl http://127.0.0.1:18610/v1/images/generations \
  -H "Authorization: Bearer $MUSE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Một khu vườn mùa xuân","async":true}'

curl http://127.0.0.1:18610/v1/images/generations/task_xxx \
  -H "Authorization: Bearer $MUSE_API_KEY"
```

URL ảnh đầu vào được tải phía server; URL tới địa chỉ nội bộ hoặc loopback bị chặn. Dùng data URL hoặc upload multipart cho ảnh cục bộ.

### `POST /v1/images/edits` — tạo ảnh từ ảnh tham chiếu

Gửi **multipart/form-data**, không gửi JSON. Cần `prompt` và ít nhất một tệp trong trường `image` hoặc `image[]`, tối đa 4 ảnh tổng cộng. Các trường văn bản `model`, `n`, `size`, `response_format`, `background`, `async` dùng như endpoint tạo ảnh.

```bash
curl http://127.0.0.1:18610/v1/images/edits \
  -H "Authorization: Bearer $MUSE_API_KEY" \
  -F 'image[]=@reference.png' \
  -F 'prompt=Giữ nhân vật trong ảnh, đổi sang bối cảnh mùa đông' \
  -F 'response_format=url'
```

Để curl tự đặt Content-Type multipart cùng boundary. Các ảnh được dùng làm tham chiếu để tạo ảnh mới. Gửi trường `mask` sẽ bị lỗi 400 vì chưa hỗ trợ inpainting theo vùng. Phản hồi có cùng cấu trúc với `/v1/images/generations`, gồm cả chế độ tác vụ khi gửi `async=true`.

### `POST /v1/videos` — tạo tác vụ video

| Trường | Bắt buộc / mặc định | Cách dùng |
| --- | --- | --- |
| `prompt` | Bắt buộc, chuỗi không rỗng | Mô tả video |
| `model` | `muse-video` | Model/alias video |
| `size` | Không bắt buộc | Chuỗi kích thước/tỉ lệ, ví dụ `16:9` |
| `duration` | Không bắt buộc, số nguyên 1–60 | Thời lượng yêu cầu, tính bằng giây |
| `seconds` | Không bắt buộc, số nguyên 1–60 | Tên thay thế cho `duration`; `duration` được ưu tiên |
| `image` | Không bắt buộc | Ảnh khung hình đầu, dạng data URL, URL HTTP(S) hoặc base64 |
| `input_reference` | Không bắt buộc | Tên thay thế cho `image`; `image` được ưu tiên |

Endpoint luôn tạo tác vụ nền và trả HTTP 200 với ID; chưa có video ngay trong phản hồi đầu tiên. Giới hạn 1–60 là kiểm tra đầu vào của API, không bảo đảm upstream tạo đúng mọi thời lượng trong khoảng đó.

### Truy vấn kết quả ảnh/video

- `GET /v1/images/generations/{task_id}`: chỉ nhận ID tác vụ ảnh.
- `GET /v1/videos/{task_id}`: chỉ nhận ID tác vụ video.

Cả hai trả 404 nếu ID không tồn tại hoặc thuộc loại tác vụ khác. Body chung minh họa:

```json
{
  "id": "task_xxx",
  "object": "video",
  "status": "queued",
  "progress": 0,
  "created_at": 1730000000,
  "model": "muse-video",
  "result": null,
  "error": null
}
```

Đối với ảnh, `object` là `image.task`. `status` có thể là `queued`, `running`, `succeeded`, `failed`, `cancelled`; `progress` nằm trong 0–100 và không nhất thiết cập nhật liên tục.

| Trạng thái | Cách xử lý |
| --- | --- |
| `queued`, `running` | Chờ rồi gọi lại endpoint trạng thái, ví dụ sau 2–5 giây |
| `succeeded` | Ảnh: đọc `result.data[].url`; video: đọc `result.url`, `result.mime`, `result.width`, `result.height` |
| `failed` | Đọc `error.message`, `error.code`; không suy ra thành công chỉ từ HTTP 200 |
| `cancelled` | Tác vụ đã dừng |

Tác vụ chưa kết thúc được nạp lại sau sự cố khởi động sẽ chuyển thành `failed` với mã `interrupted`; server không tự tiếp tục chúng. Khi shutdown bình thường, các tác vụ đang chạy được yêu cầu hủy.

### `GET /v1/media/{name}` — tải tệp kết quả

Trả trực tiếp dữ liệu nhị phân với MIME tương ứng và `Cache-Control: public, max-age=86400`. Endpoint **không cần API key** để client có thể nhúng ảnh/video. Ai có URL đều có thể tải tệp khi tệp còn tồn tại; media có thể bị dọn theo chính sách lưu trữ.

### Admin API — tài khoản

Tất cả endpoint dưới đây cần admin key. Phản hồi `account` là bản thông tin công khai của tài khoản, không chứa giá trị cookie.

| Endpoint | Dữ liệu gửi / phản hồi |
| --- | --- |
| `GET /admin/accounts` | Trả `{"data":[...]}` chứa tài khoản trong kho đang dùng |
| `POST /admin/accounts` | Body: `cookies` bắt buộc; `label` mặc định `""`, `enabled` mặc định `true`, `cookie_expires` mặc định `{}`. Trả `account`, `missing_cookies` |
| `POST /admin/accounts/import` | Body `{"accounts":[...]}`, ít nhất 1 phần tử theo schema tạo tài khoản. Trả `data[]` có `index`, `ok`, thông tin tài khoản hoặc lỗi |
| `PATCH /admin/accounts/{account_id}` | Sửa các trường tùy chọn `label`, `enabled`, `cookies`, `cookie_expires`. Trả `{"account":{...}}` |
| `DELETE /admin/accounts/{account_id}` | Xóa khỏi pool/kho; trả `{"deleted":"<id>"}` |
| `POST /admin/accounts/{account_id}/renew` | Không cần body; gia hạn cookie và đánh thức VM. Trả `ok` cùng `meta` hoặc `error` |
| `POST /admin/accounts/{account_id}/reset` | Không cần body; bỏ cooldown/lỗi và các chặn tạm thời, đặt trạng thái active. Không thay cookie hoặc cấp lại quota |
| `GET /admin/accounts/{account_id}/quota` | Trả `{"account_id":"...","quota":{...}}`; thêm `?refresh=true` để bỏ cache và đọc lại |

Không có route `GET /admin/accounts/{account_id}` riêng; lấy chi tiết từ danh sách tài khoản.

`POST` tạo/import nhận cookie theo ba dạng: object tên–giá trị, chuỗi header Cookie, hoặc danh sách cookie export có `name`, `value`, thời hạn tùy chọn. `PATCH` chỉ nhận `cookies` dạng object và **thay toàn bộ bộ cookie**, không gộp từng trường. `cookie_expires` là ánh xạ tên cookie tới Unix timestamp.

```bash
curl http://127.0.0.1:18610/admin/accounts \
  -H "Authorization: Bearer $MUSE_ADMIN_KEY" \
  -H "Content-Type: application/json" \
  -d '{"label":"Tài khoản 1","cookies":{"hatch_sess":"THAY_GIA_TRI","hatch_native_auth_device":"THAY_GIA_TRI"}}'

curl -X PATCH http://127.0.0.1:18610/admin/accounts/acc_xxx \
  -H "Authorization: Bearer $MUSE_ADMIN_KEY" \
  -H "Content-Type: application/json" \
  -d '{"enabled":false}'
```

Khác launcher, Admin API có thể lưu bộ cookie thiếu trường cần thiết và báo tên trường qua `missing_cookies`; thành công khi lưu không chứng minh tài khoản đăng nhập được. Import hàng loạt trả lỗi riêng cho lỗi xử lý cookie từng phần tử; lỗi schema của toàn bộ request vẫn có thể trả 400 trước khi xử lý batch.

Quota browser được cache mặc định 30 phút; có thể trả 409 `account_busy` nếu mọi tab đều bận, hoặc 501 nếu driver không hỗ trợ. Gia hạn có thể trả HTTP 200 nhưng `ok:false`, vì vậy cần kiểm tra body.

### Admin API — API key

| Endpoint | Dữ liệu gửi / phản hồi |
| --- | --- |
| `GET /admin/keys` | `data[]` chứa key đã tạo và usage; `builtin[]` chứa thống kê của danh tính `legacy`, `admin` |
| `POST /admin/keys` | Body: `name` bắt buộc dài 1–100 ký tự, `note` tùy chọn tối đa 500 ký tự. Trả `key` và `api_key` dạng đầy đủ **chỉ một lần** |
| `PATCH /admin/keys/{key_id}` | Sửa `name`, `note`, `revoked`; trả `{"key":{...}}`. `revoked:true` vô hiệu hóa key |
| `DELETE /admin/keys/{key_id}` | Xóa key; trả `{"deleted":"<id>"}` |
| `GET /admin/keys/usage` | Thống kê theo `key_id`, kể cả key đã xóa còn trong nhật ký; trả `since`, `data[]` |

Usage gồm `total`, `requests_24h`, `errors_24h`, `last_request_at`; số liệu phụ thuộc lịch sử còn được lưu. Các thao tác PATCH/DELETE áp dụng cho key trong kho, không đổi key cấu hình `legacy` hoặc `admin`.

```bash
curl http://127.0.0.1:18610/admin/keys \
  -H "Authorization: Bearer $MUSE_ADMIN_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name":"Ứng dụng cá nhân","note":"Client chat"}'
```

### Admin API — tác vụ, nhật ký và thống kê

| Endpoint | Tham số / phản hồi |
| --- | --- |
| `GET /admin/status` | Trả `version`, `driver`, `capabilities`, `accounts` |
| `GET /admin/tasks` | Query `limit`, mặc định 100. Trả `data[]` mới nhất trước, gồm request, result, error và trạng thái |
| `POST /admin/tasks/{task_id}/cancel` | Không cần body. Trả `{"cancelled":true}` khi đã gửi yêu cầu hủy tác vụ đang chạy; `false` nếu không còn tác vụ đang chạy với ID đó |
| `GET /admin/requests` | Truy vấn nhật ký có phân trang; trả `data[]`, `total` |
| `GET /admin/stats` | Query `window=1h`, `24h` hoặc `7d`, mặc định `24h` |
| `GET /admin/extension.zip` | Tải ZIP extension, kiểu `application/zip`; trả 404 nếu không có tài nguyên extension |

`cancelled:true` xác nhận đã yêu cầu hủy; kiểm tra lại trạng thái để xác nhận hoàn tất. API chưa có endpoint client `/v1/.../cancel`; dùng route quản trị ở trên.

Bộ lọc cho `GET /admin/requests`:

| Query | Ý nghĩa |
| --- | --- |
| `key_id`, `account_id` | Lọc theo ID key hoặc tài khoản |
| `status` | `2xx`, `3xx`, `4xx`, `5xx`, hoặc `failed` |
| `path` | Lọc theo tiền tố đường dẫn request |
| `since` | Unix timestamp, tính bằng giây |
| `hide_polls` | `true` để ẩn request kiểm tra trạng thái tác vụ; mặc định `false` |
| `limit` | 1–500, mặc định 100 |
| `offset` | Vị trí bắt đầu, từ 0; mặc định 0 |

```bash
curl 'http://127.0.0.1:18610/admin/requests?status=failed&hide_polls=true&limit=20&offset=0' \
  -H "Authorization: Bearer $MUSE_ADMIN_KEY"

curl 'http://127.0.0.1:18610/admin/stats?window=24h' \
  -H "Authorization: Bearer $MUSE_ADMIN_KEY"
```

Thống kê có `total`, `errors`, `server_errors`, `error_rate`, độ trễ `latency_ms.p50/p95`, các nhóm `by_key`, `by_account`, `by_model`, `by_status` và chuỗi thời gian `series`. Các tác vụ nền có thể thất bại sau khi request tạo tác vụ đã trả 200; xem cả kết quả tác vụ và bộ lọc `failed`.

### Mã lỗi và giới hạn tương thích

Các lỗi do ứng dụng xử lý dùng cấu trúc:

```json
{"error":{"message":"invalid or missing API key","type":"authentication_error","code":"invalid_api_key"}}
```

| HTTP | Code điển hình | Ý nghĩa |
| --- | --- | --- |
| 400 | `invalid_request` | Body/tham số không hợp lệ, sai loại model hoặc chức năng đầu vào không hỗ trợ |
| 401 | `invalid_api_key` | Thiếu key, key sai hoặc đã bị thu hồi |
| 404 | `not_found` | Không tìm thấy tài khoản, key, tác vụ hoặc tài nguyên |
| 409 | `account_busy` | Tài khoản đang bận khi đọc quota |
| 429 | `upstream_quota_exhausted` | Upstream hết quota |
| 501 | `not_implemented` | Driver chưa triển khai chức năng |
| 502 | `upstream_error`, `upstream_auth_failed`, `upstream_refused` | Lỗi upstream, phiên không hợp lệ hoặc upstream không tạo kết quả được yêu cầu |
| 503 | `no_account_available` | Không có tài khoản khả dụng |
| 504 | `upstream_timeout` | Upstream quá thời gian chờ |

Lỗi validation JSON/query được ứng dụng chuyển thành **400**, không phải 422 mặc định của FastAPI. Lỗi phát sinh sau khi SSE bắt đầu không thể đổi HTTP status đã gửi; client cần đọc cả nội dung lỗi trong stream. Nhiều trường lạ được schema chấp nhận để tương thích, nhưng điều đó không có nghĩa tính năng tương ứng đã được thực hiện.

## Kiểm thử

```bash
uv sync --locked --extra dev
uv run --extra dev python -m pytest
```

## Cấu trúc

```text
Muse2APICookies/
├── main.py
├── pyproject.toml
├── uv.lock
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── data/                  # Tự tạo khi dùng
└── muse2api/               # Thư viện server, mã nguồn và tests
    ├── pyproject.toml
    ├── src/muse2api/
    └── tests/
```

`src/` mẫu ở thư mục gốc đã được bỏ; `muse2api/src/` chứa mã server thực tế.
Không đưa `.env` hoặc `data/` vào Git.
