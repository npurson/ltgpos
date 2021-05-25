#pragma once

// Max number of input sensors.
static const int kMaxNumSsrs = 64;

// Number of search times.
static const int kNumSchs = 2;
// Number of extended intervals for next search.
static const int kNumNxtSchInvs = 2;

// Number of CUDA grids set for a single dimension.
static const int kMaxGrdSize = 512;
// Number of total CUDA grids set for grid search.
static const int kMaxGrdNum = kMaxGrdSize * kMaxGrdSize;

// // Max number of threads on GPU.
// static const int kMaxNumThreads = 512 * 65535;
// // Max number of concurrent threads on GTX 1080 Ti.
// static const int kMaxNumConcurThreads = 28 * 2048;

// Expansion ratio for search domain generation.
static const double kSchDomGenRatio = 1.2;
// Threshold for goodness of search results.
static const double kGoodThres = 20;
