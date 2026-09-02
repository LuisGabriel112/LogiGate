# language: es
Característica: Optimización de velocidad del motor de detección de daños en CPU

  Escenario: El preprocesamiento reduce la imagen al tamaño de inferencia configurado
    Dado una imagen más grande que el tamaño de inferencia de daños
    Cuando se preprocesa la imagen
    Entonces el lado mayor debe quedar igual al tamaño de inferencia configurado

  Escenario: El análisis de daños invoca el modelo con el tamaño de inferencia reducido
    Dado una imagen ya preprocesada
    Cuando se analiza la imagen
    Entonces el modelo debe invocarse con imgsz igual al tamaño de inferencia configurado

  Escenario: Se prefiere el modelo exportado a OpenVINO cuando existe
    Dado que existe un directorio "best_openvino_model" junto al modelo .pt
    Cuando se resuelve la ruta del modelo de daños a cargar
    Entonces debe usarse la ruta del directorio OpenVINO

  Escenario: Se usa el modelo .pt original cuando no existe export OpenVINO
    Dado que no existe un directorio "best_openvino_model" junto al modelo .pt
    Cuando se resuelve la ruta del modelo de daños a cargar
    Entonces debe usarse la ruta del archivo .pt original

  Escenario: Se limita el número de hilos CPU antes de cargar PyTorch/OpenVINO
    Dado que PyTorch (motor de placas) y OpenVINO (motor de daños) corren en el mismo proceso
    Y ambos por defecto intentan usar todos los núcleos del CPU
    Cuando arranca la aplicación
    Entonces OMP_NUM_THREADS debe fijarse a un valor acotado antes de importar esas librerías
    Para evitar que compitan por CPU y se degrade el tiempo de inferencia entre requests
