#include <assert.h>
#include <iostream>
#include <sstream>
#include <vector>

#include <onnxruntime_cxx_api.h>


int main() {
    #include <algorithm>
    std::string weight = "C:\\Users\\89378\\Documents\\Tencent Files\\893786194\\FileRecv\\waveclf.onnx";
    std::vector<float> input(1 * 3 * 9 * 112 * 112);
    std::generate(input.begin(), input.end(), [&] { return rand() % 255 / 255; });

    std::basic_string<ORTCHAR_T> model_path(std::wstring(weight.begin(), weight.end()));

    // Setup onnxruntime env.
    Ort::Env env(ORT_LOGGING_LEVEL_WARNING, "waveclf");
    Ort::SessionOptions session_options;
    Ort::Session session(env, model_path.data(), session_options);
    Ort::AllocatorWithDefaultOptions allocator;

    // Get name & shape info of inputs & outputs.
    char* input_name = session.GetInputName(0, allocator);
    char* output_name = session.GetOutputName(0, allocator);
    std::vector<int64_t> input_shape = session.GetInputTypeInfo(0).GetTensorTypeAndShapeInfo().GetShape();  // 1x3x9x112x112

    // Pass data through model
    auto memory_info = Ort::MemoryInfo::CreateCpu(OrtArenaAllocator, OrtMemTypeDefault);
    Ort::Value input_tensor = Ort::Value::CreateTensor<float>(memory_info, input.data(), input.size(), input_shape.data(), input_shape.size());
    // assert(input_tensor.IsTensor() && input_tensor.GetTensorTypeAndShapeInfo().GetShape() == input_shape);
    std::vector<Ort::Value> output_tensors = session.Run(Ort::RunOptions{ nullptr }, &input_name, &input_tensor, 1, &output_name, 1);
    std::vector<int64_t> output_shape = output_tensors[0].GetTensorTypeAndShapeInfo().GetShape();
    // assert(output_tensors.size() == 1 && output_tensors.front().IsTensor() && output_shape[0] == 1 && output_shape[1] == 2);

    float* output = output_tensors[0].GetTensorMutableData<float>();
    std::cout << output[0] << " " << output[1] << "\n";
    // return output[1] > output[0] ? 1 : 0;
    return 0;
}
