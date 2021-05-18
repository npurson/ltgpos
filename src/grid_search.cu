#include "grid_search.h"


__global__ void calGirdGoodness2d_G(ssrinfo_t sinfo, grdinfo_t ginfo)
{
    int num_ssrs = sinfo.num_ssrs;
    long involved = sinfo.involved;
    double* ssr_locs = sinfo.ssr_locs;
    double* ssr_times = sinfo.ssr_times;

    double x = ginfo.sch_dom[0] + ginfo.grd_inv[0] * threadIdx.x;
    double y = ginfo.sch_dom[2] + ginfo.grd_inv[1] * blockIdx.x;
    double dt[kMaxNumSsrs];
    double t0 = 0, err = 0;

    int num_involved = 0;
    for (int i = 0; i < num_ssrs; i++) {
        if (!(involved & mask << i)) continue;
        ++num_involved;
        dt[i] = getGeoDistance2d_D(ssr_locs[i * 2], ssr_locs[i * 2 + 1], x, y) / C;
        // Is referrence sensor
        // if (involved & -involved & mask << i) { t0 = dt[i]; continue; }
        t0 += dt[i] - ssr_times[i];
    }
    t0 /= num_involved;

    for (int i = 0; i < num_ssrs; i++) {
        if (!(involved & mask << i)) continue;
        dt[i] -= t0 + ssr_times[i];
        err += dt[i] * dt[i] * 1e6;
    }
    err /= num_involved - 1;
    ginfo.douts[blockIdx.x * blockDim.x + threadIdx.x] = err;
}


void grid_search(ssrinfo_t* ssrinfo, grdinfo_t* grdinfo, schdata_t* schdata)
{
    if (get_num_involved(schdata->involved) < 3) {
        // fprintf(stderr, "%s(%d): grid search expects number of involved sensors >= 3, but got %d.\n",
        //         __FILE__, __LINE__, get_num_involved(schdata->involved));
        schdata->out_ans[4] = INFINITY;
        return;
    }
    ssrinfo->num_ssrs = schdata->num_ssrs;
    ssrinfo->involved = schdata->involved;
    double* ssr_locs = schdata->ssr_locs;
    double* ssr_times = schdata->ssr_times;
    int num_ssrs = ssrinfo->num_ssrs;
    cudaMemcpy(ssrinfo->ssr_locs, ssr_locs, num_ssrs * 2 * sizeof(double), cudaMemcpyHostToDevice);
    cudaMemcpy(ssrinfo->ssr_times, ssr_times, num_ssrs * sizeof(double), cudaMemcpyHostToDevice);

    double* out_ans = schdata->out_ans;
    double* sch_dom = grdinfo->sch_dom;
    double* grd_inv = grdinfo->grd_inv;
    double* houts   = grdinfo->houts;
    double min_err;
    int min_idx = 0;

    for (int i = 0; i < kNumSchs; i++) {
        if (!i) {
            // memcpy(sch_dom, schdata->sch_dom, 4 * sizeof(double));
            gen_sch_dom(ssr_locs, num_ssrs, schdata->involved, sch_dom);
        } else {
            // Generate search domain based on result of previous search.
            for (int j = 0; j < 4; j++) {
                sch_dom[j] = out_ans[j / 2 + 1] + grd_inv[j / 2] * kNumNxtSchInvs * ((j % 2) ? 1 : -1);
            }
        }
        for (int j = 0; j < 2; j++) {
            grd_inv[j] = (sch_dom[j * 2 + 1] - sch_dom[j * 2]) / (kMaxGrdSize - 1);
        }

        dim3 grid(kMaxGrdSize), block(kMaxGrdSize);
        calGirdGoodness2d_G <<<grid, block>>> (*ssrinfo, *grdinfo);
        cudaError_t err = cudaGetLastError();
        if (err != cudaSuccess) {
            fprintf(stderr, "%s(%d): %s.\n", __FILE__, __LINE__, cudaGetErrorString(err));
            out_ans[4] = INFINITY;
            return;
        }
        cudaMemcpy(houts, grdinfo->douts, kMaxGrdNum * sizeof(double), cudaMemcpyDeviceToHost);

        min_err = houts[0];
        min_idx = 0;
        for (int j = 1; j < kMaxGrdNum; j++) {
            if (houts[j] >= min_err) continue;
            min_err = houts[j];
            min_idx = j;
        }
        out_ans[1] = sch_dom[0] + min_idx % kMaxGrdSize * grd_inv[0];
        out_ans[2] = sch_dom[2] + min_idx / kMaxGrdSize % kMaxGrdSize * grd_inv[1];

        #ifdef PLT
        FILE* fp = fopen("figures/grdres.txt", "a");
        for (int j = 0; j < kMaxGrdNum; j++) {
            fprintf(fp, "%f ", houts[j]);
        }
        fprintf(fp, "%f %f %f %f %f %f\n", sch_dom[0], sch_dom[1], sch_dom[2], sch_dom[3], out_ans[1], out_ans[2]);
        fclose(fp);
        #endif
    }
    int ref_idx = get_first_involved(schdata->involved);
    out_ans[0] = ssr_times[ref_idx] - getGeoDistance2d_H(ssr_locs[ref_idx * 2], ssr_locs[ref_idx * 2 + 1], out_ans[1], out_ans[2]) / C;
    out_ans[4] = min_err;
    return;
}
