/**
 * @file include/retdec/bin2llvmir/utils/llvm.h
 * @brief LLVM Utility functions.
 * @copyright (c) 2017 Avast Software, licensed under the MIT license
 *
 * Useful LLVM-related things that are missing in LLVM itself.
 * All (Values, Types, Instructions, etc.) in one module.
 * Keep this as small as possible. Use LLVM when possible.
 */

#ifndef RETDEC_BIN2LLVMIR_UTILS_LLVM_H
#define RETDEC_BIN2LLVMIR_UTILS_LLVM_H

#include <llvm/IR/Value.h>

namespace retdec {
namespace bin2llvmir {
namespace llvm_utils {

//
//==============================================================================
// Values
//==============================================================================
//

llvm::Value* skipCasts(llvm::Value* val);

} // namespace llvm_utils
} // namespace bin2llvmir
} // namespace retdec

#endif
