# Ví dụ spawn model bằng Python (cơ bản)

File này minh họa cách dùng Python để tương tác với Gazebo qua service/topic.
Lưu ý: Gazebo Harmonic (gz) sử dụng Ignition Transport, không phải ROS.
Bạn có thể cài thư viện `gz-transport` Python nếu cần lập trình sâu.

```python
# scripts/spawn_box.py
# Ví dụ khái niệm - cần cài thêm thư viện gz-transport-python để chạy thật

def spawn_box():
    print("Để spawn model vào Gazebo, bạn có thể:")
    print("  1. Thêm model vào file .sdf world và chạy lại")
    print("  2. Hoặc dùng gz service để spawn model tại runtime")
    print("Ví dụ lệnh terminal:")
    print("  gz service -s /world/empty/create --reqtype gz.msgs.EntityFactory --reptype gz.msgs.Boolean --timeout 5000")

if __name__ == "__main__":
    spawn_box()
```
