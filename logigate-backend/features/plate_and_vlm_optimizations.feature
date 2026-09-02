# language: es
Característica: Optimización de tiempos de reconocimiento de placas y VLM

  Escenario: Ignorar detecciones YOLO por debajo del umbral de confianza de placas
    Dado que el motor YOLO se invoca para detectar placas
    Cuando se procesa una imagen
    Entonces debe invocarse con el umbral de confianza configurado (0.30)

  Escenario: Solo se ejecuta OCR sobre la caja de mayor confianza
    Dado que el motor YOLO detecta varias cajas válidas con distintas confianzas
    Cuando se procesa la imagen
    Entonces el lector OCR debe invocarse exactamente una vez
    Y debe invocarse sobre el recorte de la caja con mayor confianza

  Escenario: Sin cajas detectadas no se ejecuta OCR ni se devuelven placas
    Dado que el motor YOLO no detecta ninguna caja
    Cuando se procesa la imagen
    Entonces el lector OCR no debe invocarse
    Y el resultado debe ser una lista vacía

  Escenario: Texto de placa demasiado corto se descarta
    Dado que el OCR devuelve un texto de menos de 4 caracteres
    Cuando se procesa la imagen
    Entonces el resultado debe ser una lista vacía

  Escenario: Formatear placa con guion cuando tiene 6 o más caracteres
    Dado un texto de placa limpio "ABC1234"
    Cuando se formatea la placa
    Entonces el resultado debe ser "ABC-1234"

  Escenario: No formatear placas cortas
    Dado un texto de placa limpio "AB12"
    Cuando se formatea la placa
    Entonces el resultado debe ser "AB12"

  Escenario: Filtrar bloques de texto OCR fuera de la banda vertical central
    Dado bloques OCR en el centro y en el borde de un recorte
    Cuando se filtran los bloques por banda central
    Entonces solo el bloque del centro debe conservarse

  Escenario: Descartar leyenda pequeña aunque esté cerca del centro vertical
    Dado un bloque alto con el texto de la placa y un bloque bajo con la leyenda del estado, ambos dentro de la banda central
    Cuando se filtran los bloques por banda central
    Entonces solo el bloque alto (la placa) debe conservarse

  Escenario: Limpiar bloque OCR quita palabras de ruido y símbolos
    Dado un bloque OCR con texto "mexico abc-123!"
    Cuando se limpia el bloque
    Entonces el resultado debe ser "ABC123"

  Escenario: VLM_ENABLED por defecto habilita el motor VLM
    Dado que la variable de entorno VLM_ENABLED no está definida
    Cuando se consulta si el VLM está habilitado
    Entonces debe responder verdadero

  Escenario: VLM_ENABLED en "false" deshabilita el motor VLM
    Dado que la variable de entorno VLM_ENABLED es "false"
    Cuando se consulta si el VLM está habilitado
    Entonces debe responder falso

  Escenario: VLM_ENABLED es insensible a mayúsculas/minúsculas
    Dado que la variable de entorno VLM_ENABLED es "FALSE"
    Cuando se consulta si el VLM está habilitado
    Entonces debe responder falso
