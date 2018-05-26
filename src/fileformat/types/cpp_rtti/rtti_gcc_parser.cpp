/**
 * @file src/fileformat/types/cpp_rtti/rtti_gcc_parser.cpp
 * @brief Parse C++ GCC/Clang RTTI structures.
 * @copyright (c) 2017 Avast Software, licensed under the MIT license
 */

#include <iostream>

#include "retdec/fileformat/file_format/file_format.h"
#include "retdec/fileformat/types/cpp_rtti/rtti_gcc_parser.h"
#include "retdec/utils/string.h"

#define LOG \
	if (!debug_enabled) {} \
	else std::cout << std::showbase
const bool debug_enabled = false;

using namespace retdec::utils;

namespace retdec {
namespace fileformat {

/**
 * Pointer to RTTI entry if parsed ok, @c nullptr otherwise.
 */
std::shared_ptr<ClassTypeInfo> parseGccRtti(
		FileFormat* ff,
		CppRttiGcc& rttis,
		retdec::utils::Address rttiAddr)
{
	auto findRtti = rttis.find(rttiAddr);
	if (findRtti != rttis.end())
	{
		LOG << "\t[OK] already parsed" << std::endl << std::endl;
		return findRtti->second;
	}

	size_t wordSize = ff->getBytesPerWord();

	Address addr = rttiAddr;
	std::uint64_t vptrAddr = 0;
	if (!ff->getWord(addr, vptrAddr))
	{
		LOG << "\t[FAILED] vptrAddr @ " << addr <<  std::endl << std::endl;
		return nullptr;
	}
	if (vptrAddr != 0 && !ff->getSegmentFromAddress(vptrAddr))
	{
		LOG << "\t[FAILED] vptrAddr not valid = " << vptrAddr
			<<  std::endl << std::endl;
		return nullptr;
	}
	LOG << "\t\tvptr = " << vptrAddr << "\n";
	addr += wordSize;

	std::uint64_t nameAddr = 0;
	if (!ff->getWord(addr, nameAddr))
	{
		LOG << "\t[FAILED] nameAddr @ " << addr <<  std::endl << std::endl;
		return nullptr;
	}
	LOG << "\t\tname = " << nameAddr << "\n";
	std::string name;
	if (!ff->getNTBS(nameAddr, name))
	{
		LOG << "\t[FAILED] name @ " << nameAddr <<  std::endl << std::endl;
		return nullptr;
	}
	if (retdec::utils::hasNonprintableChars(name))
	{
		LOG << "\t[FAILED] name unprintable = " << name
			<<  std::endl << std::endl;
		return nullptr;
	}
	LOG << "\t\tname = " << name << "\n";
	addr += wordSize;

	Address baseAddr;
	Address addrOfBaseAddr = addr;
	std::uint64_t ba = 0;
	if (!ff->getWord(addrOfBaseAddr, ba))
	{
		LOG << "\t[NON-CRITICAL FAIL] baseAddr @ " << addrOfBaseAddr
			<< std::endl << std::endl;
	}
	else
	{
		baseAddr = ba;
		LOG << "\t\tbase = " << baseAddr << "\n";
	}
	Address flags;
	std::uint64_t f = 0;
	if (!ff->get4Byte(addr, f))
	{
		LOG << "\t[NON-CRITICAL FAIL] flags @ " << addr
			<< std::endl << std::endl;
	}
	else
	{
		flags = f;
		LOG << "\t\tflags= " << flags << "\n";
	}
	addr += 4;

	Address baseCount;
	std::uint64_t bc = 0;
	if (!ff->get4Byte(addr, bc))
	{
		LOG << "\t[NON-CRITICAL FAIL] baseCount @ " << addr
			<< std::endl << std::endl;
	}
	else
	{
		baseCount = bc;
		LOG << "\t\tb cnt= " << baseCount << "\n";
	}
	addr += 4;

	std::shared_ptr<ClassTypeInfo> cti;

	std::shared_ptr<ClassTypeInfo> baseRtti;
	if (baseAddr.isDefined() && ff->isPointer(addrOfBaseAddr)
			&& baseAddr != rttiAddr)
	{
		baseRtti = parseGccRtti(ff, rttis, baseAddr);
		if (baseRtti == nullptr)
		{
			LOG << "\t[FAILED] parsing base rtti @ " << baseAddr << "\n";
		}
	}

	if (baseRtti)
	{
		LOG << "\t\tSIMPLE" << "\n";

		auto scti = std::make_shared<SiClassTypeInfo>();
		cti = scti;
		scti->baseClassAddr = baseAddr;
		scti->baseClass = baseRtti;
	}
	else if (flags.isDefined()
			&& baseCount.isDefined()
			&& flags < (VmiClassTypeInfo::NON_DIAMOND_REPEAT_MASK
					+ VmiClassTypeInfo::DIAMOND_SHAPED_MASK))
	{
		LOG << "\t\tMULTIPLE"<< "\n";

		auto vcti = std::make_shared<VmiClassTypeInfo>();
		vcti->flags = flags;
		vcti->baseCount = baseCount;

		bool failed = false;
		for (unsigned i=0; i<baseCount; ++i)
		{
			BaseClassTypeInfo bcti;

			std::uint64_t mbaseAddr = 0;
			if (!ff->getWord(addr, mbaseAddr))
			{
				LOG << "\t\t[NON-CRITICAL FAIL] mbaseAddr @ " << addr
					<< std::endl << std::endl;
				failed = true;
				break;
			}
			LOG << "\t\t\tbase = " << mbaseAddr << "\n";
			bcti.baseClassAddr = mbaseAddr;

			baseRtti = nullptr;
			if (ff->isPointer(addr) && mbaseAddr != rttiAddr)
			{
				baseRtti = parseGccRtti(ff, rttis, mbaseAddr);
			}
			if (baseRtti == nullptr)
			{
				LOG << "\t[FAILED] parsing rtti @ " << mbaseAddr << "\n";
				failed = true;
				break;
			}
			bcti.baseClass = baseRtti;

			addr += wordSize;
			std::uint64_t oflags = 0;
			if (!ff->get4Byte(addr, oflags))
			{
				LOG << "\t\t[NON-CRITICAL FAIL] oflags @ " << addr
					<< std::endl << std::endl;
				failed = true;
				break;
			}
			LOG << "\t\t\tflags= " << oflags << "\n";
			bcti.offsetFlags = oflags;
			addr += 4;

			vcti->baseInfo.push_back(bcti);
		}

		if (!failed)
		{
			cti = vcti;
		}
	}
	else
	{
		// this is ok -> no base class -> this class is the base.
	}

	if (cti == nullptr)
	{
		LOG << "\t\tBASE"<< "\n";
		cti = std::make_shared<ClassTypeInfo>();
	}

	cti->vtableAddr = vptrAddr;
	cti->nameAddr = nameAddr;
	cti->address = rttiAddr;
	cti->name = name;

	LOG << "\t[OK] parsed" << std::endl << std::endl;

	return rttis.emplace(rttiAddr, cti).first->second;
}

void finalizeGccRtti(CppRttiGcc& rttis)
{
	for (auto &rtti : rttis)
	{
		if (auto scti = std::dynamic_pointer_cast<SiClassTypeInfo>(rtti.second))
		{
			auto fIt = rttis.find(scti->baseClassAddr);
			if (fIt != rttis.end())
			{
				scti->baseClass = fIt->second;
			}
		}
		else if (auto vcti = std::dynamic_pointer_cast<VmiClassTypeInfo>(rtti.second))
		{
			for (auto &bcti : vcti->baseInfo)
			{
				auto fIt = rttis.find(bcti.baseClassAddr);
				if (fIt != rttis.end())
				{
					bcti.baseClass = fIt->second;
				}
			}
		}
	}
}

} // namespace fileformat
} // namespace retdec
