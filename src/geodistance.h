#pragma once

#include <math.h>
#include <cuda.h>
#include <cuda_runtime.h>

#define C   299.792458
#define PI  3.14159265358979323846
#define RA  6378.137
#define RB  6356.752314245
#define F   (1 / 298.257223563)
#define rad(deg) (deg * PI / 180.0)
#define pow2(x) ((x) * (x))


double getGeoDistance2d_H(double lat1, double lon1, double lat2, double lon2);

__device__ double getGeoDistance2d_D(double lat1, double lon1, double lat2, double lon2);
