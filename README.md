**eFlesh Sensor Development**

**Distributed Magnetic Tactile Sensing for Contact Detection and Localisation on Universal Robots UR5**

This repository contains the hardware development, experimental data and software implementation/packages required for the
implementation of a distributed magnetic tactile feedback system for the UR5

This project was developed as a part of a Bachelor of Electrical & Electronics Engineering (Honours) Thesis at Curtin University, Bentley, Western Australia

This project expands on the work previously completed by eFlesh originators and utulises hardware from the ReSkin originators:

**Credits and Acknowledgements**

eFlesh

  Website: https://e-flesh.com/

  Paper: https://arxiv.org/abs/2506.09994

  Accompanying GitHub Repo: https://github.com/notvenky/eFlesh

ReSkin

  Website: https://reskin.dev/

  Paper: https://openreview.net/pdf?id=87_OJU4sw3V

  Accompanying GitHub Repo: https://github.com/raunaqbhirangi/reskin_sensor

**Special thanks to Curtin Robotics Club for providing access to the UR5 for this project**
Website: https://croc.tidyhq.com/

**ABOUT**
This project builds upon existing research into eFlesh tactile magnetic sensing technology and expands to implement simple pause/play functionality to a UR5
The included ROS2 package includes three nodes:
-eFlesh data publisher
-contact detection
-UR5 collision monitor

A demonstration video is available here: https://www.youtube.com/watch?v=mf6Gzsx6Pog

This project features:
  Modular I2C architecture eFlesh sensors
  Improvements to lattice fabrication and reliability
  Custom 3D printing files (3mf and STEP)
  ROS2 integration and eFlesh package for UR5
  Basic Collision response

**Repo Structure**

```text
eFlesh_Sensor_Development/
│
├── arduino/
│   └── Microcontroller firmware
│
├── experimental_data/
│   └── Sensor development and experimental data
│
├── src/
│   └── eflesh_sensor/
│       └── ROS 2 sensor integration package
│
├── ur5_loop.py
│   └── UR5 movement demonstration script
│
└── README.md
```
