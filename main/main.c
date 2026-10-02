#include <stdio.h>

#include "driver/ledc.h"
#include "embutidos.h"
#include "esp_err.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "inferencia.h"
#include "serial.h"
#include "soc/gpio_num.h"

#define SERVO_GPIO GPIO_NUM_4
#define SERVO_FREQ_HZ 50
#define SERVO_PERIOD_US 20000
#define SERVO_RESOLUTION LEDC_TIMER_14_BIT
#define ANGLE_HOLD_MS 1500

static uint32_t duty_for_pulse_us(uint32_t pulse_us)
{
    const uint32_t duty_max = (1u << 14) - 1u;
    return (uint32_t)(((uint64_t)pulse_us * duty_max) / SERVO_PERIOD_US);
}

static void servo_set_pulse_us(uint32_t pulse_us)
{
    ESP_ERROR_CHECK(ledc_set_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0, duty_for_pulse_us(pulse_us)));
    ESP_ERROR_CHECK(ledc_update_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0));
}

static void servo_init(void)
{
    const ledc_timer_config_t timer = {
        .speed_mode = LEDC_LOW_SPEED_MODE,
        .duty_resolution = SERVO_RESOLUTION,
        .timer_num = LEDC_TIMER_0,
        .freq_hz = SERVO_FREQ_HZ,
        .clk_cfg = LEDC_AUTO_CLK,
    };
    const ledc_channel_config_t channel = {
        .gpio_num = SERVO_GPIO,
        .speed_mode = LEDC_LOW_SPEED_MODE,
        .channel = LEDC_CHANNEL_0,
        .intr_type = LEDC_INTR_DISABLE,
        .timer_sel = LEDC_TIMER_0,
        .duty = 0,
        .hpoint = 0,
    };

    ESP_ERROR_CHECK(ledc_timer_config(&timer));
    ESP_ERROR_CHECK(ledc_channel_config(&channel));
}

void app_main(void)
{
    int i;

    servo_init();
    servo_set_pulse_us(PULSO_SERVO_0_US);

    if (inferencia_iniciar() != 0) {
        printf("inferencia falhou\n");
        fflush(stdout);
        while (true) {
            vTaskDelay(pdMS_TO_TICKS(1000));
        }
    }

    for (i = 0; i < JANELA_N; i++) {
        char texto[64];
        int classe = classificar_pcm(janela_pcm[i]);
        int pulso;

        if (classe < 0) {
            printf("inferencia falhou\n");
            fflush(stdout);
            servo_set_pulse_us(PULSO_SERVO_0_US);
            break;
        }
        pulso = linhas_da_janela(classe, texto, sizeof(texto));
        printf("%s", texto);
        fflush(stdout);
        if (pulso != 0) {
            servo_set_pulse_us((uint32_t)pulso);
        }
        vTaskDelay(pdMS_TO_TICKS(ANGLE_HOLD_MS));
    }

    while (true) {
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}
