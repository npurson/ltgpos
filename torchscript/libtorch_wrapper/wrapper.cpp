#include <torch/script.h>

#include "wrapper.h"


torch::jit::Module gModule;


int initModule(std::string path) {
    try {
        gModule = torch::jit::load(path);
        return 0;
    }
    catch (const c10::Error& e) {
        std::cerr << __FILE__ << __LINE__ << ": " << "error loading the model.\n";
        return 1;
    }
}


int forwardModule(std::vector<double> input) {
    std::vector<torch::jit::IValue> inputs;
    inputs.push_back(torch::tensor(input).view({ 1, 3, 9, 112, 112 }));
    at::Tensor outputs = gModule.forward(inputs).toTensor();
    int output = std::get<1>(torch::max(outputs, 1)).item().toInt();
    return output;
}
