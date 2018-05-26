/**
 * @file include/retdec/fileformat/types/cpp_rtti/rtti_gcc_parser.h
 * @brief Parse C++ GCC/Clang RTTI structures.
 * @copyright (c) 2017 Avast Software, licensed under the MIT license
 */

#ifndef RETDEC_FILEFORMAT_TYPES_CPP_RTTI_RTTI_GCC_PARSER_H
#define RETDEC_FILEFORMAT_TYPES_CPP_RTTI_RTTI_GCC_PARSER_H

#include "retdec/fileformat/types/cpp_rtti/rtti_gcc.h"
#include "retdec/utils/address.h"

namespace retdec {
namespace fileformat {

class FileFormat;

std::shared_ptr<ClassTypeInfo> parseGccRtti(
		FileFormat* ff,
		CppRttiGcc& rttis,
		retdec::utils::Address rttiAddr);

void finalizeGccRtti(CppRttiGcc& rttis);

} // namespace fileformat
} // namespace retdec

#endif
