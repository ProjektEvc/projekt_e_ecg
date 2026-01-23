#include "pantompkins.h"
#include <stdio.h>

/* ==================== CONFIGURATION ==================== */
#define FS 256                    // Sampling frequency in Hz
#define BUF_SIZE 64              // Buffer size for filtered signal storage
#define REFRACTORY_SAMPLES 90    // ~350ms at 256 Hz - Minimum time between QRS (prevents T-wave detection)
#define SEARCH_BACK_SAMPLES 50   // ~195ms - How far back to search for R-peak in filtered signal
#define MWI_WINDOW 38            // 150ms at 256 Hz - Moving window integration window

/* ==================== STATIC VARIABLES ==================== */

// Filtered signal buffer (stores recent filtered ECG for R-peak search-back)
static int filtered[BUF_SIZE];
static int filtered_idx = 0;

// Integration buffer (stores last 3 integrated values for peak detection)
static int integrated[3] = {0, 0, 0};

// Peak tracking for INTEGRATED signal (suffix 'i')
static int spki = 0;  // Running estimate of Signal Peak
static int npki = 0;  // Running estimate of Noise Peak

// Peak tracking for FILTERED signal (suffix 'f')
static int spkf = 0;  // Running estimate of Signal Peak
static int npkf = 0;  // Running estimate of Noise Peak

// Adaptive thresholds
static int thresholdi1 = 0;  // Primary threshold for integrated signal
static int thresholdi2 = 0;  // Secondary threshold (for missed beat detection)
static int thresholdf1 = 0;  // Primary threshold for filtered signal
static int thresholdf2 = 0;  // Secondary threshold (for missed beat detection)

// Sample counting
static int n_samples = 0;           // Total samples processed
static int r_n_samples = -1;        // Sample number of current R-peak
static int last_r_n_samples = -1;   // Sample number of previous R-peak

// RR interval tracking (RR = time between consecutive R-peaks)
static int rr_buffer[8] = {0};         // Stores last 8 RR intervals (all beats)
static int rr_limited_buffer[8] = {0}; // Stores last 8 "regular" RR intervals
static int rr_idx = 0;                 // Index for rr_buffer
static int rr_lim_idx = 0;             // Index for rr_limited_buffer

// RR averages and limits
static int rr_avg = 0;           // Average of all RR intervals
static int rr_avg_limited = 0;   // Average of only "regular" RR intervals
static int rr_low_limit = 0;     // Lower bound for regular beat (92% of average)
static int rr_high_limit = 0;    // Upper bound for regular beat (116% of average)
static int rr_missed_limit = 0;  // Threshold for missed beat detection (166% of average)

static int bpm = 0;  // Current heart rate in beats per minute

// Physiological RR limits (40-200 BPM for safety)
#define PHYS_MIN_RR ((60 * FS) / 200)  // 200 BPM = 77 samples
#define PHYS_MAX_RR ((60 * FS) / 40)   // 40 BPM = 384 samples

/* ==================== FUNCTION PROTOTYPES ==================== */
static void UpdateRRAverage(int rr);
static void UpdateThresholds(void);
static int IsLocalPeak(void);

/* ==================== INITIALIZATION ==================== */
void PanTompkins_Init(void) {
    int i;

    // Clear all buffers
    for (i = 0; i < BUF_SIZE; i++) filtered[i] = 0;
    for (i = 0; i < 3; i++) integrated[i] = 0;

    // Initialize RR buffers with reasonable default (72 BPM at 256 Hz)
    int default_rr = (60 * FS) / 72;  // ~213 samples for 72 BPM
    for (i = 0; i < 8; i++) {
        rr_buffer[i] = default_rr;
        rr_limited_buffer[i] = default_rr;
    }

    // Reset counters and indices
    n_samples = 0;
    r_n_samples = -1;
    last_r_n_samples = -1;
    filtered_idx = 0;
    rr_idx = 0;
    rr_lim_idx = 0;

    // Initialize peak estimators - CRITICAL FIX: Start with more realistic values
    spki = 500;   // Signal peak estimate for integrated signal
    npki = 100;   // Noise peak estimate for integrated signal
    spkf = 800;   // Signal peak estimate for filtered signal
    npkf = 200;   // Noise peak estimate for filtered signal

    // Initialize thresholds based on peak estimates
    UpdateThresholds();

    // Initialize RR parameters
    rr_avg = default_rr;
    rr_avg_limited = default_rr;

    // Set initial limits
    rr_low_limit = (default_rr * 92) / 100;
    rr_high_limit = (default_rr * 116) / 100;
    rr_missed_limit = (default_rr * 166) / 100;

    bpm = 72;
}

