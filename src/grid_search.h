#pragma once

#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <math.h>

#include <cuda.h>
#include <cuda_runtime.h>
#include <device_launch_parameters.h>

#include "utils.h"
#include "configs.h"
#include "geodistance.h"
#include "json_parser.h"


typedef struct ssrinfo {
    int num_ssrs;
    long involved;
    F* ssr_locs;
    F* ssr_times;
} ssrinfo_t;


typedef struct grdinfo {
    F sch_dom[4];
    F grd_inv[2];
    F* houts;
    F* douts;
} grdinfo_t;


void grid_search(ssrinfo_t* sinfos, grdinfo_t* ginfos, schdata_t* schdata);
