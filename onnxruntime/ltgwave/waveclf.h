#pragma once
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

#include <Python.h>

#include <ort/wrapper.h>


class WaveClf {
    public:
        WaveClf(const std::string& weight);
        ~WaveClf();
        int predict(int freq, std::vector<double> data);
    private:
        PyObject* PyFunc_wavetf;
        PyObject* tf;
};