/* ==================== HELPER FUNCTIONS ==================== */
static int IsLocalPeak(void) {
    return (integrated[1] > integrated[0] && integrated[1] > integrated[2]);
}

/* ==================== MAIN PROCESSING ==================== */
int PanTompkins_Process(int raw_sample) {
    int sample, peaki, loc_max, loc_max_idx, idx, val, j;
    int rr;
    static int last_detection_time = 0;

    // Reset if no detection for too long (5 seconds) - more generous timeout
    if (r_n_samples > 0 && (n_samples - r_n_samples) > (FS * 5)) {
        // Reset to initial state
        PanTompkins_Init();
        last_detection_time = n_samples;
    }

    n_samples++;

    /* ==================== STEP 1: FILTERING ==================== */
    sample = LowPassFilter(raw_sample);
    sample = HighPassFilter(sample);

    // Store filtered signal for search-back
    filtered[filtered_idx] = sample;
    int current_f_idx = filtered_idx;
    filtered_idx = (filtered_idx + 1) % BUF_SIZE;

    /* ==================== STEP 2-4: DERIVATIVE, SQUARE, INTEGRATE ==================== */
    sample = Derivative(sample);
    sample = sample * sample;
    sample = MovingWindowIntegral(sample);

    /* ==================== STEP 5: UPDATE PEAK DETECTION BUFFER ==================== */
    integrated[0] = integrated[1];
    integrated[1] = integrated[2];
    integrated[2] = sample;

    /* ==================== STEP 6: PEAK DETECTION ==================== */
    if (IsLocalPeak()) {
        peaki = integrated[1];

        // REFRACTORY PERIOD CHECK
        int time_since_last = n_samples - last_detection_time;
        if (time_since_last < REFRACTORY_SAMPLES) {
            // In refractory period - update noise peak
            npki = (npki + (peaki >> 2)) >> 1;  // Faster adaptation for noise
            UpdateThresholds();
            return bpm;
        }

        // PRIMARY THRESHOLD CHECK
        if (peaki >= thresholdi1) {
            // Update signal peak
            spki = (spki + (peaki >> 1)) >> 1;  // Faster adaptation for signal

            /* --- SEARCH-BACK FOR R-PEAK --- */
            loc_max = 0;
            loc_max_idx = 0;

            // Search for maximum in filtered signal
            for (j = 0; j < SEARCH_BACK_SAMPLES; j++) {
                idx = (current_f_idx - j + BUF_SIZE) % BUF_SIZE;
                val = filtered[idx];
                if (val < 0) val = -val;

                if (val > loc_max) {
                    loc_max = val;
                    loc_max_idx = j;
                }
            }

            // FILTERED SIGNAL THRESHOLD CHECK
            if (loc_max >= thresholdf1) {
                spkf = (spkf + (loc_max >> 1)) >> 1;  // Faster adaptation

                // Record R-peak position
                last_r_n_samples = r_n_samples;
                r_n_samples = n_samples - loc_max_idx;
                last_detection_time = n_samples;

                /* --- CALCULATE RR INTERVAL --- */
                if (last_r_n_samples > 0) {
                    rr = r_n_samples - last_r_n_samples;

                    // Validate RR interval
                    if (rr >= REFRACTORY_SAMPLES && rr <= PHYS_MAX_RR) {
                        UpdateRRAverage(rr);
                    }
                }
            } else {
                // Filtered peak too low
                npkf = (npkf + (loc_max >> 2)) >> 1;
            }

        } else if (peaki >= thresholdi2) {
            // SECONDARY THRESHOLD - Check for missed beat
            if (r_n_samples > 0 && time_since_last >= rr_missed_limit) {
                // Possibly missed beat
                spki = (spki + (peaki >> 2)) >> 1;

                // Search back in filtered signal
                loc_max = 0;
                loc_max_idx = 0;

                for (j = 0; j < SEARCH_BACK_SAMPLES; j++) {
                    idx = (current_f_idx - j + BUF_SIZE) % BUF_SIZE;
                    val = filtered[idx];
                    if (val < 0) val = -val;

                    if (val > loc_max) {
                        loc_max = val;
                        loc_max_idx = j;
                    }
                }

                if (loc_max >= thresholdf2) {
                    spkf = (spkf + (loc_max >> 2)) >> 1;

                    last_r_n_samples = r_n_samples;
                    r_n_samples = n_samples - loc_max_idx;
                    last_detection_time = n_samples;

                    if (last_r_n_samples > 0) {
                        rr = r_n_samples - last_r_n_samples;
                        if (rr >= REFRACTORY_SAMPLES && rr <= PHYS_MAX_RR) {
                            UpdateRRAverage(rr);
                        }
                    }
                }
            } else {
                npki = (npki + (peaki >> 2)) >> 1;
            }
        } else {
            // Below both thresholds - noise
            npki = (npki + (peaki >> 2)) >> 1;
        }

        UpdateThresholds();
    }

    /* ==================== STEP 7: CALCULATE BPM ==================== */
    if (rr_avg_limited > 0) {
        bpm = (60 * FS) / rr_avg_limited;

        // Clamp to realistic range
        if (bpm < 40) bpm = 40;
        if (bpm > 200) bpm = 200;
    }

    return bpm;
}

