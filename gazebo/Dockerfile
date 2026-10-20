FROM gazebo:gzserver8

# Thiết lập thư mục làm việc
WORKDIR /root

# Copy các world vào container
COPY worlds/ /root/worlds/

# Copy models vào thư mục model của Gazebo
COPY models/ /root/.gazebo/models/

# Copy script hỗ trợ
COPY scripts/ /root/scripts/

# Cấp quyền chạy cho entrypoint
COPY entrypoint.sh /root/entrypoint.sh
RUN chmod +x /root/entrypoint.sh

# Mặc định chạy entrypoint (chọn world trống)
ENTRYPOINT ["/root/entrypoint.sh"]
CMD ["/root/worlds/empty.world"]
