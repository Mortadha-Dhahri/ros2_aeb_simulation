FROM osrf/ros:jazzy-ros-core
 
RUN apt-get update && apt-get install -y \
    ros-jazzy-rclpy \
    ros-jazzy-std-msgs \
    ros-jazzy-sensor-msgs \
    python3-colcon-common-extensions \
    && rm -rf /var/lib/apt/lists/*
 
RUN echo "source /opt/ros/jazzy/setup.bash" >> /root/.bashrc && \
    echo "[ -f /aeb_ws/install/setup.bash ] && source /aeb_ws/install/setup.bash" >> /root/.bashrc
 
WORKDIR /aeb_ws