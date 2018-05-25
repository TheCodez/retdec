/**
 * @file src/llvm-support/utils.cpp
 * @brief LLVM Utility functions.
 * @copyright (c) 2017 Avast Software, licensed under the MIT license
 */

#include <fstream>
#include <regex>

#include <llvm/Support/Casting.h>
#include <llvm/../../lib/IR/LLVMContextImpl.h>

#include "retdec/bin2llvmir/providers/abi/abi.h"
#include "retdec/bin2llvmir/utils/llvm.h"
#include "retdec/utils/conversion.h"

using namespace llvm;

namespace retdec {
namespace bin2llvmir {
namespace llvm_utils {

//
//==============================================================================
// Values
//==============================================================================
//

/**
 * Skips both casts and getelementptr instructions and constant expressions.
 */
llvm::Value* skipCasts(llvm::Value* val)
{
	while (true)
	{
		if (auto* c = dyn_cast_or_null<CastInst>(val))
		{
			val = c->getOperand(0);
		}
		else if (auto* p = dyn_cast_or_null<GetElementPtrInst>(val))
		{
			val = p->getOperand(0);
		}
		else if (auto* ce = dyn_cast_or_null<ConstantExpr>(val))
		{
			if (ce->isCast()
					|| ce->getOpcode() == Instruction::GetElementPtr)
			{
				val = ce->getOperand(0);
			}
			else
			{
				return val;
			}
		}
		else
		{
			return val;
		}
	}

	return val;
}

//
//==============================================================================
// Types
//==============================================================================
//

llvm::IntegerType* getCharType(llvm::LLVMContext& ctx)
{
	return Type::getInt8Ty(ctx);
}

llvm::PointerType* getCharPointerType(llvm::LLVMContext& ctx)
{
	return PointerType::get(getCharType(ctx), 0);
}

/**
 * @return @c True if @a t is the same as @c getCharType() result,
 *         @c false otherwise.
 */
bool isCharType(const llvm::Type* t)
{
	return t ? t == getCharType(t->getContext()) : false;
}

/**
 * @return @c True if @a t is the same as @c getCharPointerType() result,
 *         @c false otherwise.
 */
bool isCharPointerType(const llvm::Type* t)
{
	return t ? t == getCharPointerType(t->getContext()) : false;
}

/**
 * @return @c True if @a t is a string array -- an array of char elements,
 *         @c false otherwise.
 */
bool isStringArrayType(const llvm::Type* t)
{
	auto* at = dyn_cast_or_null<ArrayType>(t);
	return at ? isCharType(at->getElementType()) : false;
}

/**
 * @return @c True if @a t is a pointer to string array type
 *         (see @c isStringArrayType), @c false otherwise.
 */
bool isStringArrayPointeType(const llvm::Type* t)
{
	auto* pt = dyn_cast_or_null<PointerType>(t);
	return pt ? isStringArrayType(pt->getElementType()) : false;
}

/**
 * This is the same as @c stringToLlvmType(), but default type is returned
 * instead of nulltpr.
 */
llvm::Type* stringToLlvmTypeDefault(llvm::Module* m, const std::string& str)
{
	auto* t = stringToLlvmType(m->getContext(), str);
	return t ? t : Abi::getDefaultType(m);
}

/**
 * Parse string with list of LLVM types (i.e. "t1,..,tn") into vector
 * of LLVM types.
 * @param ctx           Context in which the LLVM type is created.
 * @param list          String list to parse.
 * @param[out] typeList Output vector to fill.
 * @return @c False if parsing was successful, @c true otherwise.
 */
bool parseTypeList(
		LLVMContext& ctx,
		std::string list,
		std::vector<Type*>& typeList)
{
	while (!list.empty())
	{
		size_t pos = 0;
		if (retdec::utils::findFirstInEmbeddedLists(
				pos,
				list,
				',',
				{ {'{','}'}, {'(',')'} }))
		{
			return true;
		}

		std::string elemStr = list.substr(0, pos);
		if (pos == std::string::npos)
			list.erase(0, pos);
		else
			list.erase(0, pos+1);

		auto* elemType = stringToLlvmType(ctx, elemStr);
		if (elemType == nullptr)
		{
			return true;
		}
		typeList.push_back(elemType);
	}

	return false;
}

/**
 * Convert the provided LLVM type string representation into an LLVM type.
 * @param ctx Context in which the LLVM type is created.
 * @param str String with LLVM type representation.
 * @return LLVM type if the conversion was successful, @c nullptr otherwise.
 */
Type* stringToLlvmType(LLVMContext& ctx, const std::string& str)
{
	std::string s = retdec::utils::removeWhitespace(str);

	std::smatch match;

	static std::regex regexInt(R"(i(\d+))");
	static std::regex regexPointer(R"((.+)\*)");
	static std::regex regexArray(R"(\[(\d+)x(.+)\])");
	static std::regex regexVector(R"(<(\d+)x(.+)>)");
	static std::regex regexFunction(R"((.+)\((.*)\))");
	static std::regex regexOpaqueIdStruct(R"(%(.+)=typeopaque)");
	static std::regex regexLiteralStruct(R"(\{(.*)\})");
	static std::regex regexLiteralStructPacked(R"(<\{(.*)\}>)");
	static std::regex regexIdStruct(R"(%(.+)=type\{(.*)\})");
	static std::regex regexIdStructPacked(R"(%(.+)=type<\{(.*)\}>)");
	static std::regex regexStructId(R"(%(.+))");

	// Primitive types: <keyword>.
	//
	if (s=="void") return Type::getVoidTy(ctx);
	else if (s=="label") return Type::getLabelTy(ctx);
	else if (s=="half") return Type::getHalfTy(ctx);
	else if (s=="float") return Type::getFloatTy(ctx);
	else if (s=="double") return Type::getDoubleTy(ctx);
	else if (s=="metadata") return Type::getMetadataTy(ctx);
	else if (s=="x86_fp80") return Type::getX86_FP80Ty(ctx);
	else if (s=="fp128") return Type::getFP128Ty(ctx);
	else if (s=="ppc_fp128") return Type::getPPC_FP128Ty(ctx);
	else if (s=="x86_mmx") return Type::getX86_MMXTy(ctx);
	else if (std::regex_match(s, match, regexInt))
	{
		unsigned intBits = 0;
		if (retdec::utils::strToNum(match[1], intBits) && intBits > 0)
		{
			return Type::getIntNTy(ctx, intBits);
		}
		else
		{
			return nullptr;
		}
	}
	// Pointer type: <type>*
	//
	else if (std::regex_match(s, match, regexPointer))
	{
		auto* t = stringToLlvmType(ctx, match[1]);

		// Special handling for void*. In LLVM, void is not a valid type for
		// PointerType, but we need to handle it because of LTI and other
		// outside sources that might not be so strict.
		//
		if (t && t->isVoidTy())
		{
			return PointerType::get(
					Type::getInt8Ty(ctx),
					Abi::DEFAULT_ADDR_SPACE);
		}

		return t == nullptr ?
				t :
				PointerType::isValidElementType(t) ?
						PointerType::get(t, Abi::DEFAULT_ADDR_SPACE) :
						nullptr;
	}
	// Array type: [<#elems> x <elem type>]
	//
	else if (std::regex_match(s, match, regexArray))
	{
		unsigned n = 0;
		if (retdec::utils::strToNum(match[1], n))
		{
			auto d = n > 0 ? n : 1;
			auto* t = stringToLlvmType(ctx, match[2]);
			return t == nullptr ?
					t :
					ArrayType::isValidElementType(t) ?
							ArrayType::get(t, d) :
							nullptr;
		}
		else
		{
			return nullptr;
		}
	}
	// Vector type: <<#elems> x <elem type>>
	// Element types are only primitive types.
	//
	else if (std::regex_match(s, match, regexVector))
	{
		unsigned n = 0;
		if (retdec::utils::strToNum(match[1], n))
		{
			auto* t = stringToLlvmType(ctx, match[2]);
			return t == nullptr ?
					t :
					VectorType::isValidElementType(t) ?
							VectorType::get( t, n ) :
							nullptr;
		}
		else
		{
			return nullptr;
		}
	}
	// Function type: <return type>(<type list>)
	//
	else if (std::regex_match(s, match, regexFunction))
	{
		auto* retType = stringToLlvmType(ctx, match[1]);
		if (retType == nullptr || !FunctionType::isValidReturnType(retType))
		{
			return nullptr;
		}

		std::string paramList = match[2];

		bool isVarArg = false;
		static std::regex regexVariadic(R"(.*,\.\.\.)");
		if (std::regex_match(paramList, regexVariadic))
		{
			paramList.erase(paramList.length()-4);
			isVarArg = true;
		}
		else if (paramList == "...")
		{
			paramList.clear();
			isVarArg = true;
		}

		std::vector<Type*> args;
		if (parseTypeList(ctx, paramList, args))
		{
			return nullptr;
		}
		if (!std::all_of(
				args.begin(),
				args.end(),
				FunctionType::isValidArgumentType))
		{
			return nullptr;
		}

		return FunctionType::get(retType, args, isVarArg);
	}
	// Opaque identified structure.
	//
	else if (std::regex_match(s, match, regexOpaqueIdStruct))
	{
		return StructType::create(ctx, std::string(match[1]));
	}
	// Literal structure.
	//
	else if (std::regex_match(s, match, regexLiteralStruct) ||
	         std::regex_match(s, match, regexLiteralStructPacked))
	{
		std::vector<Type*> elems;
		if (parseTypeList(ctx, match[1], elems))
		{
			return nullptr;
		}
		if (!std::all_of(
				elems.begin(),
				elems.end(),
				FunctionType::isValidArgumentType))
		{
			return nullptr;
		}

		if (elems.empty())
		{
			elems.push_back(Type::getInt32Ty(ctx));
		}

		return StructType::get(ctx, elems, s.back() == '>');
	}
	// Identified structure.
	//
	else if (std::regex_match(s, match, regexIdStruct) ||
	         std::regex_match(s, match, regexIdStructPacked))
	{
		std::vector<Type*> elems;
		if (parseTypeList(ctx, match[2], elems))
		{
			return nullptr;
		}
		if (!std::all_of(
				elems.begin(),
				elems.end(),
				FunctionType::isValidArgumentType))
		{
			return nullptr;
		}

		if (elems.empty())
		{
			elems.push_back(Type::getInt32Ty(ctx));
		}

		return StructType::create(
				ctx,
				elems,
				std::string(match[1]),
				s.back() == '>');
	}
	// Structure ID.
	// We need to get to structures that were already added to the current
	// LLVM contex. The problem is that context itself, or any other LLVM
	// object accessible from here, does not offer method to get to the
	// existing structures.
	// Possible solutions:
	// 1. Use LLVMContext::pImpl member -- private implementation of context.
	//    It offers exactly what we need -- an access to the named structures.
	//    However, it should not be used by external tools based on LLVM.
	//    This is the currently used solution.
	// 2. Cache already added structures -- this function would have to maintain
	//    static/global std::map<LLVMContext*, StructType> with all created
	//    structures. This may be dangerous -- this functions would not be
	//    aware of context's structures that were not added by it. Moreover,
	//   structures might change and I'm not sure what would happen to cached
	//   pointes.
	//
	else if (std::regex_match(s, match, regexStructId))
	{
		return ctx.pImpl->NamedStructTypes.lookup(std::string(match[1]));
	}

	return nullptr;
}

} // namespace llvm_utils
} // namespace bin2llvmir
} // namespace retdec
