/**
 * @file src/bin2llvmir/utils/instruction.cpp
 * @brief LLVM instruction utilities.
 * @copyright (c) 2017 Avast Software, licensed under the MIT license
 */

#include <llvm/IR/Constants.h>
#include <llvm/IR/IRBuilder.h>
#include <llvm/IR/InstIterator.h>
#include <llvm/IR/LLVMContext.h>
#include <llvm/Support/raw_ostream.h>

#include "retdec/bin2llvmir/utils/llvm.h"
#include "retdec/utils/container.h"
#include "retdec/utils/string.h"
#include "retdec/bin2llvmir/providers/asm_instruction.h"
#include "retdec/bin2llvmir/utils/instruction.h"
#include "retdec/bin2llvmir/utils/ir_modifier.h"

using namespace llvm;

namespace retdec {
namespace bin2llvmir {

/**
 * Modify @a call instruction to call @a calledVal value with @a args arguments.
 *
 * At the moment, this will create a new call instruction which replaces the old
 * one. The new call is returned as return value. The old call is destroyed.
 * Therefore, users must be careful not to store pointers to it.
 * Maybe, it would be possible to modify call operands (arguments) inplace
 * as implemented in @c PHINode::growOperands(). However, this looks very
 * hackish and dangerous.
 */
llvm::CallInst* _modifyCallInst(
		llvm::CallInst* call,
		llvm::Value* calledVal,
		llvm::ArrayRef<llvm::Value*> args)
{
	std::set<Instruction*> toEraseCast;
	auto* newCall = CallInst::Create(calledVal, args, "", call);
	if (call->getNumUses())
	{
		if (!newCall->getType()->isVoidTy())
		{
			auto* cast = IrModifier::convertValueToType(newCall, call->getType(), call);
			call->replaceAllUsesWith(cast);
		}
		else
		{
			std::set<StoreInst*> toErase;

			for (auto* u : call->users())
			{
				if (auto* s = dyn_cast<StoreInst>(u))
				{
					toErase.insert(s);
				}
				// TODO: solve better.
				else if (auto* c = dyn_cast<CastInst>(u))
				{
					assert(c->getNumUses() == 1);
					auto* s = dyn_cast<StoreInst>(*c->users().begin());
					assert(s);
					toErase.insert(s);
					toEraseCast.insert(c);
				}
				else
				{
					assert(false);
				}
			}

			for (auto* i : toErase)
			{
				// TODO: erasing here is dangerous. Call result stores may be
				// used somewhere else -- e.g. entries in param_return analysis.
				//
//				i->eraseFromParent();
				auto* conf = ConfigProvider::getConfig(call->getModule());
				auto* c = IrModifier::convertValueToType(
						conf->getGlobalDummy(),
						i->getValueOperand()->getType(),
						i);
				i->replaceUsesOfWith(i->getValueOperand(), c);
			}
		}
	}
	for (auto* i : toEraseCast)
	{
		i->eraseFromParent();
	}
	call->eraseFromParent();
	return newCall;
}

/**
 * Modify call instruction:
 *   - Old called value is casted to new function pointer type derived from
 *     return value and arguments. This is done even if called value is
 *     function. If you want to avoid casts, make sure called function's type is
 *     modified before this function is called and that arguments passed in
 *     @c args have same types as called function -- they will not be casted,
 *     if they differ, function is casted to function pointer derived from them.
 *   - New function pointer type value is used to modify call instruction.
 * Notes:
 *   - If @a ret is nullptr, call's return value is left unchanged.
 *     Pass @c void type in @c ret if you want the call to return no value.
 *   - If @a args is empty, call will have zero arguments.
 * @return New call instruction which replaced the old @c call.
 *         See @c _modifyCallInst() comment for details.
 */
llvm::CallInst* modifyCallInst(
		llvm::CallInst* call,
		llvm::Type* ret,
		llvm::ArrayRef<llvm::Value*> args)
{
	ret = ret ? ret : call->getType();
	std::vector<llvm::Type*> argTypes;
	for (auto* v : args)
	{
		argTypes.push_back(v->getType());
	}
	auto* t = llvm::PointerType::get(
			llvm::FunctionType::get(
					ret,
					argTypes,
					false), // isVarArg
			0);
	auto* conv = IrModifier::convertValueToType(call->getCalledValue(), t, call);

	return _modifyCallInst(call, conv, args);
}

/**
 * Inspired by ArgPromotion::DoPromotion().
 * Steps performed in ArgPromotion::DoPromotion() that are not done here:
 *   - Patch the pointer to LLVM function in debug info descriptor.
 *   - Some attribute magic.
 *   - Update alias analysis.
 *   - Update call graph info.
 * @return New function that replaced the old one. Function type cannot be
 * changed in situ -> we create an entirely new function with the desired type.
 */
FunctionPair modifyFunction(
		Config* config,
		llvm::Function* fnc,
		llvm::Type* ret,
		std::vector<llvm::Type*> args,
		bool isVarArg,
		const std::map<llvm::ReturnInst*, llvm::Value*>& rets2vals,
		const std::map<llvm::CallInst*, std::vector<llvm::Value*>>& calls2vals,
		llvm::Value* retVal,
		const std::vector<llvm::Value*>& argStores,
		const std::vector<std::string>& argNames)
{
	auto* cf = config->getConfigFunction(fnc);

	if (!FunctionType::isValidReturnType(ret))
	{
		ret = Abi::getDefaultType(fnc->getParent());
	}
	for (Type*& t : args)
	{
		if (!FunctionType::isValidArgumentType(t))
		{
			t = Abi::getDefaultType(fnc->getParent());
		}
	}

	// New function type.
	//
	ret = ret ? ret : fnc->getReturnType();
	llvm::FunctionType* newFncType = llvm::FunctionType::get(
			ret,
			args,
			isVarArg);

	// New function.
	//
	Function *nf = nullptr;
	if (newFncType == fnc->getFunctionType())
	{
		nf = fnc;
	}
	else
	{
		nf = Function::Create(
				newFncType,
				fnc->getLinkage(),
				fnc->getName());
		nf->copyAttributesFrom(fnc);

		fnc->getParent()->getFunctionList().insert(fnc->getIterator(), nf);
		nf->takeName(fnc);
		nf->getBasicBlockList().splice(nf->begin(), fnc->getBasicBlockList());
	}

	// Rename arguments.
	//
	auto nIt = argNames.begin();
	auto oi = fnc->arg_begin();
	auto oie = fnc->arg_end();
	std::size_t idx = 1;
	for (auto i = nf->arg_begin(), e = nf->arg_end(); i != e; ++i, ++idx)
	{
		if (nIt != argNames.end() && !nIt->empty())
		{
			i->setName(*nIt);
		}
		else
		{
			if (oi != oie && !oi->getName().empty())
			{
				if (nf != fnc)
				{
					i->setName(oi->getName());
				}
			}
			else
			{
				std::string n = "arg" + std::to_string(idx);
				i->setName(n);
			}
		}

		if (nIt != argNames.end())
		{
			++nIt;
		}
		if (oi != oie)
		{
			++oi;
		}
	}

	// Set arguments to config function.
	//
	if (cf)
	{
		cf->parameters.clear();
		std::size_t idx = 0;
		for (auto i = nf->arg_begin(), e = nf->arg_end(); i != e; ++i, ++idx)
		{
			std::string n = i->getName();
			assert(!n.empty());
			auto s = retdec::config::Storage::undefined();
			retdec::config::Object arg(n, s);
			if (argNames.size() > idx)
			{
				arg.setRealName(argNames[idx]);
				arg.setIsFromDebug(true);
			}
			arg.type.setLlvmIr(llvmObjToString(i->getType()));

			// TODO: hack, we need to propagate type's wide string property.
			// but how?
			//
			if (i->getType()->isPointerTy()
					&& i->getType()->getPointerElementType()->isIntegerTy()
					&& retdec::utils::contains(nf->getName(), "wprintf"))
			{
				arg.type.setIsWideString(true);
			}
			cf->parameters.insert(arg);
		}
	}

	// Replace uses of old arguments in function body for new arguments.
	//
	for (auto i = fnc->arg_begin(), e = fnc->arg_end(), i2 = nf->arg_begin();
			i != e; ++i, ++i2)
	{
		auto* a1 = &(*i);
		auto* a2 = &(*i2);
		if (a1->getType() == a2->getType())
		{
			a1->replaceAllUsesWith(a2);
		}
		else
		{
			auto uIt = i->user_begin();
			while (uIt != i->user_end())
			{
				Value* u = *uIt;
				uIt++;

				auto* inst = dyn_cast<Instruction>(u);
				assert(inst && "we need an instruction here");

				auto* conv = IrModifier::convertValueToType(a2, a1->getType(), inst);
				inst->replaceUsesOfWith(a1, conv);
			}
		}

		a2->takeName(a1);
	}

	// Store arguments into allocated objects (stacks, registers) at the
	// beginning of function body.
	//
	auto asIt = argStores.begin();
	auto asEndIt = argStores.end();
	for (auto aIt = nf->arg_begin(), eIt = nf->arg_end();
			aIt != eIt && asIt != asEndIt;
			++aIt, ++asIt)
	{
		auto* a = &(*aIt);
		auto* v = *asIt;

		assert(v->getType()->isPointerTy());
		auto* conv = IrModifier::convertValueToType(
				a,
				v->getType()->getPointerElementType(),
				&nf->front().front());

		auto* s = new StoreInst(conv, v);

		if (auto* alloca = dyn_cast<AllocaInst>(v))
		{
			s->insertAfter(alloca);
		}
		else
		{
			if (conv == a)
			{
				s->insertBefore(&nf->front().front());
			}
			else
			{
				s->insertAfter(cast<Instruction>(conv));
			}
		}
	}

	// Update returns in function body.
	//
//	if (nf->getReturnType() != fnc->getReturnType())
	{
		auto it = inst_begin(nf);
		auto eit = inst_end(nf);
		while (it != eit)
		{
			auto* i = &(*it);
			++it;

			if (auto* retI = dyn_cast<ReturnInst>(i))
			{
				auto fIt = rets2vals.find(retI);
				if (nf->getReturnType()->isVoidTy())
				{
					ReturnInst::Create(nf->getContext(), nullptr, retI);
					retI->eraseFromParent();
				}
				else if (fIt != rets2vals.end())
				{
					auto* conv = IrModifier::convertValueToType(
							fIt->second,
							nf->getReturnType(),
							retI);
					if (auto* val = retI->getReturnValue())
					{
						retI->replaceUsesOfWith(val, conv);
					}
					else
					{
						ReturnInst::Create(nf->getContext(), conv, retI);
						retI->eraseFromParent();
					}
				}
				else if (auto* val = retI->getReturnValue())
				{
					auto* conv = IrModifier::convertValueToType(
							val,
							nf->getReturnType(),
							retI);
					retI->replaceUsesOfWith(val, conv);
				}
				else
				{
					auto* conv = IrModifier::convertConstantToType(
							config->getGlobalDummy(),
							nf->getReturnType());
					ReturnInst::Create(nf->getContext(), conv, retI);
					retI->eraseFromParent();
				}
			}
		}
	}

	// Update function users (calls, etc.).
	//
	auto uIt = fnc->user_begin();
	while (uIt != fnc->user_end())
	{
		Value* u = *uIt;
		uIt++;

		if (CallInst* call = dyn_cast<CallInst>(u))
		{
			std::vector<Value*> args;

			auto fIt = calls2vals.find(call);
			if (fIt != calls2vals.end())
			{
				auto vIt = fIt->second.begin();
				for (auto fa = nf->arg_begin(); fa != nf->arg_end(); ++fa)
				{
					if (vIt != fIt->second.end())
					{
						auto* conv = IrModifier::convertValueToType(
								*vIt,
								fa->getType(),
								call);
						args.push_back(conv);
						++vIt;
					}
					else
					{
						auto* conv = IrModifier::convertValueToType(
								config->getGlobalDummy(),
								fa->getType(),
								call);
						args.push_back(conv);
					}
				}
				while (isVarArg && vIt != fIt->second.end())
				{
					args.push_back(*vIt);
					++vIt;
				}
			}
			else
			{
				unsigned ai = 0;
				unsigned ae = call->getNumArgOperands();
				for (auto fa = nf->arg_begin(); fa != nf->arg_end(); ++fa)
				{
					if (ai != ae)
					{
						auto* conv = IrModifier::convertValueToType(
								call->getArgOperand(ai),
								fa->getType(),
								call);
						args.push_back(conv);
						++ai;
					}
					else
					{
						auto* conv = IrModifier::convertValueToType(
								config->getGlobalDummy(),
								fa->getType(),
								call);
						args.push_back(conv);
					}
				}
			}
			assert(isVarArg || args.size() == nf->arg_size());

			auto* nc = _modifyCallInst(
					call,
					nf,
					args);

			if (!ret->isVoidTy() && retVal)
			{
				auto* n = nc->getNextNode();
				assert(n);
				auto* conv = IrModifier::convertValueToType(
						nc,
						retVal->getType()->getPointerElementType(),
						n);
				new StoreInst(conv, retVal, n);
			}
		}
		else if (StoreInst* s = dyn_cast<StoreInst>(u))
		{
			auto* conv = IrModifier::convertValueToType(nf, fnc->getType(), s);
			s->replaceUsesOfWith(fnc, conv);
		}
		else if (auto* c = dyn_cast<CastInst>(u))
		{
			auto* conv = IrModifier::convertValueToType(nf, fnc->getType(), c);
			c->replaceUsesOfWith(fnc, conv);
		}
		else if (isa<Constant>(u))
		{
			// will be replaced by replaceAllUsesWith()
		}
		else
		{
			// we could do generic IrModifier::convertValueToType() and hope for the best,
			// but we would prefer to know about such cases -> throw assert.
			errs() << "unhandled use : " << *u << "\n";
			assert(false && "unhandled use");
		}
	}

	if (nf->getType() != fnc->getType())
	{
		auto* conv = IrModifier::convertConstantToType(nf, fnc->getType());
		fnc->replaceAllUsesWith(conv);
	}

	// Even when fnc->user_empty() && fnc->use_empty() it still fails here.
	// No ide why.
//	fnc->eraseFromParent();

	return {nf, cf};
}

/**
 * @return New argument -- function type cannot be changed in situ, we created
 * an entirely new fuction with desired argument type.
 */
llvm::Argument* modifyFunctionArgumentType(
		Config* config,
		llvm::Argument* arg,
		llvm::Type* type)
{
	auto* f = arg->getParent();
	std::vector<Type*> args;
	for (auto& a : f->args())
	{
		args.push_back(&a == arg ? type : a.getType());
	}
	auto* nf = modifyFunction(config, f, f->getReturnType(), args).first;
	auto& al = nf->getArgumentList();
	std::size_t i = 0;
	for (auto& a : al)
	{
		if (i == arg->getArgNo())
		{
			return &a;
		}
		++i;
	}
	return nullptr;
}

} // namespace bin2llvmir
} // namespace retdec
