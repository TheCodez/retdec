/**
 * @file include/retdec/stacofin/stacofin.h
 * @brief Static code finder library.
 * @copyright (c) 2017 Avast Software, licensed under the MIT license
 */

#ifndef RETDEC_STACOFIN_STACOFIN_H
#define RETDEC_STACOFIN_STACOFIN_H

#include <string>
#include <utility>
#include <vector>

#include "retdec/utils/address.h"
#include "retdec/utils/string.h"

using namespace retdec::utils;

namespace retdec {
namespace loader {
	class Image;
} // namespace loader

namespace stacofin {

/**
 * Forward declaration.
 */
class DetectedFunction;

class Reference
{
	public:
		Reference(
				std::size_t o,
				const std::string& n,
				utils::Address a = utils::Address::getUndef,
				utils::Address t = utils::Address::getUndef,
				DetectedFunction* tf = nullptr,
				bool k = false);

	public:
		std::size_t offset = 0;
		std::string name;

		utils::Address address;
		utils::Address target;
		DetectedFunction* targetFnc = nullptr;
		bool ok = false;
};

/**
 * Structure representing one detected function.
 */
struct DetectedFunction
{
	public:
		bool operator<(const DetectedFunction& o) const;

		bool allRefsOk() const;
		std::size_t countRefsOk() const;
		float refsOkShare() const;
		std::string getName() const;
		retdec::utils::Address getAddress() const;
		bool isTerminating() const;
		bool isThumb() const;

		/// @name Setters.
		/// @{
		void setReferences(const std::string &refsString);
		void setAddress(retdec::utils::Address a);
		/// @}

	public:
		/// Original size of source.
		std::size_t size;
		/// File offset.
		std::size_t offset;

		/// Possible original names.
		std::vector<std::string> names;
		/// Offset-name relocation pairs.
		std::vector<Reference> references;

		/// Source signature path.
		std::string signaturePath;

	private:
		/// Virtual address.
		retdec::utils::Address address;
};

/**
 * Finder implementation using Yara.
 */
class Finder
{
	public:
		using DetectedFunctionsPtrMap = typename std::map<
				utils::Address,
				stacofin::DetectedFunction*>;
		using DetectedFunctionsMultimap = typename std::multimap<
				utils::Address,
				stacofin::DetectedFunction>;
		using DetectedFunctionsPtrMultimap = typename std::multimap<
				utils::Address,
				stacofin::DetectedFunction*>;

	public:
		/// @name Actions.
		/// @{
		void clear();
		void search(
			const retdec::loader::Image &image,
			const std::string &yaraFile);
		std::string dumpDetectedFunctions() const;
		/// @}

		/// @name Getters.
		/// @{
		retdec::utils::AddressRangeContainer getCoveredCode();
		DetectedFunctionsMultimap& getDectedFunctions();
		const DetectedFunctionsMultimap& getDectedFunctions() const;
		/// @}

	private:
		/// Code coverage.
		retdec::utils::AddressRangeContainer coveredCode;
		/// Functions.
		DetectedFunctionsMultimap detectedFunctions;

		bool isSorted = true; ///< @c true if detected functions are sorted.
};

} // namespace stacofin
} // namespace retdec

#endif
