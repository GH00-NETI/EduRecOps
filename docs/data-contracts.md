# Data contracts

## `learning-events` v1

| Trường | Kiểu | Bắt buộc | Mô tả |
| --- | --- | ---: | --- |
| schema_version | string | Có | Phiên bản schema |
| event_id | UUID | Có | Idempotency key |
| event_type | enum | Có | view/click/enroll/complete/rate/assessment |
| user_id | string | Có | Mã người học |
| course_id | string | Có | Mã khóa học |
| session_id | UUID | Có | Phiên sử dụng |
| event_time | ISO-8601 UTC | Có | Event time |
| device | enum | Không | web/ios/android |
| position | integer | Không | Vị trí item khi hiển thị |
| dwell_seconds | integer | Không | Thời lượng tương tác |
| score | float [0,1] | Với assessment | Điểm chuẩn hóa |

## `recommendation-impressions` v1

Mỗi item được hiển thị phải có một bản ghi, kể cả không có click.

| Trường | Mục đích |
| --- | --- |
| request_id, impression_id | Nối request → slate → outcome |
| policy_id, model_version | Lineage và replay |
| course_id, rank, score | Ranking analysis |
| candidate_source | Coverage theo nguồn |
| propensity | Counterfactual evaluation |
| feature_generated_at, served_at | Freshness và leakage checks |

## Tương thích

Producer không xóa hoặc đổi nghĩa trường trong cùng major version. Consumer phải bỏ qua trường chưa biết. Thay đổi breaking tạo topic/version mới và có cửa sổ dual-read.
