/**
 * @file include/retdec/bin2llvmir/utils/type.h
 * @brief LLVM type utilities.
 * @copyright (c) 2017 Avast Software, licensed under the MIT license
 */

#ifndef RETDEC_BIN2LLVMIR_UTILS_TYPE_H
#define RETDEC_BIN2LLVMIR_UTILS_TYPE_H

#include <llvm/IR/LLVMContext.h>
#include <llvm/IR/Module.h>
#include <llvm/IR/Type.h>

#include "retdec/bin2llvmir/providers/config.h"
#include "retdec/bin2llvmir/providers/fileimage.h"
#include "retdec/bin2llvmir/utils/debug.h"

namespace retdec {
namespace bin2llvmir {

llvm::Value* convertValueToType(
		llvm::Value* val,
		llvm::Type* type,
		llvm::Instruction* before);

llvm::Value* convertValueToTypeAfter(
		llvm::Value* val,
		llvm::Type* type,
		llvm::Instruction* after);

llvm::Constant* convertConstantToType(
		llvm::Constant* val,
		llvm::Type* type);

llvm::Value* changeObjectType(
		Config* config,
		FileImage* objf,
		llvm::Module* module,
		llvm::Value* val,
		llvm::Type* toType,
		llvm::Constant* init = nullptr,
		std::unordered_set<llvm::Instruction*>* instToErase = nullptr,
		bool dbg = false,
		bool wideString = false);

std::vector<llvm::Type*> parseFormatString(
		llvm::Module* module,
		const std::string& format,
		llvm::Function* calledFnc = nullptr);

} // namespace bin2llvmir
} // namespace retdec

#endif
