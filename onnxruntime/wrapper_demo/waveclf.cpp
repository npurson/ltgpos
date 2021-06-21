#include <onnxruntime_cxx_api.h>

#include "waveclf.h"


typedef struct SessionInfo {
    Ort::Session* ssn;
    Ort::SessionOptions* ssnOpt;
    Ort::Env* env;
    Ort::AllocatorWithDefaultOptions* alloc;

    char* inname;
    char* outname;
    std::vector<int64_t> inshape;
} SessionInfo, * SessionInfo_p;


SessionInfo_p pSsnInfo;


SessionInfo_p CreateSessionInfo(const ORTCHAR_T* model)
{
    SessionInfo_p ssnInfo = new SessionInfo();
    ssnInfo->env = new Ort::Env(ORT_LOGGING_LEVEL_WARNING, "waveclf");
    ssnInfo->ssnOpt = new Ort::SessionOptions();
    ssnInfo->ssn = new Ort::Session(*ssnInfo->env, model, *ssnInfo->ssnOpt);
    ssnInfo->alloc = new Ort::AllocatorWithDefaultOptions();
    ssnInfo->inname = ssnInfo->ssn->GetInputName(0, *ssnInfo->alloc);
    ssnInfo->outname = ssnInfo->ssn->GetOutputName(0, *ssnInfo->alloc);
    ssnInfo->inshape = ssnInfo->ssn->GetInputTypeInfo(0).GetTensorTypeAndShapeInfo().GetShape();  // 1x3x9x112x112
    return ssnInfo;
}


int RunSession(SessionInfo_p ssnInfo, std::vector<float> input)
{
    Ort::MemoryInfo memInfo = Ort::MemoryInfo::CreateCpu(OrtArenaAllocator, OrtMemTypeDefault);
    Ort::Value intensor = Ort::Value::CreateTensor<float>(memInfo, input.data(), input.size(), ssnInfo->inshape.data(), ssnInfo->inshape.size());
    // assert(intensor.IsTensor() && intensor.GetTensorTypeAndShapeInfo().GetShape() == input_shape);
    std::vector<Ort::Value> outtensors = ssnInfo->ssn->Run(Ort::RunOptions{ nullptr }, &ssnInfo->inname, &intensor, 1, &ssnInfo->outname, 1);
    // std::vector<int64_t> outshape = outtensor[0].GetTensorTypeAndShapeInfo().GetShape();
    // assert(outtensor.size() == 1 && outtensor.front().IsTensor() && outshape[0] == 1 && outshape[1] == 2);
    float* output = outtensors[0].GetTensorMutableData<float>();
    // std::cout << output[0] << " " << output[1] << std::endl;
    return output[1] > output[0] ? 1 : 0;
}


WaveClf::WaveClf(const std::string& model)
{
    CreateSessionInfo();

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
    return RunSession(pSsnInfo, input);
}


WaveClf::~WaveClf() {
    delete pSsnInfo;
    Py_Finalize();
}
