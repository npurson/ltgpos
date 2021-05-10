#include "ltgpos.h"


ssrinfo_t gSsrInfo;
grdinfo_t gGrdInfo;
bool isInit = false;


int initSysInfo()
{
    if (malloc_s(&gGrdInfo.houts, kMaxGrdNum)) return 1;
    if (cudaMalloc_s(&gGrdInfo.douts, kMaxGrdNum)) return 1;
    if (cudaMalloc_s(&gSsrInfo.ssr_locs, kMaxNumSsrs * 2)) return 1;
    if (cudaMalloc_s(&gSsrInfo.ssr_times, kMaxNumSsrs)) return 1;
    isInit = true;
    return 0;
}


void freeSysInfo()
{
    free(gGrdInfo.houts);
    cudaFree(gGrdInfo.douts);
    cudaFree(gSsrInfo.ssr_locs);
    cudaFree(gSsrInfo.ssr_times);
    isInit = false;
}


// Divide & conquer.
long dac_search(schdata_t& d)
{
    long involved = 0, prev_involved;
    // printf("beg: %lx\n", d.involved);
    std::vector<long> combs = comb_mapper(d.involved);
    for (int i = 0; i != combs.size(); i++) {
        // printf("sub: %lx\n", combs[i]);
        d.involved = combs[i];
        grid_search(&gSsrInfo, &gGrdInfo, &d);
        // double* out_ans = d.out_ans;
        // printf("%7.4lf  %8.4lf  %.4lf\n", out_ans[1], out_ans[2], out_ans[4]);
        prev_involved = involved;
        involved |= d.out_ans[4] > kGoodThres ? dac_search(d) : combs[i];
        d.involved = involved;
        grid_search(&gSsrInfo, &gGrdInfo, &d);
        if (d.out_ans[4] > kGoodThres) involved = prev_involved;
    }
    // printf("fin: %lx\n", involved);
    return involved;
}


char* ltgpos(char* str)
{
    if (!isInit && initSysInfo()) {
        fprintf(stderr, "%s(%d): failed to initialize sysinfo.\n", __FILE__, __LINE__);
        return NULL;
    }

    schdata_t schdata;
    // Ensure jarr is deleted before return.
    cJSON* jarr = parseJsonStr(str, &schdata);
    if (!jarr) return NULL;

    grid_search(&gSsrInfo, &gGrdInfo, &schdata);
    if (schdata.out_ans[4] >= kGoodThres) {
        long prev_involved = schdata.involved;
        long involved = dac_search(schdata);
        schdata.involved = involved ? involved : prev_involved;
        grid_search(&gSsrInfo, &gGrdInfo, &schdata);
    }

    // Ensure the string returned is deallocated after use.
    return formatRetJsonStr(&schdata, jarr);
}
