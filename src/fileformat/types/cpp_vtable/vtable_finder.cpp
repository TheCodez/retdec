/**
 * @file src/fileformat/types/cpp_vtable/vtable_finder.cpp
 * @brief Find vtable structures in @c FileFormat.
 * @copyright (c) 2017 Avast Software, licensed under the MIT license
 */

#include "retdec/fileformat/file_format/file_format.h"
#include "retdec/fileformat/types/cpp_rtti/rtti_gcc_parser.h"
#include "retdec/fileformat/types/cpp_rtti/rtti_msvc_parser.h"
#include "retdec/fileformat/types/cpp_vtable/vtable_finder.h"

using namespace retdec::utils;

namespace retdec {
namespace fileformat {

void findPossibleVtables(
		const FileFormat* ff,
		std::set<retdec::utils::Address>& possibleVtables,
		bool gcc)
{
	auto wordSz = ff->getBytesPerWord();

	for (auto& sec : ff->getSections())
	{
		if (!sec->isSomeData())
		{
			continue;
		}

		auto addr = sec->getAddress();
		auto end = sec->getEndAddress();
		while (addr + wordSz < end)
		{
			std::uint64_t val = 0;
			if (!ff->getWord(addr, val))
			{
				addr += wordSz;
				continue;
			}

			if (gcc && val != 0)
			{
				addr += wordSz;
				continue;
			}

			Address item1 = addr + wordSz;
			Address item2 = item1 + wordSz;

			if (!ff->isPointer(item1)
					|| !ff->isPointer(item2))
			{
				addr += wordSz;
				continue;
			}

			possibleVtables.insert(item2);
			addr = item2;
		}
	}
}

/**
 * @return @c True if vtable ok and can be used, @c false if it should
 * be thrown away.
 */
bool fillVtable(
		const FileFormat* ff,
		std::set<retdec::utils::Address>& processedAddresses,
		Address a,
		Vtable& vt)
{
	std::set<retdec::utils::Address> items;

	auto bpw = ff->getBytesPerWord();
	std::uint64_t ptr = 0;
	auto isPtr = ff->isPointer(a, &ptr);
	while (true)
	{
		if (!isPtr)
		{
			break;
		}
		if (ff->isArm() && ptr % 2)
		{
			--ptr;
		}
		if (processedAddresses.find(a) != processedAddresses.end())
		{
			break;
		}
		auto* sec = ff->getSectionFromAddress(ptr);
		if (sec == nullptr || !sec->isSomeCode())
		{
			break;
		}

		// All items in vtable must be unique (really???).
		//
		if (items.find(ptr) != items.end())
		{
			return false;
		}

		vt.virtualFncAddresses.emplace_back(VtableItem(ptr));
		items.insert(ptr);
		processedAddresses.insert(a);

		a += bpw;
		isPtr = ff->isPointer(a, &ptr);
	}

	if (vt.virtualFncAddresses.empty())
	{
		return false;
	}

	return true;
}

void findGccVtables(FileFormat* ff, CppVtablesGcc& vtables, CppRttiGcc& rttis)
{
	std::set<retdec::utils::Address> possibleVtables;
	findPossibleVtables(ff, possibleVtables, true);

	std::set<retdec::utils::Address> processedAddresses;
	for (auto addr : possibleVtables)
	{
		VtableGcc vt(addr);

		if (!fillVtable(ff, processedAddresses, addr, vt))
		{
			continue;
		}

		auto rttiPtrAddr = addr - ff->getBytesPerWord();
		std::uint64_t rttiAddr = 0;
		if (ff->getWord(rttiPtrAddr, rttiAddr))
		{
			vt.rttiAddress = rttiAddr;
			vt.rtti = parseGccRtti(ff, rttis, vt.rttiAddress);
			if (vt.rtti == nullptr)
			{
				continue;
			}
		}
		else
		{
			continue;
		}

		vtables.emplace(addr, vt);
	}

	finalizeGccRtti(rttis);
}

void findMsvcVtables(FileFormat* ff, CppVtablesMsvc& vtables, CppRttiMsvc& rttis)
{
	std::set<retdec::utils::Address> possibleVtables;
	findPossibleVtables(ff, possibleVtables, false);

	std::set<retdec::utils::Address> processedAddresses;
	for (auto addr : possibleVtables)
	{
		VtableMsvc vt(addr);

		if (!fillVtable(ff, processedAddresses, addr, vt))
		{
			continue;
		}

		auto rttiPtrAddr = addr - ff->getBytesPerWord();
		std::uint64_t rttiAddr = 0;
		if (ff->getWord(rttiPtrAddr, rttiAddr))
		{
			vt.objLocatorAddress = rttiAddr;
			vt.rtti = parseMsvcRtti(ff, rttis, vt.objLocatorAddress);
			if (vt.rtti == nullptr)
			{
				continue;
			}
		}
		else
		{
			continue;
		}

		vtables.emplace(addr, vt);
	}
}

} // namespace fileformat
} // namespace retdec
