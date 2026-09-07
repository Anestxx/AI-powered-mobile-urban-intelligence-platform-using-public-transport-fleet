\# Pothole Dataset and Model Training



This module prepares the dataset and training pipeline for pothole detection.



\## Dataset Structure



\- images/train: training images

\- images/val: validation images

\- images/test: testing images

\- labels/train: training annotations

\- labels/val: validation annotations

\- labels/test: testing annotations



\## Target Class



0 = pothole



\## Training



The final YOLO model will be trained on an NVIDIA GPU and the resulting best.pt will be transferred to:



01\_ai\_edge/models/best.pt

