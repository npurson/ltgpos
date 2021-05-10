#include "json_parser.h"

const char* kJsonKeys[5] = { "time", "latitude", "longitude", "altitude", "goodness" };

#define cJSON_GetObjectItem_s(jitem, jobj, key) { \
    (jitem) = cJSON_GetObjectItem((jobj), (key)); \
    if (!(jitem)) { \
        fprintf(stderr, "%s(%d): missing json key \"%s\".\n", \
                __FILE__, __LINE__, key); \
        return NULL; \
    } \
}


cJSON* parseJsonStr(const char* jstr, schdata_t* schdata)
{
    cJSON* jarr = cJSON_Parse(jstr);
    cJSON* jobj = NULL;
    cJSON* jitem = NULL;

    double* ssr_locs = schdata->ssr_locs;
    double* ssr_times = schdata->ssr_times;
    double ms0;

    int num_ssrs = cJSON_GetArraySize(jarr);

    if (num_ssrs < 3) {
        fprintf(stderr, "%s(%d): ltgpos expects number of input sensors >= 3, but got %d.\n",
                __FILE__, __LINE__, num_ssrs);
        return NULL;
    }
    if (num_ssrs > kMaxNumSsrs) {
        fprintf(stderr, "warning: ltgpos expects number of input sensors <= %d, but got %d. ignoring exceeding part.\n",
                kMaxNumSsrs, num_ssrs);
        num_ssrs = 64;
    }

    for (int i = 0; i < num_ssrs; i++) {
        jobj = cJSON_GetArrayItem(jarr, i);
        for (int j = 0; j < 2; j++) {
            cJSON_GetObjectItem_s(jitem, jobj, kJsonKeys[j + 1]);
            ssr_locs[i * 2 + j] = jitem->valuedouble;
        }
        cJSON_GetObjectItem_s(jitem, jobj, "microsecond");
        if (i == 0) ms0 = (double)jitem->valueint / 1e4;
        ssr_times[i] = (double)jitem->valueint / 1e4 - ms0;
        // Assert the diff of seconds < 1 s.
        if (ssr_times[i] < 0) ssr_times[i] += 1e3;
    }
    // schdata->involved = (mask << num_ssrs) - 1;
    schdata->involved = filter_outliers(ssr_locs, num_ssrs);
    schdata->num_ssrs = num_ssrs;
    gen_sch_dom(ssr_locs, num_ssrs, schdata->involved, schdata->sch_dom);
    return jarr;
}


