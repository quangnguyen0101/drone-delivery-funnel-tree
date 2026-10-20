#!/bin/bash
# entrypoint.sh - Khởi động Gazebo với world được truyền vào
# Nếu không có đối số, dùng world trống

WORLD=${1:-/root/worlds/empty.world}

echo "=== Gazebo Sample Project ==="
echo "Loading world: $WORLD"

# Chạy gzserver với world được chọn
exec gzserver "$WORLD"
