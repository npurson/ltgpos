#include "utils.h"


void getPrevDatetime(char* datetime, unsigned int secs)
{
    char* token;
    struct tm timeinfo, * ptimeinfo;
    time_t timer;

    token = strtok(datetime, "-");
    timeinfo.tm_year = atoi(token) - 1900;
    token = strtok(NULL, "-");
    timeinfo.tm_mon = atoi(token) - 1;
    token = strtok(NULL, " ");
    timeinfo.tm_mday = atoi(token);

    token = strtok(NULL, ":");
    timeinfo.tm_hour = atoi(token);
    token = strtok(NULL, ":");
    timeinfo.tm_min = atoi(token);
    token = strtok(NULL, " ");
    timeinfo.tm_sec = atoi(token);

    timer = mktime(&timeinfo) - secs;       // Convert tm to time_t as local time.
    ptimeinfo = localtime(&timer);          // Convert time_t to tm as local time.
    strftime(datetime, 20, "%Y-%m-%d %H:%M:%S", ptimeinfo);
    return;
}


inline void gen_ssr_dom(double* ssr_locs, int num_ssrs, long involved, double* ssr_dom) {
    for (int i = 0; i < num_ssrs; i++) {
        if (!(involved & mask << i)) continue;
        for (int j = 0; j < 2; j++) {
            if (i == get_first_involved(involved)) {
                ssr_dom[j * 2 + 1] = ssr_dom[j * 2] = ssr_locs[j];
            } else if (ssr_locs[i * 2 + j] > ssr_dom[j * 2 + 1]) {
                ssr_dom[j * 2 + 1] = ssr_locs[i * 2 + j];
            } else if (ssr_locs[i * 2 + j] < ssr_dom[j * 2]) {
                ssr_dom[j * 2] = ssr_locs[i * 2 + j];
            }
        }
    }
    return;
}


void gen_sch_dom(double* ssr_locs, int num_ssrs, long involved, double* sch_dom)
{
    double ssr_dom[4];
    gen_ssr_dom(ssr_locs, num_ssrs, involved, ssr_dom);
    double area = (ssr_dom[1] - ssr_dom[0]) * (ssr_dom[3] - ssr_dom[2]);
    double exp_ratio = kSchDomGenRatio * (area > 8 ? 1 : sqrt(8 / area));
    for (int i = 0; i < 4; i++) {
        sch_dom[i] = (exp_ratio / 2 + 0.5) * ssr_dom[i] -
                     (exp_ratio / 2 - 0.5) * ssr_dom[i % 2 ? i - 1 : i + 1];
    }
    return;
}


inline double avg(double* arr, int len, int d) {
    double sum = 0;
    for (int i = 0; i < len; i++) sum += arr[i * 2 + d];
    return sum / len;
}


inline double var(double* arr, int len, int d, double e) {
    double dev = 0;
    for (int i = 0; i < len; i++) dev += (arr[i * 2 + d] - e) * (arr[i * 2 + d] - e);
    return dev / len;
}


long filter_outliers(double* ssr_locs, int num_ssrs)
{
    long involved = (mask << num_ssrs) - 1;
    double ssr_dom[4];
    gen_ssr_dom(ssr_locs, num_ssrs, involved, ssr_dom);
    double s = (ssr_dom[3] - ssr_dom[2]) * (ssr_dom[1] - ssr_dom[0]);
    double e0 = avg(ssr_locs, num_ssrs, 0);
    double e1 = avg(ssr_locs, num_ssrs, 1);
    double d0 = var(ssr_locs, num_ssrs, 0, e0);
    double d1 = var(ssr_locs, num_ssrs, 1, e1);

    int num_involved = num_ssrs;
    double max_d = 0;
    int max_idx = 0;
    if (num_ssrs > 3 && (s > 150 + 2.5 * num_ssrs || d0 + d1 > 20 + 0.5 * num_ssrs)) {
        for (int i = 0; i < num_ssrs; i++) {
            double d = abs(ssr_locs[i * 2] - e0) / d0 + abs(ssr_locs[i * 2 + 1] - e1) / d1;
            if (d > max_d) {
                max_d = d;
                max_idx = i;
            }
            if (d > 0.5 + 0.05 * num_ssrs) {
                involved ^= mask << i;
                --num_involved;
            }
        }
        if (num_involved < 3) {
            involved = (mask << num_ssrs) - 1;
            involved ^= mask << max_idx;
        }
    }
    return involved;
}


// int dump_grdres(double* outs, int* grd_size, const char* filename)
// {
//     FILE* fp = fopen(filename, "w");
//     for (int i = 0; i < grd_size[1]; i++) {
//         for (int j = 0; j < grd_size[0]; k++) {
//             fprintf(fp, "%8.2f ", outs[i * grd_size[1] + j]);
//         }
//         fprintf(fp, "\n");
//     }
//     fclose(fp);
//     printf("[Dump] outputs dumped to %s\n", filename);
//     return 0;
// }