char* formatRetJsonStr(schdata_t* schdata, cJSON* jarr)
{
    int num_ssrs = schdata->num_ssrs;
    long involved = schdata->involved;
    double* ssr_locs = schdata->ssr_locs;
    double* ssr_times = schdata->ssr_times;
    double* out_ans = schdata->out_ans;

    cJSON* jobj = cJSON_GetArrayItem(jarr, get_first_involved(involved));
    cJSON* jitem;
    cJSON_GetObjectItem_s(jitem, jobj, "datetime");
    char* datetime = jitem->valuestring;
    cJSON_GetObjectItem_s(jitem, jobj, "microsecond");
    double ms0 = (double)jitem->valueint / 1e4;

    // Don't change the order of the following statements!
    double all_dist[kMaxNumSsrs], all_dtime[kMaxNumSsrs];
    for (int i = 0; i < num_ssrs; i++) {
        all_dist[i] = getGeoDistance2d_H(ssr_locs[i * 2], ssr_locs[i * 2 + 1], out_ans[1], out_ans[2]);
        all_dtime[i] = ssr_times[i] - out_ans[0];
    }
    if ((out_ans[0] += ms0) < 0) {
        out_ans[0] += 1e3;
        getPrevDatetime(datetime, 1);
    }

    // ################################################################
    //                  Calculate altitude & current                  #
    // ################################################################
    int num_involved = 0, is_involved[kMaxNumSsrs] = { 0 }, num_cal_alt = 0, num_cal_cur = 0;
    double us[kMaxNumSsrs], itdfs[kMaxNumSsrs], current = 0;
    char* nodes[kMaxNumSsrs];
    out_ans[3] = 0;

    // Don't change the order of the following statements!
    for (int i = 0; i < num_ssrs; i++) {
        if (!(involved & mask << i)) continue;
        jobj = cJSON_GetArrayItem(jarr, i);
        is_involved[i] = 1;
        cJSON_GetObjectItem_s(jitem, jobj, "node");
        nodes[num_involved] = jitem->valuestring;
        cJSON_GetObjectItem_s(jitem, jobj, "signal_strength");
        us[num_involved] = jitem->valuedouble;
        itdfs[num_involved] = itdf(all_dist[i], us[num_involved]);

        if (30 <= all_dist[i] && all_dist[i] <= 150) {
            current += itdfs[num_involved];
            ++num_cal_cur;
        }
        ++num_involved;

        if (!i) continue;
        // Skip 0 because 0 is the reference sensor and thus the result would be 0,
        // which may cause problems if 0 is no longer the reference sensor later.
        if (all_dist[i] <= 150) {
            double h_sqr = pow(C * all_dtime[i], 2) - pow(all_dist[i], 2);
            if (h_sqr < 0) continue;
            out_ans[3] += sqrt(h_sqr);
            ++num_cal_alt;
        }
    }
    if (num_cal_alt) out_ans[3] /= num_cal_alt;
    if (out_ans[3] > 20) out_ans[3] = 20;

    if (num_cal_cur > 1) {
        current /= num_cal_cur;
    } else if (all_dist[1] > 150) {
        current = (itdfs[0] + itdfs[1]) / 2;
    } else if (all_dist[num_involved - 2] < 30) {
        current = (itdfs[num_involved - 1] + itdfs[num_involved - 2]) / 2;
    }
    // ################################################################
    //                              End                               #
    // ################################################################

    jobj = cJSON_CreateObject();
    cJSON_AddItemToObject(jobj, "datetime", cJSON_CreateString(datetime));
    for (int i = 0; i < 5; ++i) {
        cJSON_AddItemToObject(jobj, kJsonKeys[i], cJSON_CreateNumber(out_ans[i]));
    }
    cJSON_AddItemToObject(jobj, "current", cJSON_CreateNumber(current));
    cJSON_AddItemToObject(jobj, "raw", jarr);
    cJSON_AddItemToObject(jobj, "allDist", cJSON_CreateDoubleArray(all_dist, num_ssrs));
    cJSON_AddItemToObject(jobj, "allDtime", cJSON_CreateDoubleArray(all_dtime, num_ssrs));
    cJSON_AddItemToObject(jobj, "isInvolved", cJSON_CreateIntArray(is_involved, num_ssrs));
    cJSON_AddItemToObject(jobj, "involvedNodes", cJSON_CreateStringArray((const char**)nodes, num_involved));
    cJSON_AddItemToObject(jobj, "referNode", cJSON_CreateString(nodes[0]));
    cJSON_AddItemToObject(jobj, "involvedSigStrength", cJSON_CreateDoubleArray(us, num_involved));
    cJSON_AddItemToObject(jobj, "involvedCurrent", cJSON_CreateDoubleArray(itdfs, num_involved));

    char* ret_str = cJSON_PrintUnformatted(jobj);
    cJSON_Delete(jobj);
    #ifdef TEST
    printf("%.6lf, %.6lf, %.4lf, %.4lf, %.4lf\n", out_ans[1], out_ans[2], out_ans[3], out_ans[4], current);
    // printf("%.6lf; %.6lf; %.4lf; %.4lf; %.4lf; %s\n", out_ans[1], out_ans[2], out_ans[3], out_ans[4], current, ret_str);
    #endif
    return ret_str;
}
