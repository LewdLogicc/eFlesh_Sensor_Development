from setuptools import find_packages, setup

package_name = 'eflesh_sensor'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/eflesh_launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='shea',
    maintainer_email='shea@todo.todo',
    description='TODO: Package description',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
    'console_scripts': [
        'eflesh_publisher = eflesh_sensor.eflesh_publisher:main',
        'collision_detector = eflesh_sensor.collision_detector:main',
        'ur5_collision_monitor = eflesh_sensor.ur5_collision_monitor:main',
    ],
},
)
