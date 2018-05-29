/**
 * @file patterns/stacofinl/stacofinl.cpp
 * @brief Static code finder library.
 * @copyright (c) 2017 Avast Software, licensed under the MIT license
 */

#include <iostream>
#include <sstream>
#include <string>

#include "retdec/stacofin/stacofin.h"
#include "yaracpp/yara_detector/yara_detector.h"
#include "retdec/loader/loader/image.h"

using namespace retdec::utils;
using namespace yaracpp;
using namespace retdec::loader;

namespace retdec {
namespace stacofin {

//
//==============================================================================
// Reference.
//==============================================================================
//

Reference::Reference(
		std::size_t o,
		const std::string& n,
		utils::Address a,
		utils::Address t,
		DetectedFunction* tf,
		bool k)
		:
		offset(o),
		name(n),
		address(a),
		target(t),
		targetFnc(tf),
		ok(k)
{

}

//
//==============================================================================
// DetectedFunction.
//==============================================================================
//

bool DetectedFunction::operator<(const DetectedFunction& o) const
{
	if (address == o.address)
	{
		if (names.empty())
		{
			return true;
		}
		else if (o.names.empty())
		{
			return false;
		}
		else
		{
			return getName() < o.getName();
		}
	}
	else
	{
		return address < o.address;
	}
}

bool DetectedFunction::allRefsOk() const
{
	for (auto& ref : references)
	{
		if (!ref.ok)
		{
			return false;
		}
	}

	return true;
}

std::size_t DetectedFunction::countRefsOk() const
{
	std::size_t ret = 0;

	for (auto& ref : references)
	{
		ret += ref.ok;
	}

	return ret;
}

float DetectedFunction::refsOkShare() const
{
	return references.empty()
			? 1.0
			: float(countRefsOk()) / float(references.size());
}

std::string DetectedFunction::getName() const
{
	return names.empty() ? "" : names.front();
}

retdec::utils::Address DetectedFunction::getAddress() const
{
	return address;
}

bool DetectedFunction::isTerminating() const
{
	// TODO: couple names with source signaturePath to make sure we do not
	// hit wrong functions?
	//
	static std::set<std::string> termNames = {
			"exit",
			"_exit",
	};

	for (auto& n : names)
	{
		if (termNames.count(n))
		{
			return true;
		}
	}

	return false;
}

bool DetectedFunction::isThumb() const
{
	return utils::containsCaseInsensitive(signaturePath, "thumb");
}

/**
 * Parse string with references from meta attribute.
 *
 * @param refsString references string
 */
void DetectedFunction::setReferences(const std::string &refsString)
{
	std::string name;
	std::size_t offset;
	std::stringstream refsStream(refsString);

	for (;;) {
		refsStream >> std::hex >> offset;
		refsStream >> name;
		if (!refsStream) {
			break;
		}

		references.emplace_back(offset, name);
	}
}

/**
 * Setting an address will also update addresses of all references.
 *
 * @param a Address to set.
 */
void DetectedFunction::setAddress(retdec::utils::Address a)
{
	address = a;
	for (auto r : references)
	{
		r.address = r.offset + address;
	}
}

//
//==============================================================================
// Finder.
//==============================================================================
//

/**
 * Clear all previous results.
 */
void Finder::clear()
{
	coveredCode.clear();
	detectedFunctions.clear();
}

/**
 * Search for static code in input file.
 *
 * @param image input file image
 * @param yaraFile static code signatures
 */
void Finder::search(
	const Image &image,
	const std::string &yaraFile)
{
	// Get FileFormat instance.
	const auto* fileFormat = image.getFileFormat();
	if (!fileFormat) {
		return;
	}

	// Start Yara detector.
	YaraDetector detector;
	detector.addRuleFile(yaraFile);
	auto inputBytes = fileFormat->getLoadedBytes();
	detector.analyze(inputBytes);
	if (!detector.isInValidState()) {
		return;
	}

	// Iterate over detected rules.
	isSorted = false;
	for (const YaraRule &detectedRule : detector.getDetectedRules()) {
		DetectedFunction detectedFunction;
		detectedFunction.signaturePath = yaraFile;

		for (const YaraMeta &ruleMeta : detectedRule.getMetas()) {
			if (ruleMeta.getId() == "name") {
				detectedFunction.names.push_back(ruleMeta.getStringValue());
			}
			if (ruleMeta.getId() == "size") {
				detectedFunction.size = ruleMeta.getIntValue();
			}
			if (ruleMeta.getId() == "refs") {
				const auto &refs = ruleMeta.getStringValue();
				detectedFunction.setReferences(refs);
			}
			if (ruleMeta.getId() == "altNames") {
				std::string name;
				const auto &altNames = ruleMeta.getStringValue();
				std::istringstream ss(altNames, std::istringstream::in);
				while(ss >> name) {
					detectedFunction.names.push_back(name);
				}
			}
		}

		// Iterate over all matches.
		for (const YaraMatch &ruleMatch : detectedRule.getMatches()) {
			// This is different for every match.
			detectedFunction.offset = ruleMatch.getOffset();
			unsigned long long address = 0;
			if (!fileFormat->getAddressFromOffset(
						address, detectedFunction.offset)) {
				// Cannot get address. Maybe report error?
				continue;
			}

			// Store data.
			detectedFunction.setAddress(address);
			coveredCode.insert(AddressRange(address,
				address + detectedFunction.size));
			detectedFunctions.emplace(address, detectedFunction);
		}
	}
}

std::string Finder::dumpDetectedFunctions() const
{
	std::stringstream ret;
	ret << "\t Detected functions (bin2llvmir):" << "\n";
	for (auto& p : detectedFunctions)
	{
		auto& f = p.second;

		ret << "\t\t" << (p.second.allRefsOk() ? "[+] " : "[-] ")
				<< f.getAddress() << " @ " << f.names.front()
				<< ", sz = " << f.size << "\n";

		for (auto& ref : f.references)
		{
			ret << "\t\t\t" << (ref.ok ? "[+] " : "[-] ")
					<< ref.address << " @ " << ref.name
					<< " -> " << ref.target << "\n";
		}
	}

	return ret.str();
}

/**
 * Return detected code coverage.
 *
 * @return covered code
 */
retdec::utils::AddressRangeContainer Finder::getCoveredCode()
{
	return coveredCode;
}

/**
 * Return detected functions sorted by their address.
 *
 * @return sorted detected functions
 */
Finder::DetectedFunctionsMultimap& Finder::getDectedFunctions()
{
	return detectedFunctions;
}

const Finder::DetectedFunctionsMultimap& Finder::getDectedFunctions() const
{
	return detectedFunctions;
}

} // namespace stacofin
} // namespace retdec
