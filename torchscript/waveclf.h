#include <iostream>
#include <string>
#include <vector>
#include <memory>

#include <Python.h>
#include <torch/script.h>


class WaveClf {
    public:
        WaveClf(const std::string& weight);
        ~WaveClf();
        int predict(int freq, std::vector<double> data);
    private:
        // torch::jit::Module module;
        PyObject* PyFunc_wavetf;
        PyObject* tf;
};
