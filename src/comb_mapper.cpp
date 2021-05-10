#include "comb_mapper.h"


std::vector<long> comb_mapper(long involved)
{
    std::vector<long> combs;
    int num_involved = get_num_involved(involved);
    if (num_involved <= 3) return combs;

    if (num_involved < 6) {
        int n = 0;
        long involved_sub = 0;
        for (int i = 0; i < 64; i++) {
            if (!(involved & mask << i)) continue;
            involved_sub |= mask << i;
            ++n;
            if (n == 3) {
                combs.push_back(involved_sub);
                involved_sub = 0;
                break;
            }
        }
        n = 0;
        for (int i = 63; i != 0; i--) {
            if (!(involved & mask << i)) continue;
            involved_sub |= mask << i;
            ++n;
            if (n == 3) {
                combs.push_back(involved_sub);
                involved_sub = 0;
                break;
            }
        }
    } else if (num_involved >= 6) {
        int batch = num_involved < 18 ? (num_involved < 9 ? 2 : 3): 4;
        int num_involved_sub = (num_involved + 1) / batch;
        int n = 0;
        long involved_sub = 0;
        for (int i = 0; i < 64; i++) {
            if (!(involved & mask << i)) continue;
            involved_sub |= mask << i;
            ++n;
            if (n == num_involved_sub) {    // Push back
                combs.push_back(involved_sub);
                involved_sub = 0;
                n = 0;
                if (combs.size() == batch - 1) {
                    num_involved_sub = num_involved - num_involved_sub * (batch - 1);
                }
                else if (combs.size() == batch) break;
            }
        }
    }
    return combs;
}
