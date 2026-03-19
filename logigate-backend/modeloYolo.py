from roboflow import Roboflow

rf = Roboflow(api_key="nFwszjsA0FpvEr9GMKqD")
project = rf.workspace("joshua-obr6u").project("placasdetect")
version = project.version(1)
dataset = version.download("yolov11")
                