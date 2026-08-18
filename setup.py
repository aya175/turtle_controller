from setuptools import find_packages, setup

package_name = 'turtle_controller'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/turtle_launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Aya',
    maintainer_email='aya@example.com',
    description='Task 7.1 - turtlesim teleop control + color-sensor perception node',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'controller_node = turtle_controller.controller_node:main',
        ],
    },
)
