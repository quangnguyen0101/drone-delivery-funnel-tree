FROM gazebo:gzserver8

# Copy world file vào container
COPY world.sdf /root/world.sdf

# Mặc định chạy Gazebo server với world.sdf
CMD ["gzserver", "/root/world.sdf"]
