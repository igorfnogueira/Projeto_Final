idf_component_register(SRCS "main.c" "inferencia.cc" "embutidos.c"
                            "../host/mfcc.c" "../host/serial.c"
                       INCLUDE_DIRS "." "../host"
                       REQUIRES esp_driver_ledc espressif__esp-tflite-micro)
