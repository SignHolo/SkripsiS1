# SkripsiS1
Skripsi S1 Muhammad Juan Hamzah

Smart Lighting System for the Telecommunication Laboratory of Jakarta State University Using Computer Vision

Description:
This project was developed to fulfill the final requirement for a Bachelor's Degree in Electronic Engineering Education at Jakarta State University.

The topic was selected based on several key considerations:

The rapid advancement of technology

The need for automated lighting systems

The importance of energy efficiency in lighting usage

The system intelligently adjusts indoor lighting in real time using computer vision, based on human presence and position within the room. It is specifically designed for use in the Telecommunication Laboratory and operates within a local network environment.

Key Parameters Monitored:

Light intensity (lux), measured against Indonesian National Standards (SNI)
Accuracy and effectiveness of the human detection system

System Workflow:

Input is captured through an IP camera
Human detection and zone mapping are processed via computer vision
Lighting intensity is automatically adjusted based on detected human zones
All components communicate within a local network

Hardware Used:

IP Camera – for video input
Raspberry Pi 5 – main processing unit
ESP32 – controls lighting outputs
LED Floodlights – as the lighting source

Programming Languages:

Python – for main system logic and computer vision
MicroPython – for ESP32 microcontroller control

Libraries & Frameworks Used:

cv2 (OpenCV) – for image processing
torch – PyTorch framework for AI inference
numpy – for numerical computations
ultralytics YOLO (YOLOv11n model) – for real-time object detection
