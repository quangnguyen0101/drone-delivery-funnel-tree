# Gazebo Sample Project

Dự án mẫu để học **Gazebo + Docker**. Mục tiêu: bạn có thể chạy, quan sát, và sửa thử để hiểu Gazebo hoạt động như thế nào.

## Cấu trúc

```
gazebo/
├── Dockerfile              # Build image từ gazebo:gzserver8
├── entrypoint.sh           # Script khởi động container
├── README.md               # Tài liệu hướng dẫn (file này)
├── worlds/                 # Các file world (.sdf)
│   ├── empty.world         # Trống trơn (chỉ mặt đất + ánh sáng)
│   ├── obstacles.world     # Có các vật cản (hộp, cầu)
│   └── drone_landing.world # Mô phỏng sân bay hạ cánh đơn giản
├── models/                 # Các model tùy chỉnh
│   └── simple_box/         # Hộp đơn giản
│       ├── model.config
│       └── model.sdf
├── scripts/                # Script hỗ trợ
│   └── spawn_box.py        # Script PythonDrop hộp vào world bằng API
└── docs/                   # Tài liệu bổ sung
    └── commands.md         # Lệnh Gazebo thường dùng
```

## Cách build image

```bash
cd src/my/gazebo
docker build -t gazebo-sample .
```

## Cách chạy

### Chạy world trống (mặc định)
```bash
docker run -d --name gazebo-sample gazebo-sample
```

### Chạy world có vật cản
```bash
docker run -d --name gazebo-sample gazebo-sample /root/worlds/obstacles.world
```

### Chạy tương tác (xem log trực tiếp)
```bash
docker run --name gazebo-sample gazebo-sample /root/worlds/empty.world
```

## Kiểm tra container đang chạy

```bash
docker ps --filter name=gazebo-sample
```

## Xem log Gazebo

```bash
docker logs gazebo-sample
```

## Vào container để thao tác trực tiếp

```bash
docker exec -it gazebo-sample bash
```

Bên trong container, bạn có thể chạy:
- `gzserver /root/worlds/empty.world` — chạy world
- `gz model --list` — liệt kê model
- `gz topic -l` — liệt kê topic đang phát

## Dừng và xoá

```bash
docker stop gazebo-sample
docker rm gazebo-sample
```

## Các file quan trọng giải thích

| File | Mục đích |
|------|----------|
| `Dockerfile` | Xây dựng image Gazebo, copy worlds và models vào |
| `entrypoint.sh` | Chạy khi container khởi động, chọn world mặc định |
| `worlds/empty.world` | World đơn giản nhất: mặt đất + mặt trời |
| `worlds/obstacles.world` | World có hộp và cầu để quan sát va chạm |
| `models/simple_box/` | Định nghĩa model hộp tùy chỉnh |
| `scripts/spawn_box.py` | Ví dụ dùng Python để spawn model vào Gazebo |

## Tùy chỉnh world

Sửa file `worlds/empty.world` để:
- Thay đổi màu nền (`<ambient>` trong `<scene>`)
- Thêm ánh sáng khác (`<light>`)
- Thêm model khác vào `<world>`

Sau khi sửa, rebuild image và chạy lại container.
