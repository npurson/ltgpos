. tools/pathcfg.sh

rm libs/* test/*.so test/*.out

$NVCC --compiler-options -fPIC -DTEST -rdc=true -shared \
  src/ltgpos.cu \
  src/comb_mapper.cu \
  src/grid_search.cu \
  src/json_parser.cu \
  src/geodistance.cu \
  src/utils.cu \
  src/cJSON.c \
  -o libs/libltgpos.so

cp libs/libltgpos.so test/
export LD_LIBRARY_PATH=test:$LD_LIBRARY_PATH
g++ test/test.c -I/usr/local/cuda/include/ -Ltest -lltgpos -o test/test.out

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
	test/test.out test/data/input_$IN.csv > test/data/output_$IN.csv
else
	test/test.out test/data/input_$IN.csv
fi
