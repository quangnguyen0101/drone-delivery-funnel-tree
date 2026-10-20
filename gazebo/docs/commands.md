# Lệnh Gazebo thường dùng

## Chạy Gazebo server
```bash
gzserver /root/worlds/empty.world
```

## Liệt kê model trong world
```bash
gz model --list
```

## Liệt kê topic đang phát
```bash
gz topic -l
```

## Gửi lệnh dừng mô phỏng
```bash
gz service -s /gazebo/pause_physics --reqtype gz.msgs.Boolean --reptype gz.msgs.Boolean --timeout 1000 --data true
```

## Tiếp tục mô phỏng
```bash
gz service -s /gazebo/unpause_physics --reqtype gz.msgs.Boolean --reptype gz.msgs.Boolean --timeout 1000 --data false
```

## Trong Docker container

Chạy lệnh bên trong container đang chạy:
```bash
docker exec -it gazebo-sample bash
```

Sau đó chạy các lệnh Gazebo như trên.
