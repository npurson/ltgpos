#include "waveclf.h"


WaveClf::WaveClf(const std::string& model)
{
    CreateSessionInfo(model);

    Py_Initialize();
    if (!Py_IsInitialized()) {
        std::cerr << __FILE__ << __LINE__ << ": " << "failed to init python env.\n";
    }
    PyRun_SimpleString("import sys");
    PyRun_SimpleString("sys.path.append('./')");

    PyObject* PyModule = PyImport_ImportModule("wavetf");
    if (!PyModule) {
        std::cerr << __FILE__ << __LINE__ << ": " << "failed to import python module.\n";
    }
    this->PyFunc_wavetf = PyObject_GetAttrString(PyModule, "wavetf");

    PyObject* PyFunc_buildtf = PyObject_GetAttrString(PyModule, "build_tf");
    this->tf = PyObject_CallObject(PyFunc_buildtf, NULL);
}


int WaveClf::predict(int freq, std::vector<double> data)
{
    PyObject* PyArgs = PyTuple_New(3);
    PyObject* PyInput = PyTuple_New(data.size());
    for (int i = 0; i < data.size(); i++) {
        PyTuple_SetItem(PyInput, i, PyFloat_FromDouble(data[i]));
    }
    PyTuple_SetItem(PyArgs, 0, PyLong_FromLong(freq));
    PyTuple_SetItem(PyArgs, 1, PyInput);
    PyTuple_SetItem(PyArgs, 2, this->tf);

    PyObject* PyRet = PyObject_CallObject(this->PyFunc_wavetf, PyArgs);
    if (!PyRet) {
        std::cerr << __FILE__ << __LINE__ << ": " << "PyRet is NULL.\n";
        return -1;
    }

    std::vector<float> input;
    for (int i = 0; i < PyList_Size(PyRet); i++) {
        input.push_back((float)PyFloat_AsDouble(PyList_GetItem(PyRet, i)));
    }
    return RunSession(input);
}


WaveClf::~WaveClf() {
    DeleteSession();
    Py_Finalize();
}
