# Runbook

## API trả lỗi cao

1. Kiểm tra `/health`, `/ready` và Prometheus alert.
2. Xem tỷ lệ Redis fallback và Kafka consumer lag.
3. Nếu candidate model đang nhận traffic, đặt candidate weight về 0.
4. Xác minh model champion và feature schema version.

## Feature freshness vượt SLO

1. Kiểm tra Redpanda health và consumer lag.
2. Kiểm tra duplicate/late-event rate.
3. Scale feature worker nếu backlog tăng liên tục.
4. Chỉ replay từ offset đã xác minh; dedup marker phải còn TTL.

## Rollback model

1. Disable candidate/shadow traffic.
2. Trỏ stable manifest về champion digest trước đó.
3. Xác minh p95, error rate và output contract.
4. Ghi incident với model, feature, dataset và commit lineage.
