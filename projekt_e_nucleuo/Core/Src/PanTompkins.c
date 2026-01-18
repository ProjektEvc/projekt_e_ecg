#include "pantompkins.h"

/* Static variables to maintain state between calls */
static int filtered[BUF_SIZE];
static int integrated[3];
static int filtered_idx = 0;

static int spki = 0, npki = 0, thresholdi1 = 0, thresholdi2 = 0;
static int spkf = 0, npkf = 0, thresholdf1 = 0, thresholdf2 = 0;

static int n_samples = 0;
static int last_r_n_samples = -1;
static int rr_avg_limited = 0;
static int bpm = 0;

/* Internal Filter Prototypes */
static int LowPassFilter(int data);
static int HighPassFilter(int data);
static int Derivative(int data);
static int MovingWindowIntegral(int data);

void PanTompkins_Init(void) {
    n_samples = 0;
    last_r_n_samples = -1;
    // Initial estimates for thresholds (adjust based on your ADC range)
    spki = 1000;
    thresholdi1 = 500;
}

int PanTompkins_Process(int raw_sample) {
    n_samples++;

    // 1. Filter Chain
    int sample = LowPassFilter(raw_sample);
    sample = HighPassFilter(sample);

    // Store in circular buffer for back-search
    filtered[filtered_idx] = sample;
    int current_f_idx = filtered_idx;
    filtered_idx = (filtered_idx + 1) % BUF_SIZE;

    sample = Derivative(sample);
    sample = sample * sample;
    int integrated_val = MovingWindowIntegral(sample);

    // 2. Shift integration buffer to detect peaks
    integrated[0] = integrated[1];
    integrated[1] = integrated[2];
    integrated[2] = integrated_val;

    // 3. Peak Detection (Local max)
    if (integrated[1] > integrated[0] && integrated[1] > integrated[2]) {
        int peaki = integrated[1];

        if (peaki >= thresholdi1) {
            // Signal Peak in Integration
            spki = (peaki >> 3) + (spki - (spki >> 3)); // 0.125 * p + 0.875 * sp

            // Find max in filtered signal (back-search 32 samples)
            int loc_max = 0;
            int loc_max_idx = 0;
            for (int j = 0; j < 32; j++) {
                int idx = (current_f_idx - j + BUF_SIZE) % BUF_SIZE;
                int val = (filtered[idx] < 0) ? -filtered[idx] : filtered[idx];
                if (val > loc_max) {
                    loc_max = val;
                    loc_max_idx = j;
                }
            }

            if (loc_max >= thresholdf1) {
                spkf = (loc_max >> 3) + (spkf - (spkf >> 3));

                int r_n_samples = n_samples - loc_max_idx;
                if (last_r_n_samples != -1) {
                    int rr = r_n_samples - last_r_n_samples;
                    // Update RR Average (Simplification of your RRAverage logic)
                    if (rr_avg_limited == 0) rr_avg_limited = rr;
                    else rr_avg_limited = (rr >> 3) + (rr_avg_limited - (rr_avg_limited >> 3));

                    if (rr_avg_limited > 0) {
                        bpm = (60 * FS) / rr_avg_limited;
                    }
                }
                last_r_n_samples = r_n_samples;
            }
        } else {
            // Noise Peak
            npki = (peaki >> 3) + (npki - (npki >> 3));
        }

        // Update Thresholds
        thresholdi1 = npki + ((spki - npki) >> 2); // np + 0.25*(sp-np)
        thresholdf1 = npkf + ((spkf - npkf) >> 2);
    }

    return bpm;
}

/* Filter Implementations */
static int LowPassFilter(int data) {
    static int y1 = 0, y2 = 0, x[26], n = 12;
    x[n] = x[n + 13] = data;
    int y0 = (y1 << 1) - y2 + x[n] - (x[n + 6] << 1) + x[n + 12];
    y2 = y1; y1 = y0;
    if (--n < 0) n = 12;
    return y0 >> 5;
}

static int HighPassFilter(int data) {
    static int y1 = 0, x[66], n = 32;
    x[n] = x[n + 33] = data;
    int y0 = y1 + x[n] - x[n + 32];
    y1 = y0;
    if (--n < 0) n = 32;
    return x[n + 16] - (y0 >> 5);
}

static int Derivative(int data) {
    static int x_d[4];
    int y = (data << 1) + x_d[3] - x_d[1] - (x_d[0] << 1);
    for (int i = 0; i < 3; i++) x_d[i] = x_d[i + 1];
    x_d[3] = data;
    return y >> 3;
}

static int MovingWindowIntegral(int data) {
    static int x[32], i = 0;
    static int sum = 0;
    sum -= x[i];
    sum += data;
    x[i] = data;
    if (++i == 32) i = 0;
    return sum >> 5;
}
