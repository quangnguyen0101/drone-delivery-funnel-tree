"""Ví dụ spawn model trong Gazebo.

Gazebo Harmonic (gz) dùng gz-transport, không phải ROS.
Muốn lập trình sâu cần cài gz-transport Python bindings.
Cách đơn giản nhất để thêm model: khai báo trong file .sdf world.
"""


def spawn_box():
    print("Để spawn model vào Gazebo, bạn có thể:")
    print("  1. Thêm model vào file .sdf world rồi chạy lại")
    print("  2. Dùng gz service để spawn tại runtime:")
    print(
        "  gz service -s /world/empty/create "
        "--reqtype gz.msgs.EntityFactory --reptype gz.msgs.Boolean --timeout 5000"
    )


if __name__ == "__main__":
    spawn_box()
