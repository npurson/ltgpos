#include <onnxruntime_cxx_api.h>

#include "wrapper.h"


typedef struct SessionInfo {
    Ort::Session* ssn;
    Ort::SessionOptions* ssnOpt;
    Ort::Env* env;
    Ort::AllocatorWithDefaultOptions* alloc;
    Ort::MemoryInfo* memInfo;

    char* inname;
    char* outname;
    std::vector<int64_t> inshape;
} SessionInfo, * SessionInfo_p;


SessionInfo_p pSsnInfo;


void CreateSessionInfo(const std::string model) {
    std::basic_string<ORTCHAR_T> model_path(std::wstring(model.begin(), model.end()));
    pSsnInfo = new SessionInfo();
    pSsnInfo->env = new Ort::Env(ORT_LOGGING_LEVEL_WARNING, "waveclf");
    pSsnInfo->ssnOpt = new Ort::SessionOptions();
    pSsnInfo->ssn = new Ort::Session(*pSsnInfo->env, model_path.data(), *pSsnInfo->ssnOpt);
    pSsnInfo->alloc = new Ort::AllocatorWithDefaultOptions();
    pSsnInfo->memInfo = new Ort::MemoryInfo(Ort::MemoryInfo::CreateCpu(OrtArenaAllocator, OrtMemTypeDefault));
    pSsnInfo->inname = pSsnInfo->ssn->GetInputName(0, *pSsnInfo->alloc);
    pSsnInfo->outname = pSsnInfo->ssn->GetOutputName(0, *pSsnInfo->alloc);
    pSsnInfo->inshape = pSsnInfo->ssn->GetInputTypeInfo(0).GetTensorTypeAndShapeInfo().GetShape();  // 1x3x9x112x112
    return;
}


int RunSession(std::vector<float> input) {
    Ort::Value intensor = Ort::Value::CreateTensor<float>(*pSsnInfo->memInfo, input.data(), input.size(), pSsnInfo->inshape.data(), pSsnInfo->inshape.size());
    // assert(intensor.IsTensor() && intensor.GetTensorTypeAndShapeInfo().GetShape() == input_shape);
    std::vector<Ort::Value> outtensors = pSsnInfo->ssn->Run(Ort::RunOptions{ nullptr }, &pSsnInfo->inname, &intensor, 1, &pSsnInfo->outname, 1);
    // std::vector<int64_t> outshape = outtensor[0].GetTensorTypeAndShapeInfo().GetShape();
    // assert(outtensor.size() == 1 && outtensor.front().IsTensor() && outshape[0] == 1 && outshape[1] == 2);
    float* output = outtensors[0].GetTensorMutableData<float>();
    // std::cout << output[0] << " " << output[1] << std::endl;
    return output[1] > output[0] ? 1 : 0;
}


void DeleteSession(void) {
    delete pSsnInfo;
}