/* ==================== RR INTERVAL AVERAGING ==================== */
static void UpdateRRAverage(int rr) {
    int i, sum;
    static int beat_count = 0;

    // Validate RR interval
    if (rr < PHYS_MIN_RR || rr > PHYS_MAX_RR) {
        return;  // Ignore physiologically impossible values
    }

    /* ---------- UPDATE ALL-RR AVERAGE ---------- */
    rr_buffer[rr_idx] = rr;
    rr_idx = (rr_idx + 1) % 8;

    sum = 0;
    for (i = 0; i < 8; i++) {
        sum += rr_buffer[i];
    }
    rr_avg = sum / 8;

    beat_count++;

    /* ---------- UPDATE LIMITED RR AVERAGE ---------- */
    if (beat_count <= 4) {
        // Learning phase: accept first few beats
        rr_limited_buffer[rr_lim_idx] = rr;
    } else {
        // Check if RR is within expected range of current average
        int lower_bound = (rr_avg_limited * 70) / 100;  // 70% of average
        int upper_bound = (rr_avg_limited * 130) / 100; // 130% of average

        if (rr >= lower_bound && rr <= upper_bound) {
            rr_limited_buffer[rr_lim_idx] = rr;
        } else {
            // Use average instead of outlier
            rr_limited_buffer[rr_lim_idx] = rr_avg_limited;
        }
    }

    rr_lim_idx = (rr_lim_idx + 1) % 8;

    /* ---------- RECALCULATE LIMITED AVERAGE ---------- */
    sum = 0;
    for (i = 0; i < 8; i++) {
        sum += rr_limited_buffer[i];
    }
    rr_avg_limited = sum / 8;

    /* ---------- UPDATE LIMITS ---------- */
    rr_low_limit = (rr_avg_limited * 85) / 100;    // 85% for tighter bounds
    rr_high_limit = (rr_avg_limited * 115) / 100;  // 115% for tighter bounds
    rr_missed_limit = (rr_avg_limited * 150) / 100; // 150% for missed beats
}

