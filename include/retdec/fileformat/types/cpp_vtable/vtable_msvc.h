/**
 * @file include/retdec/fileformat/types/cpp_vtable/vtable_gcc.h
 * @brief MSVC C++ virtual table structures.
 * @copyright (c) 2017 Avast Software, licensed under the MIT license
 */

#ifndef RETDEC_FILEFORMAT_TYPES_CPP_VTABLE_VTABLE_MSVC_H
#define RETDEC_FILEFORMAT_TYPES_CPP_VTABLE_VTABLE_MSVC_H

#include <cstdint>
#include <map>
#include <vector>

#include "retdec/fileformat/types/cpp_rtti/rtti_msvc.h"
#include "retdec/fileformat/types/cpp_vtable/vtable.h"
#include "retdec/utils/address.h"

namespace retdec {
namespace fileformat {

/**
 * MSVC virtual table sturcture ( [] means array of entries ):
 *
 *   complete object locator address
 *   [virtual function pointers] <- vtable address in instances points here
 *
 */
class VtableMsvc : public Vtable
{
	public:
		VtableMsvc(retdec::utils::Address a) : Vtable(a) {}

	public:
		retdec::utils::Address objLocatorAddress;
		// Vtable::virtualFncAddresses

		RTTICompleteObjectLocator* rtti = nullptr;
};

using CppVtablesMsvc = std::map<retdec::utils::Address, VtableMsvc>;

} // namespace fileformat
} // namespace retdec

#endif
