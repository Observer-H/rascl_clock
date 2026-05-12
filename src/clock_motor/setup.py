from setuptools import find_packages, setup

package_name = "clock_motor"

setup(
    name=package_name,
    version="0.0.1",
    packages=find_packages(),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
        (f"share/{package_name}/launch", ["launch/clock.launch.py"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="student",
    maintainer_email="student@example.com",
    description="Python ROS2 nodes for a motor driven clock hand.",
    license="MIT",
    entry_points={
        "console_scripts": [
            "motor_node = clock_motor.motor_node:main",
            "sequence_action_server = clock_motor.sequence_action_server:main",
        ],
    },
)