/* ==================== THRESHOLD UPDATING ==================== */
static void UpdateThresholds(void) {
    // Ensure noise doesn't exceed signal
    if (npki > spki) npki = spki >> 1;
    if (npkf > spkf) npkf = spkf >> 1;

    // Ensure minimum thresholds to prevent false negatives
    int min_threshold_i = 50;
    int min_threshold_f = 100;

    // Primary threshold = noise + 0.375 * (signal - noise)
    thresholdi1 = npki + ((spki - npki) * 3 / 8);
    thresholdf1 = npkf + ((spkf - npkf) * 3 / 8);

    if (thresholdi1 < min_threshold_i) thresholdi1 = min_threshold_i;
    if (thresholdf1 < min_threshold_f) thresholdf1 = min_threshold_f;

    // Secondary threshold = 0.5 * primary
    thresholdi2 = thresholdi1 >> 1;
    thresholdf2 = thresholdf1 >> 1;
}

/* ==================== VISUALIZATION FUNCTIONS ==================== */
int showGraphIntegralWindow(int ecg_data) {
    int filtered = HighPassFilter(LowPassFilter(ecg_data));
    int deriv = Derivative(filtered);
    long squared = (long)deriv * deriv;
    return MovingWindowIntegral((int)squared) / 10;
}

int showGraphSquared(int ecg_data) {
    int var = LowPassFilter(ecg_data);
    var = HighPassFilter(var);
    var = Derivative(var);
    var = var * var;
    return var / 1000;
}

int filter(int data) {
    return HighPassFilter(LowPassFilter(data));
}

/* ==================== DEBUG FUNCTIONS ==================== */
int PanTompkins_GetLastRR(void) {
    if (last_r_n_samples > 0 && r_n_samples > 0) {
        return r_n_samples - last_r_n_samples;
    }
    return 0;
}

void PanTompkins_GetDebugInfo(int *rr_avg_out, int *rr_lim_out, int *last_rr_out) {
    if (rr_avg_out) *rr_avg_out = rr_avg;
    if (rr_lim_out) *rr_lim_out = rr_avg_limited;
    if (last_rr_out) {
        if (last_r_n_samples > 0 && r_n_samples > 0) {
            *last_rr_out = r_n_samples - last_r_n_samples;
        } else {
            *last_rr_out = 0;
        }
    }
}

void PanTompkins_ResetRR(void) {
    PanTompkins_Init();
}

/* ==================== FILTER IMPLEMENTATIONS ==================== */
int LowPassFilter(int data) {
    static int y1 = 0, y2 = 0;
    static int x[13];
    static int n = 0;

    x[n] = data;

    int x0 = x[n];
    int x6 = x[(n + 13 - 6) % 13];
    int x12 = x[(n + 13 - 12) % 13];

    int y0 = (y1 << 1) - y2 + x0 - (x6 << 1) + x12;

    y2 = y1;
    y1 = y0;
    n = (n + 1) % 13;

    return y0 >> 5;
}

int HighPassFilter(int data) {
    static int y1 = 0;
    static int x[33];
    static int n = 0;

    x[n] = data;

    int x0 = x[n];
    int x16 = x[(n + 33 - 16) % 33];
    int x32 = x[(n + 33 - 32) % 33];

    int y0 = y1 + x0 - x32;
    y1 = y0;
    n = (n + 1) % 33;

    return x16 - (y0 >> 5);
}

int Derivative(int data) {
    static int x[5] = {0};

    int y = ((data << 1) + x[0] - x[2] - (x[3] << 1)) >> 3;

    x[3] = x[2];
    x[2] = x[1];
    x[1] = x[0];
    x[0] = data;

    return y;
}

int MovingWindowIntegral(int data) {
    static int x[MWI_WINDOW] = {0};
    static int i = 0;
    static long sum = 0;

    sum -= x[i];
    sum += data;
    x[i] = data;

    i = (i + 1) % MWI_WINDOW;

    return (int)(sum / MWI_WINDOW);
}
