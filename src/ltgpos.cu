#include "ltgpos.h"


ssrinfo_t gSsrInfos[kNumSchs];
grdinfo_t gGrdInfos[kNumSchs];
bool isInit = false;


int initSysInfo()
{
    if (malloc_s(&gGrdInfos[0].houts, gMaxGridSize)) return 1;
    gGrdInfos[1].houts = gGrdInfos[0].houts;
    if (cudaMalloc_s(&gGrdInfos[0].douts, gMaxGridSize)) return 1;
    gGrdInfos[1].douts = gGrdInfos[0].douts;

    if (cudaMalloc_s(&gSsrInfos[0].ssr_locs, kMaxNumSsrs * 3)) return 1;
    gSsrInfos[1].ssr_locs = gSsrInfos[0].ssr_locs;
    if (cudaMalloc_s(&gSsrInfos[0].ssr_times, kMaxNumSsrs)) return 1;
    gSsrInfos[1].ssr_times = gSsrInfos[0].ssr_times;

    isInit = true;
    return 0;
}


void freeSysInfo()
{
    free(gGrdInfos[0].houts);
    cudaFree(gGrdInfos[0].douts);
    cudaFree(gSsrInfos[0].ssr_locs);
    cudaFree(gSsrInfos[0].ssr_times);
    isInit = false;
}


// int set_cfg(int num_sensors, int grid_size)
// {
//     gMaxGridSize <= kMaxNumThreads ? (gMaxGridSize = grid_size) :
//     fprintf(stderr, "%s(%d): grid size > the upper limit of concurrent threads.\n",
//             __FILE__, __LINE__);
//     freeSysInfo();
//     return initSysInfo();
// }


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

    grid_search(gSsrInfos, gGrdInfos, &schdata);

    #ifdef TEST
    F* out_ans = schdata.out_ans;
    F* sch_dom = schdata.sch_dom;
    printf("%7.4lf  %8.4lf  %.4lf\n", out_ans[1], out_ans[2], out_ans[4]);
    printf("%7.4lf  %7.4lf  %8.4lf %8.4lf\n", sch_dom[0], sch_dom[1], sch_dom[2], sch_dom[3]);
    // printf("%d\n", schdata.num_ssrs);

    // F* ssr_locs = schdata.ssr_locs;
    // for (int i = 0; i < schdata.num_ssrs; i++) printf("%.4lf, %.4lf\n", ssr_locs[i * 2], ssr_locs[i * 2 + 1]);
    printf("\n");
    #endif

    // Ensure the string returned is deallocated after use.
    return formatRetJsonStr(&schdata, jarr);
}
