# ⚡️ Ltgpos

Ltgpos is a parallel lightning positioning algorithm based on grid search, with CUDA parallel computing acceleration.

## Installation

### Build libltgpos from Source

Set the paths in `tools/pathcfg.sh` and run the following:

```shell
bash tools/build.sh
```

## Usage

### Getting Started with Source

See the [documentation](docs/doc.md).

### Test & Evaluate

Test results for designated input:

```shell
bash tools/test.sh -i /path/to/input (-o)
```

Evaluate the results by **Geodesic Distance**:

```shell
python test/evaluation.py --no xxx
```

Filter the input data by geoditance and goodness:

```shell
python test/badcase.py --no xxx
```

Split the output JSON string into data frame and raw JSON string:

```shell
python test/split_output.py --no xxx
```

### Compile and Run Java Demo

```shell
bash tools/demo.sh
```

## Deployment

Included dirs: `demo/`, `src/`, `tools/`

Modify `tools/pathcfg.sh` :

```bash
JAVA_HOME=~/ltgpos/jdk1.8.0_271
LTGPOS=~/ltgpos
```

Modify `demo/LtgposCaller.java` :

```bash
System.load("/home/yftx02/ltgpos/libs/libltgpos.so");
```

Set `src/config.h/kMaxGrdSize` to 1024 for GTX 1080 Ti.

## TODO

- [ ] Traverse all combination for gt input
- [ ] Windows deployment
- [ ] RPC debug
- [ ] Tune goodness threshold for Vincenty Formula
- [ ] Analyze 0 gooness but large error result (grd_inv, sch_dom)
