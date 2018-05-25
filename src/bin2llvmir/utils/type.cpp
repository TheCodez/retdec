/**
 * @file src/bin2llvmir/utils/type.cpp
 * @brief LLVM type utilities.
 * @copyright (c) 2017 Avast Software, licensed under the MIT license
 */

#include <iostream>
#include <regex>
#include <vector>

#include <llvm/../../lib/IR/LLVMContextImpl.h>
#include <llvm/IRReader/IRReader.h>
#include <llvm/Support/MemoryBuffer.h>
#include <llvm/Support/SourceMgr.h>
#include <llvm/Support/raw_ostream.h>

#include "retdec/utils/conversion.h"
#include "retdec/utils/string.h"
#include "retdec/bin2llvmir/providers/config.h"
#include "retdec/bin2llvmir/utils/instruction.h"
#include "retdec/bin2llvmir/utils/type.h"
#include "retdec/bin2llvmir/utils/llvm.h"

using namespace llvm;

namespace retdec {
namespace bin2llvmir {

namespace {

/**
 * Change @c val declaration to @c toType. Only the object type is changed,
 * not its usages. Because of this, it is not safe to use this function alone.
 * This function is not public, i.e. accessible from other modules.
 * @param config Configuration that needs to be changed when object changed.
 * @param objf   Object file for this object -- needed to initialize it values.
 * @param module Module.
 * @param val    Value which type to change.
 * @param toType Type to change it to.
 * @param init   Initializer constant.
 * @return New value with a desired type. This may be the same as @a val if
 * value's type can be mutated, or a new object if it cannot.
 */
Value* changeObjectDeclarationType(
		Config* config,
		FileImage* objf,
		Module* module,
		Value* val,
		Type* toType,
		Constant* init = nullptr,
		bool wideString = false)
{
	if (val->getType() == toType)
	{
		return val;
	}

	if (auto* alloca = dyn_cast<AllocaInst>(val))
	{
		auto* ret = new AllocaInst(toType, alloca->getName(), alloca);
		ret->takeName(alloca);
		return ret;
	}
	else if (auto* ogv = dyn_cast<GlobalVariable>(val))
	{
		if (init == nullptr)
		{
			init = objf->getConstant(
					toType,
					config->getGlobalAddress(ogv),
					wideString);
		}

		auto* old = ogv;
		ogv = new GlobalVariable(
				*module,
				init ? init->getType() : toType,
				old->isConstant(),
				old->getLinkage(),
				init,
				old->getName());
		ogv->takeName(old);

		auto* ecgv = config->getConfigGlobalVariable(ogv);
		if (ecgv)
		{
			retdec::config::Object cgv(
					ecgv->getName(),
					ecgv->getStorage());
			cgv.type.setLlvmIr(
					llvmObjToString(ogv->getType()->getPointerElementType()));
			cgv.type.setIsWideString(wideString);
			config->getConfig().globals.insert(cgv);
		}

		return ogv;
	}
	else if (auto* arg = dyn_cast<Argument>(val))
	{
		return modifyFunctionArgumentType(config, arg, toType);
	}
	else
	{
		errs() << "unhandled value type : " << *val << "\n";
		assert(false && "unhandled value type");
		return val;
	}
}

} // anonymous namespace

Instruction* insertBeforeAfter(Instruction* i, Instruction* b, Instruction* a)
{
	if (b)
	{
		i->insertBefore(b);
	}
	else
	{
		i->insertAfter(a);
	}
	return i;
}

/**
 *
 */
Value* convertToType(
		Value* val,
		Type* type,
		Instruction* before,
		Instruction* after,
		bool constExpr)
{
	if (val == nullptr
			|| type == nullptr
			|| (!constExpr && before == nullptr && after == nullptr))
	{
		return nullptr;
	}

	auto* cval = dyn_cast<Constant>(val);
	if (constExpr)
	{
		assert(cval);
	}

	auto& ctx = type->getContext();
	Value* conv = nullptr;

	if (val->getType() == type)
	{
		conv = val;
	}
	else if (val->getType()->isPointerTy() && type->isPointerTy())
	{
		if (constExpr)
		{
			conv = ConstantExpr::getBitCast(cval, type);
		}
		else
		{
			auto* i = new BitCastInst(val, type, "");
			conv = insertBeforeAfter(i, before, after);
		}
	}
	else if (val->getType()->isPointerTy() && type->isIntegerTy())
	{
		if (constExpr)
		{
			conv = ConstantExpr::getPtrToInt(cval, type);
		}
		else
		{
			auto* i = new PtrToIntInst(val, type, "");
			conv = insertBeforeAfter(i, before, after);
		}
	}
	else if (val->getType()->isIntegerTy() && type->isPointerTy())
	{
		if (constExpr)
		{
			conv = ConstantExpr::getIntToPtr(cval, type);
		}
		else
		{
			auto* i = new IntToPtrInst(val, type, "");
			conv = insertBeforeAfter(i, before, after);
		}
	}
	else if (val->getType()->isIntegerTy() && type->isIntegerTy())
	{
		if (constExpr)
		{
			conv = ConstantExpr::getIntegerCast(cval, type, true);
		}
		else
		{
			auto* i = CastInst::CreateIntegerCast(val, type, true, "");
			conv = insertBeforeAfter(i, before, after);
		}
	}
	else if (val->getType()->isIntegerTy() && type->isFloatingPointTy())
	{
		auto* toInt = Type::getIntNTy(ctx, type->getPrimitiveSizeInBits());
		auto* szConv = convertToType(val, toInt, before, after, constExpr);

		if (constExpr)
		{
			conv = ConstantExpr::getBitCast(cast<Constant>(szConv), type);
		}
		else
		{
			auto* i = new BitCastInst(szConv, type, "");
			auto* a = val == szConv ? after : cast<Instruction>(szConv);
			conv = insertBeforeAfter(i, before, a);
		}
	}
	else if (val->getType()->isPointerTy() && type->isFloatingPointTy())
	{
		auto* toInt = Type::getIntNTy(ctx, type->getPrimitiveSizeInBits());
		auto* intConv = convertToType(val, toInt, before, after, constExpr);
		auto* a = dyn_cast<Instruction>(intConv);
		conv = convertToType(intConv, type, before, a, constExpr);
	}
	else if (val->getType()->isFloatingPointTy() && type->isIntegerTy())
	{
		Type* ft = nullptr;
		IntegerType* intT = cast<IntegerType>(type);
		switch (intT->getBitWidth())
		{
			case 16: ft = Type::getHalfTy(ctx); break;
			case 32: ft = Type::getFloatTy(ctx); break;
			case 64: ft = Type::getDoubleTy(ctx); break;
			case 80: ft = Type::getX86_FP80Ty(ctx); break;
			default:
			{
				auto* fpConv = convertToType(
						val,
						Type::getInt32Ty(ctx),
						before,
						after,
						constExpr);
				auto* a = dyn_cast<Instruction>(fpConv);
				conv = convertToType(fpConv, intT, before, a, constExpr);
				return conv;
			}
		}

		if (val->getType() != ft)
		{
			auto* fpConv = convertToType(val, ft, before, after, constExpr);
			auto* a = dyn_cast<Instruction>(fpConv);
			conv = convertToType(fpConv, intT, before, a, constExpr);
		}
		else
		{
			if (constExpr)
			{
				conv = ConstantExpr::getBitCast(cval, intT);
			}
			else
			{
				auto* i = new BitCastInst(val, intT, "");
				conv = insertBeforeAfter(i, before, after);
			}
		}
	}
	else if (val->getType()->isFloatingPointTy() && type->isPointerTy())
	{
		auto* toInt = Type::getIntNTy(
				ctx,
				val->getType()->getPrimitiveSizeInBits());
		auto* intConv = convertToType(val, toInt, before, after, constExpr);
		auto* a = dyn_cast<Instruction>(intConv);
		conv = convertToType(intConv, type, before, a, constExpr);
	}
	else if (val->getType()->isFloatingPointTy() && type->isFloatingPointTy())
	{
		if (constExpr)
		{
			conv = ConstantExpr::getFPCast(cval, type);
		}
		else
		{
			auto* i = CastInst::CreateFPCast(val, type, "");
			conv = insertBeforeAfter(i, before, after);
		}
	}
	// TODO: this is too late, it would be the best if loads/stores that
	// load/store entire aggregate types were not created at all.
	// Such complex load/stores are not possible at ASM level.
	// Something like util function createSafe{Load,Store}() that would
	// check if loaded/stored value is not aggregate and if it is, it would
	// do the same this as here.
	//
	else if (isa<LoadInst>(val) && val->getType()->isAggregateType() && !constExpr)
	{
		auto* l = cast<LoadInst>(val);
		auto* c = cast<Instruction>(convertToType(
				l->getPointerOperand(),
				PointerType::get(type, 0),
				before,
				after,
				constExpr));
		auto* nl = new LoadInst(c);
		nl->insertAfter(c);
		conv = nl;
	}
	else if (val->getType()->isAggregateType())
	{
		std::vector<unsigned> idxs = { 0 };
		Value* toSimple = nullptr;
		if (constExpr)
		{
			toSimple = ConstantExpr::getExtractValue(
					cval,
					ArrayRef<unsigned>(idxs));
		}
		else
		{
			auto* i = ExtractValueInst::Create(
					val,
					ArrayRef<unsigned>(idxs),
					"");
			toSimple = insertBeforeAfter(i, before, after);
		}
		auto* a = dyn_cast<Instruction>(toSimple);
		conv = convertToType(toSimple, type, before, a, constExpr);
	}
	else if (CompositeType* cmp = dyn_cast<CompositeType>(type))
	{
		assert(!cmp->isEmptyTy());
		std::vector<unsigned> idxs = { 0 };
		auto* idxt = cmp->getTypeAtIndex(0u);
		auto* tmp = convertToType(val, idxt, before, after, constExpr);

		if (constExpr)
		{
			auto* c = dyn_cast<Constant>(tmp);
			assert(c);
			conv = ConstantExpr::getInsertValue(
					UndefValue::get(cmp),
					c,
					ArrayRef<unsigned>(idxs));
		}
		else
		{
			auto* i = InsertValueInst::Create(
					UndefValue::get(cmp),
					tmp,
					ArrayRef<unsigned>(idxs),
					"");
			auto* a = val == tmp ? after : cast<Instruction>(tmp);
			conv = insertBeforeAfter(i, before, a);
		}
	}
	else
	{
		errs() << "\nconvertValueToType(): unhandled type conversion\n";
		errs() << *val << "\n";
		errs() << *type << "\n\n";
		assert(false);
		conv = nullptr;
	}

	return conv;
}

/**
 * Create type conversion from provided value to provided type.
 * Created instructions are inserted before the specified instruction.
 * @param val Value to convert.
 * @param type Type to convert to.
 * @param before Instruction before which created conversion instructions
 *        are inserted.
 * @return Final value of the specified type.
 */
Value* convertValueToType(Value* val, Type* type, Instruction* before)
{
	return convertToType(val, type, before, nullptr, false);
}

/**
 * Create type conversion from provided value to provided type.
 * Created instructions are inserted after the specified instruction.
 * @param val Value to convert.
 * @param type Type to convert to.
 * @param after Instruction after which created conversion instructions
 *        are inserted.
 * @return Final value of the specified type.
 */
llvm::Value* convertValueToTypeAfter(
		llvm::Value* val,
		llvm::Type* type,
		llvm::Instruction* after)
{
	return convertToType(val, type, nullptr, after, false);
}

/**
 * This is the same as @c convertValueToType() but working with constants.
 * It does not insert constant expressions (type casts) to any particular place
 * in the IR. It just returns the created constant expressions.
 * @param val  Constant value to convert.
 * @param type Type to convert to.
 * @return Constant expression representing type conversion.
 */
Constant* convertConstantToType(Constant* val, Type* type)
{
	auto* v = convertToType(val, type, nullptr, nullptr, true);
	auto* c = dyn_cast_or_null<Constant>(v);
	if (v)
	{
		assert(c);
	}
	return c;
}

/**
 * Change @c val type to @c toType and fix all its uses.
 * @param config Configuration that needs to be changed when object changed.
 * @param objf   Object file for this object -- needed to initialize it values.
 * @param module Module.
 * @param val    Value which type to change.
 * @param toType Type to change it to.
 * @param init   Initializer constant.
 * @param instToErase Some instructions may become obsolete. If pointer to this
 *                    container is provided, function adds such instructions to
 *                    it and it is up to the caller to erase them. Otherwise,
 *                    function erases such instructions from parent.
 *                    If caller does not have instructions saved, it is save
 *                    to erase them here -- pass nullptr.
 *                    If caller is performing some analysis where it has
 *                    instructions stored in internal structures and it is
 *                    possible that they will be used after they would
 *                    have been erased, it should pass pointer to container
 *                    here and erase instructions when it is finished.
 * @param dbg    Flag to enable debug messages.
 * @param wideString Is type a wide string?
 */
llvm::Value* changeObjectType(
		Config* config,
		FileImage* objf,
		Module* module,
		Value* val,
		Type* toType,
		Constant* init,
		std::unordered_set<llvm::Instruction*>* instToErase,
		bool dbg,
		bool wideString)
{
	if (!(isa<AllocaInst>(val)
			|| isa<GlobalVariable>(val)
			|| isa<Argument>(val)))
	{
		assert(false && "only globals, allocas and arguments can be changed");
		return val;
	}

	if (val->getType() == toType)
	{
		return val;
	}

	Type* origType = val->getType();
	auto* nval = changeObjectDeclarationType(
			config,
			objf,
			module,
			val,
			toType,
			init,
			wideString);
	Constant* newConst = dyn_cast<Constant>(nval);

	// For some reason, iteration using val->user_begin() and val->user_end()
	// may break -- there are many uses, but after modifying one of them,
	// iteration ends before visiting all of them. Even when we increment
	// iterator before modification.
	// Example: @glob_var_0 in arm-elf-059c1a6996c630386b5067c2ccc6ddf2
	// Therefore, we store all uses to our own container.
	//
	std::list<User*> users;
	for (const auto& U : val->users())
	{
		users.push_back(U);
	}

	for (auto* user : users)
	{
		Constant* c = dyn_cast<Constant>(user);
		auto* gvDeclr = dyn_cast<GlobalVariable>(user);

		if (auto* store = dyn_cast<StoreInst>(user))
		{
			Value* src = store->getValueOperand();
			Value* dst = store->getPointerOperand();

			if (val == dst)
			{
				PointerType* ptr = dyn_cast<PointerType>(nval->getType());
				assert(ptr);
				auto* conv = convertValueToType(src, ptr->getElementType(), store);
				store->setOperand(0, conv);
				store->setOperand(1, nval);
			}
			else
			{
				auto* conv = convertValueToType(nval, origType, store);
				store->setOperand(0, conv);
			}
		}
		else if (auto* load = dyn_cast<LoadInst>(user))
		{
			assert(val == load->getPointerOperand());

			auto* newLoad = new LoadInst(nval);
			newLoad->insertBefore(load);

			// load->getType() stays unchanged even after loaded object's type is mutated.
			// we can use it here as a target type, but the origianl load instruction can
			// not be used afterwards, because its type is incorrect.
			auto* conv = convertValueToType(newLoad, load->getType(), load);

			if (conv != load)
			{
				load->replaceAllUsesWith(conv);
				if (instToErase)
				{
					instToErase->insert(load);
				}
				else
				{
					load->eraseFromParent();
				}
			}
		}
		else if (auto* cast = dyn_cast<CastInst>(user))
		{
			if (nval->getType() == cast->getType())
			{
				if (val != cast)
				{
					cast->replaceAllUsesWith(nval);
					if (instToErase)
					{
						instToErase->insert(cast);
					}
					else
					{
						cast->eraseFromParent();
					}
				}
			}
			else
			{
				auto* conv = convertValueToType(nval, cast->getType(), cast);
				if (cast != conv)
				{
					cast->replaceAllUsesWith(conv);
					if (instToErase)
					{
						instToErase->insert(cast);
					}
					else
					{
						cast->eraseFromParent();
					}
				}
			}
		}
		// maybe GetElementPtrInst should be specially handled?
		else if (auto* instr = dyn_cast<Instruction>(user))
		{
			auto* conv = convertValueToType(nval, origType, instr);
			if (val != conv)
			{
				instr->replaceUsesOfWith(val, conv);
			}
		}
		else if (newConst && gvDeclr)
		{
			auto* conv = convertConstantToType(
					newConst,
					gvDeclr->getType()->getPointerElementType());
			if (gvDeclr != conv)
			{
//				gvDeclr->replaceUsesOfWith(newConst, conv);
				gvDeclr->replaceUsesOfWith(val, conv);
			}
		}
		// Needs to be at the very end, many objects can be casted to Constant.
		//
		else if (newConst && c)
		{
			auto* conv = convertConstantToType(newConst, c->getType());
			if (c != conv)
			{
				c->replaceAllUsesWith(conv);
			}
		}
		else
		{
			errs() << "unhandled use : " << *user << " -> " << *toType << "\n";
			assert(false && "unhandled use");
		}
	}

	return nval;
}

/**
 * Parse format string @a format used in functions such as @c printf or @c scanf
 * into vector of data types in context of module @a module.
 * If @a calledFnc provided and called function name contains "scan" string, all
 * types are transformed to pointers.
 * @return Vector of data types used in format string.
 *
 * This is done according to:
 * http://www.cplusplus.com/reference/cstdio/printf/
 * but we need small updates, because it is used for scanf where are small
 * differences in floating point numbers:
 * http://www.cplusplus.com/reference/cstdio/scanf/
 */
std::vector<llvm::Type*> parseFormatString(
		llvm::Module* module,
		const std::string& format,
		llvm::Function* calledFnc)
{
	LLVMContext& ctx = module->getContext();
	std::vector<Type*> ret;

	const char *cp = format.c_str();
	size_t max_width_length = 0;
	size_t max_precision_length = 0;

	while (*cp != '\0')
	{
		char c = *cp++;
		if (c != '%')
		{
			continue;
		}

		// Test for positional argument.
		//
		if (*cp >= '0' && *cp <= '9')
		{
			const char *np;

			for (np = cp; *np >= '0' && *np <= '9'; np++) {};

			if (*np == '$')
			{
				size_t n = 0;
				for (np = cp; *np >= '0' && *np <= '9'; np++)
				{
					n += n*10 + *np - '0';
				}
				if (n == 0) // Positional argument 0.
				{
					return ret;
				}
				cp = np + 1;
			}
		}

		// Read the flags.
		//
		for (;;)
		{
			if (*cp == '\'')
			{
				cp++;
			}
			else if (*cp == '-')
			{
				cp++;
			}
			else if (*cp == '+')
			{
				cp++;
			}
			else if (*cp == ' ')
			{
				cp++;
			}
			else if (*cp == '#')
			{
				cp++;
			}
			else if (*cp == '0')
			{
				cp++;
			}
			else
			{
				break;
			}
		}

		// Parse the field width.
		//
		if (*cp == '*')
		{
			cp++;
			if (max_width_length < 1)
			{
				max_width_length = 1;
			}

			// Test for positional argument.
			if (*cp >= '0' && *cp <= '9')
			{
				const char *np;

				for (np = cp; *np >= '0' && *np <= '9'; np++) {};

				if (*np == '$')
				{
					size_t n = 0;
					for (np = cp; *np >= '0' && *np <= '9'; np++)
					{
						n += n * 10 + *np - '0';
					}
					if (n == 0) // Positional argument 0.
					{
						return ret;
					}
					cp = np + 1;
				}
			}

			ret.push_back(Abi::getDefaultType(module));
		}
		else if (*cp >= '0' && *cp <= '9')
		{
			for (; *cp >= '0' && *cp <= '9'; cp++) {}; // skipping
		}

		// Parse the precision.
		//
		if (*cp == '.')
		{
			cp++;
			if (*cp == '*')
			{
				cp++;
				if (max_precision_length < 2)
				{
					max_precision_length = 2;
				}

				// Test for positional argument.
				if (*cp >= '0' && *cp <= '9')
				{
					const char *np;

					for (np = cp; *np >= '0' && *np <= '9'; np++) {};

					if (*np == '$')
					{
						size_t n = 0;
						for (np = cp; *np >= '0' && *np <= '9'; np++)
						{
							n += n * 10 + *np - '0';
						}
						if (n == 0) // Positional argument 0.
						{
							return ret;
						}
						cp = np + 1;
					}
				}

				ret.push_back(Abi::getDefaultType(module));
			}
			else
			{
				for (; *cp >= '0' && *cp <= '9'; cp++) {}; // skipping
			}
		}

		// Parse argument type/size specifiers.
		//
		int flags = 0;
		for (;;)
		{
			if (*cp == 'h')
			{
				flags |= (1 << (flags & 1));
				cp++;
			}
			else if (*cp == 'L')
			{
				flags |= 4;
				cp++;
			}
			else if (*cp == 'l')
			{
				flags += 8;
				cp++;
			}
			else if (*cp == 'I')
			{
				// specific to msvs, see http://msdn.microsoft.com/en-us/library/56e442dc.aspx
				// can be: "I" or "I32" or "I64"
				cp++;
				if (*cp == '3' || *cp == '6')
				{
					cp++;
					if (*cp == '2')
					{
						flags += 8;
					}
					else if (*cp == '4')
					{
						flags += 16;
					}
					cp++;
				}
			}
			else if (*cp == 'j')
			{
				// 64 -> +16, 32 -> +8, always 64?
				flags += 16;
				cp++;
			}
			// 'z' is standardized in ISO C 99, but glibc uses 'Z'
			// because the warning facility in gcc-2.95.2 understands
			// only 'Z' (see gcc-2.95.2/gcc/c-common.c:1784).
			else if (*cp == 'z' || *cp == 'Z')
			{
				// 64 -> +16, 32 -> +8, always 64?
				flags += 16;
				cp++;
			}
			else if (*cp == 't')
			{
				auto* dt = Abi::getDefaultType(module);
				if (dt->getBitWidth() == 64)
				{
					flags += 16;
				}
				else
				{
					flags += 8;
				}
				cp++;
			}
			else
				break;
		}

		// Read the conversion character.
		//
		Type* type = nullptr;
		c = *cp++;
		switch (c)
		{
			case 'd':
			case 'i':
			{
				if (flags >= 16 || (flags & 4))
				{
					type = Type::getInt64Ty(ctx);
				}
				else
				{
					if (flags >= 8) type = Type::getInt32Ty(ctx);
					else if (flags & 2) type = Type::getInt8Ty(ctx);
					else if (flags & 1) type = Type::getInt16Ty(ctx);
					else type = Abi::getDefaultType(module);
				}
				break;
			}
			case 'o':
			case 'u':
			case 'x':
			case 'X':
			{
				if (flags >= 16 || (flags & 4))
				{
					type = Type::getInt64Ty(ctx);
				}
				else
				{
					if (flags >= 8) type = Type::getInt32Ty(ctx);
					else if (flags & 2) type = Type::getInt8Ty(ctx);
					else if (flags & 1) type = Type::getInt16Ty(ctx);
					else type = Type::getInt32Ty(ctx);
				}
				break;
			}
			case 'f':
			case 'F':
			case 'e':
			case 'E':
			case 'g':
			case 'G':
			case 'a':
			case 'A':
			{
				if (flags >= 16 || (flags & 4))
				{
					type = Type::getX86_FP80Ty(ctx);
				}
				else
				{
					type = Type::getDoubleTy(ctx);
				}
				break;
			}
			case 'c':
			{
				type = Type::getInt8Ty(ctx);
				break;
			}
			case 'C':
			{
				type = Type::getInt8Ty(ctx);
				c = 'c';
				break;
			}
			case 's':
			{
				type = llvm_utils::getCharPointerType(ctx);
				break;
			}
			case 'S':
			{
				type = llvm_utils::getCharPointerType(ctx);
				c = 's';
				break;
			}
			case 'p':
			{
				type = Abi::getDefaultPointerType(module);
				break;
			}
			case 'n':
			{
				if (flags >= 16 || (flags & 4))
				{
					type = PointerType::get(Type::getInt64Ty(ctx), 0);
				}
				else
				{
					if (flags >= 8) type = Type::getInt32Ty(ctx);
					else if (flags & 2) type = Type::getInt8Ty(ctx);
					else if (flags & 1) type = Type::getInt16Ty(ctx);
					else type = Type::getInt32Ty(ctx);
					type = PointerType::get(type, 0);
				}
				break;
			}
			case '%':
			{
				type = nullptr;
				break;
			}
			default: // Unknown conversion character.
			{
				type = Abi::getDefaultType(module);
				break;
			}
		}

		if (type)
		{
			ret.push_back(type);
		}
	}

	if (calledFnc && retdec::utils::contains(calledFnc->getName(), "scan"))
	{
		for (size_t i = 0; i < ret.size(); ++i)
		{
			ret[i] = PointerType::get(ret[i], 0);
		}
	}

	return ret;
}

} // namespace bin2llvmir
} // namespace retdec
