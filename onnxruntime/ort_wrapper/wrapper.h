#pragma once
#include <string>
#include <vector>


void CreateSessionInfo(const std::string model);

int RunSession(std::vector<float> input);

void DeleteSession(void);
