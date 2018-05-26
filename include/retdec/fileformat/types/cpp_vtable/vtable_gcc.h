/**
 * @file include/retdec/fileformat/types/cpp_vtable/vtable_gcc.h
 * @brief GCC C++ virtual table structures.
 * @copyright (c) 2017 Avast Software, licensed under the MIT license
 */

#ifndef RETDEC_FILEFORMAT_TYPES_CPP_VTABLE_VTABLE_GCC_H
#define RETDEC_FILEFORMAT_TYPES_CPP_VTABLE_VTABLE_GCC_H

#include <cstdint>
#include <map>
#include <vector>

#include "retdec/fileformat/types/cpp_rtti/rtti_gcc.h"
#include "retdec/fileformat/types/cpp_vtable/vtable.h"
#include "retdec/utils/address.h"

namespace retdec {
namespace fileformat {

/**
 * gcc&clang virtual table sturcture ( [] means array of entries ):
 *
 *   [virtual call (vcall) offsets]
 *   [virtual base (vbase) offsets]
 *   offset to top
 *   typeinfo (RTTI) pointer
 *   [virtual function pointers] <- vtable address in instances points here
 *
 */
class VtableGcc : public Vtable
{
	public:
		VtableGcc(retdec::utils::Address a) : Vtable(a) {}

	public:
		std::vector<int> vcallOffsets; ///< TODO: not set/used right now
		std::vector<int> vbaseOffsets; ///< TODO: not set/used right now
		int topOffset = 0;             ///< TODO: not set/used right now
		retdec::utils::Address rttiAddress;
		// Vtable::virtualFncAddresses

		std::shared_ptr<ClassTypeInfo> rtti;
};

using CppVtablesGcc = std::map<retdec::utils::Address, VtableGcc>;

} // namespace fileformat
} // namespace retdec

#endif
