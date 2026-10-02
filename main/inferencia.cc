#include "inferencia.h"

#include <math.h>

#include "embutidos.h"
#include "mfcc.h"
#include "rotulos.h"
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/micro/micro_mutable_op_resolver.h"
#include "tensorflow/lite/schema/schema_generated.h"

namespace {
constexpr int kOps = 7;
constexpr size_t kArena = 32 * 1024;
alignas(16) uint8_t tensor_arena[kArena];
tflite::MicroMutableOpResolver<kOps> resolver;
tflite::MicroInterpreter *interpreter = nullptr;
}  // namespace

extern "C" int inferencia_iniciar(void)
{
    const tflite::Model *modelo = tflite::GetModel(modelo_tflite);
    if (modelo->version() != TFLITE_SCHEMA_VERSION) {
        return -1;
    }
    if (resolver.AddReshape() != kTfLiteOk || resolver.AddStridedSlice() != kTfLiteOk ||
        resolver.AddSquaredDifference() != kTfLiteOk || resolver.AddMean() != kTfLiteOk ||
        resolver.AddDequantize() != kTfLiteOk || resolver.AddNeg() != kTfLiteOk ||
        resolver.AddQuantize() != kTfLiteOk) {
        return -1;
    }
    static tflite::MicroInterpreter criado(modelo, resolver, tensor_arena, kArena);
    if (criado.AllocateTensors() != kTfLiteOk) {
        return -1;
    }
    interpreter = &criado;
    return 0;
}

extern "C" int classificar_pcm(const int16_t *pcm)
{
    static double mfcc[MFCC_QUADROS * MFCC_COEF];
    TfLiteTensor *entrada;
    TfLiteTensor *saida;
    int8_t *quantizado;
    int8_t *logits;
    int i;
    int melhor;
    float escala;
    int zero;

    if (interpreter == nullptr) {
        return -1;
    }
    mfcc_janela(pcm, mfcc);
    entrada = interpreter->input(0);
    saida = interpreter->output(0);
    if (entrada->bytes != MFCC_QUADROS * MFCC_COEF || saida->bytes != ROTULO_N) {
        return -1;
    }
    escala = entrada->params.scale;
    zero = entrada->params.zero_point;
    quantizado = entrada->data.int8;
    for (i = 0; i < MFCC_QUADROS * MFCC_COEF; i++) {
        int valor = (int)lrint(mfcc[i] / (double)escala + (double)zero);
        if (valor > 127) {
            valor = 127;
        }
        if (valor < -128) {
            valor = -128;
        }
        quantizado[i] = (int8_t)valor;
    }
    if (interpreter->Invoke() != kTfLiteOk) {
        return -1;
    }
    logits = saida->data.int8;
    melhor = 0;
    for (i = 1; i < ROTULO_N; i++) {
        if (logits[i] > logits[melhor]) {
            melhor = i;
        }
    }
    return melhor;
}
