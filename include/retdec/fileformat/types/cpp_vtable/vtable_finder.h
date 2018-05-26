/**
 * @file include/retdec/fileformat/types/cpp_vtable/vtable_finder.h
 * @brief Find vtable structures in @c FileFormat.
 * @copyright (c) 2017 Avast Software, licensed under the MIT license
 */

#ifndef RETDEC_FILEFORMAT_TYPES_CPP_VTABLE_VTABLE_FINDER_H
#define RETDEC_FILEFORMAT_TYPES_CPP_VTABLE_VTABLE_FINDER_H

#include <cstdint>
#include <vector>

#include "retdec/fileformat/types/cpp_rtti/rtti_gcc.h"
#include "retdec/fileformat/types/cpp_rtti/rtti_msvc.h"
#include "retdec/fileformat/types/cpp_vtable/vtable_gcc.h"
#include "retdec/fileformat/types/cpp_vtable/vtable_msvc.h"
#include "retdec/utils/address.h"

namespace retdec {
namespace fileformat {

class FileFormat;

void findGccVtables(FileFormat* ff, CppVtablesGcc& vtables, CppRttiGcc& rttis);
void findMsvcVtables(FileFormat* ff, CppVtablesMsvc& vtables, CppRttiMsvc& rttis);

} // namespace fileformat
} // namespace retdec

#endif
