. tools/pathcfg.sh
rm libs/* bin/test.out

$NVCC --compiler-options -fPIC -DTEST -DPLT -rdc=true -shared \
  src/ltgpos.cpp \
  src/json_parser.cpp \
  src/comb_mapper.cpp \
  src/grid_search.cu \
  src/geodistance.cu \
  src/utils.cpp \
  src/cJSON.c \
  -o libs/libltgpos.so

export LD_LIBRARY_PATH=libs:$LD_LIBRARY_PATH
g++ src/test.cpp -DPLT -I/usr/local/cuda/include/ -Llibs -lltgpos -o bin/test.out

while getopts "i:o" arg; do
  case $arg in
    i)
      IN=$OPTARG
      ;;
    o)
      OUT=true
      ;;
  esac
done

if [ "$OUT" = true ]; then
  bin/test.out test/data/input_$IN.csv > test/data/output_$IN.csv
else
  bin/test.out test/data/input_$IN.csv
fi
