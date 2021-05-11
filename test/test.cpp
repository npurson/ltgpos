#include <stdio.h>
#include <time.h>

#include "../src/ltgpos.h"


int main(int argc, char** argv)
{
    char buf[8192];
    char* filename = argv[1];
    FILE* fp = fopen(filename, "r");

    if (!fp) {
        fprintf(stderr, "%s(%d): failed to open file %s.\n",
                __FILE__, __LINE__, filename);
        return 1;
    }

    clock_t start = clock();
    int i = 0;
    while (!feof(fp)) {
        if (!fgets(buf, sizeof(buf), fp)) break;
        ltgpos(buf);
        i++;
    }
    clock_t end = clock();

    freeSysInfo();
    fclose(fp);

    fprintf(stderr, "total time: %lf s\n", (double)(end-start) / CLOCKS_PER_SEC);
    fprintf(stderr, "avg time: %lf s\n", (double)(end-start) / i / CLOCKS_PER_SEC);
    return 0;
}
