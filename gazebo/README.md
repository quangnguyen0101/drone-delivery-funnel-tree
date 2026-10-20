# Gazebo Docker (học Docker + Gazebo)

Folder này chứa ví dụ chạy **Gazebo server (gzserver)** trong Docker, dùng để học tập. Không liên quan đến PX4 hay MAVSDK.

## Cấu trúc

```
gazebo/
├── Dockerfile      # build image từ gazebo:gzserver8
├── world.sdf       # world mẫu (mặt đất + hộp)
└── README.md       # file này
```

## Build image

```bash
cd src/my/gazebo
docker build -t my-gazebo-app .
```

## Chạy container

### Chạy nền (khuyên dùng)

```bash
docker run -d --name gazebo-app my-gazebo-app
```

### Chạy tương tác (xem log trực tiếp)

```bash
docker run --name gazebo-app my-gazebo-app
```

### Chạy với world file khác

```bash
docker run --name gazebo-app my-gazebo-app gzserver /root/world.sdf
```

## Kiểm tra container đang chạy

```bash
docker ps --filter name=gazebo-app --format "{{.Status}} {{.Names}}"
```

## Xem log

```bash
docker logs gazebo-app
```

## Dừng và xoá container

```bash
docker stop gazebo-app
docker rm gazebo-app
```

## Ghi nhớ

- `gazebo:gzserver8` chỉ cài Gazebo server, không có giao diện GUI.
- Nếu muốn dùng Gazebo với giao diện, hãy dùng image `gazebo:gzsim` hoặc cài thêm `gz-sim`.
- Không cần PX4/MAVSDK cho mục đích học Gazebo này.
