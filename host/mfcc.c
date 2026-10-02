#include "mfcc.h"

#include <math.h>
#include <string.h>

#define TAXA 16000
#define PRE 0.97
#define QUADRO 320
#define PASSO 160
#define FFT_N 512
#define BINS (FFT_N / 2 + 1)
#define MELS 40
#define PISO 1e-10
#define LIFTER 22.0

static double banco[MELS][BINS];
static double base[MFCC_COEF][MELS];
static double lifter[MFCC_COEF];
static double hann[QUADRO];
static int pronto;

static double hz_para_mel(double hz)
{
    return 2595.0 * log10(1.0 + hz / 700.0);
}

static double mel_para_hz(double mel)
{
    return 700.0 * (pow(10.0, mel / 2595.0) - 1.0);
}

static void fft(double *re, double *im, int n)
{
    int i, j, k, bloco, metade;

    for (i = 1, j = 0; i < n; i++) {
        int bit = n >> 1;
        for (; j & bit; bit >>= 1) {
            j ^= bit;
        }
        j ^= bit;
        if (i < j) {
            double tr = re[i];
            double ti = im[i];
            re[i] = re[j];
            im[i] = im[j];
            re[j] = tr;
            im[j] = ti;
        }
    }

    for (bloco = 2; bloco <= n; bloco <<= 1) {
        double ang = -2.0 * 3.14159265358979323846 / bloco;
        double wlen_re = cos(ang);
        double wlen_im = sin(ang);
        metade = bloco >> 1;
        for (i = 0; i < n; i += bloco) {
            double w_re = 1.0;
            double w_im = 0.0;
            for (k = 0; k < metade; k++) {
                int a = i + k;
                int b = a + metade;
                double vr = re[b] * w_re - im[b] * w_im;
                double vi = re[b] * w_im + im[b] * w_re;
                double nr = w_re * wlen_re - w_im * wlen_im;
                double ni = w_re * wlen_im + w_im * wlen_re;
                re[b] = re[a] - vr;
                im[b] = im[a] - vi;
                re[a] += vr;
                im[a] += vi;
                w_re = nr;
                w_im = ni;
            }
        }
    }
}

static void preparar(void)
{
    double mels[MELS + 2];
    int bins[MELS + 2];
    int i, j, k;
    double mel0 = hz_para_mel(0.0);
    double mel1 = hz_para_mel(8000.0);

    if (pronto) {
        return;
    }

    for (i = 0; i < QUADRO; i++) {
        hann[i] = 0.5 - 0.5 * cos(2.0 * 3.14159265358979323846 * i / (QUADRO - 1));
    }

    for (i = 0; i < MELS + 2; i++) {
        double t = (double)i / (double)(MELS + 1);
        double hz = mel_para_hz(mel0 + (mel1 - mel0) * t);
        int bin = (int)floor(((FFT_N + 1) * hz) / TAXA);
        if (bin < 0) {
            bin = 0;
        }
        if (bin > BINS - 1) {
            bin = BINS - 1;
        }
        mels[i] = hz;
        bins[i] = bin;
    }

    memset(banco, 0, sizeof(banco));
    for (i = 0; i < MELS; i++) {
        int esq = bins[i];
        int centro = bins[i + 1];
        int dir = bins[i + 2];
        if (centro > esq) {
            for (j = esq; j < centro; j++) {
                banco[i][j] = (double)(j - esq) / (double)(centro - esq);
            }
        }
        if (dir > centro) {
            for (j = centro; j < dir; j++) {
                banco[i][j] = (double)(dir - j) / (double)(dir - centro);
            }
        }
    }

    for (k = 0; k < MFCC_COEF; k++) {
        double escala = sqrt(2.0 / MELS);
        if (k == 0) {
            escala = sqrt(1.0 / MELS);
        }
        for (j = 0; j < MELS; j++) {
            base[k][j] = escala * cos(3.14159265358979323846 * k * (j + 0.5) / MELS);
        }
        lifter[k] = 1.0 + (LIFTER / 2.0) * sin(3.14159265358979323846 * k / LIFTER);
    }

    (void)mels;
    pronto = 1;
}

void mfcc_janela(const int16_t *pcm, double *saida)
{
    /* Fora da pilha: no ESP32-S3 a tarefa principal não cabe 8 KB de FFT. */
    static double re[FFT_N];
    static double im[FFT_N];
    int i, j, k;

    preparar();

    for (i = 0; i < MFCC_QUADROS; i++) {
        double logmel[MELS];
        int inicio = i * PASSO;

        memset(re, 0, sizeof(re));
        memset(im, 0, sizeof(im));
        for (j = 0; j < QUADRO; j++) {
            int n = inicio + j;
            double amostra = (double)pcm[n];
            if (n > 0) {
                amostra -= PRE * (double)pcm[n - 1];
            }
            re[j] = amostra * hann[j];
        }
        fft(re, im, FFT_N);

        for (j = 0; j < MELS; j++) {
            double energia = 0.0;
            for (k = 0; k < BINS; k++) {
                double pot = re[k] * re[k] + im[k] * im[k];
                energia += banco[j][k] * pot;
            }
            if (energia < PISO) {
                energia = PISO;
            }
            logmel[j] = log(energia);
        }

        for (k = 0; k < MFCC_COEF; k++) {
            double c = 0.0;
            for (j = 0; j < MELS; j++) {
                c += logmel[j] * base[k][j];
            }
            saida[i * MFCC_COEF + k] = c * lifter[k];
        }
    }
}
