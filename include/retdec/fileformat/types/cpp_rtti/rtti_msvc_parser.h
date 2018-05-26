/**
 * @file include/retdec/fileformat/types/cpp_rtti/rtti_msvc_parser.h
 * @brief Parse C++ MSVC RTTI structures.
 * @copyright (c) 2017 Avast Software, licensed under the MIT license
 */

#ifndef RETDEC_FILEFORMAT_TYPES_CPP_RTTI_RTTI_MSVC_PARSER_H
#define RETDEC_FILEFORMAT_TYPES_CPP_RTTI_RTTI_MSVC_PARSER_H

#include "retdec/fileformat/types/cpp_rtti/rtti_msvc.h"
#include "retdec/utils/address.h"

namespace retdec {
namespace fileformat {

class FileFormat;

RTTICompleteObjectLocator* parseMsvcRtti(
		FileFormat* ff,
		CppRttiMsvc& rttis,
		retdec::utils::Address rttiAddr);

} // namespace fileformat
} // namespace retdec

#endif
