/**
* @file src/bin2llvmir/optimizations/local_vars/local_vars.cpp
* @brief Register localization.
* @copyright (c) 2017 Avast Software, licensed under the MIT license
*/

#include <cassert>
#include <iomanip>
#include <iostream>

#include <llvm/IR/Instruction.h>
#include <llvm/IR/Instructions.h>
#include <llvm/IR/InstIterator.h>

#include "retdec/bin2llvmir/utils/llvm.h"
#include "retdec/utils/string.h"
#include "retdec/bin2llvmir/optimizations/local_vars/local_vars.h"
#include "retdec/bin2llvmir/utils/debug.h"
#include "retdec/bin2llvmir/utils/ir_modifier.h"

using namespace retdec::utils;
using namespace llvm;

#define debug_enabled false

namespace retdec {
namespace bin2llvmir {

char LocalVars::ID = 0;

static RegisterPass<LocalVars> X(
		"local-vars",
		"Register localization optimization",
		false, // Only looks at CFG
		false // Analysis Pass
);

LocalVars::LocalVars() :
		ModulePass(ID)
{

}

bool canBeLocalized(const Definition* def)
{
	for (auto* u : def->uses)
	{
		if (u->defs.size() > 1)
		{
			return false;
		}
	}
	return !def->uses.empty();
}

/**
 * @return @c True if al least one instruction was (un)volatilized.
 *         @c False otherwise.
 */
bool LocalVars::runOnModule(Module& M)
{
	if (!ConfigProvider::getConfig(&M, config))
	{
		LOG << "[ABORT] config file is not available\n";
		return false;
	}

	ReachingDefinitionsAnalysis RDA;
	RDA.runOnModule(M, config);

	for (Function &F : M)
	for (auto it = inst_begin(&F), eIt = inst_end(&F); it != eIt; ++it)
	{
		Instruction& I = *it;

		if (CallInst* call = dyn_cast<CallInst>(&I))
		{
			if (call->getCalledFunction() == nullptr)
			{
				continue;
			}

			for (auto& a : call->arg_operands())
			{
				auto* aa = dyn_cast_or_null<Instruction>(llvm_utils::skipCasts(a));
				if (aa == nullptr)
				{
					continue;
				}
				auto* use = RDA.getUse(aa);
				if (use == nullptr || use->defs.size() != 1)
				{
					continue;
				}
				auto* d = *use->defs.begin();
				if (a->getType()->isFloatingPointTy()
						&& !d->getSource()->getType()->isFloatingPointTy()
						&& canBeLocalized(d))
				{
					IrModifier::localize(d->def, d->uses, false);
				}
				else if (config->isRegister(d->getSource()) && canBeLocalized(d))
				{
					IrModifier::localize(d->def, d->uses, false);
				}
			}
		}
		else if (ReturnInst* ret = dyn_cast<ReturnInst>(&I))
		{
			auto* a = llvm_utils::skipCasts(ret->getReturnValue());
			if (a == nullptr)
				continue;
			if (auto* l = dyn_cast<LoadInst>(a))
			{
				auto* use = RDA.getUse(l);
				if (use == nullptr || use->defs.size() != 1)
				{
					continue;
				}
				auto* d = *use->defs.begin();
				if (!config->isRegister(d->getSource()))
				{
					continue;
				}
				if (canBeLocalized(d))
				{
					IrModifier::localize(d->def, d->uses, false);
				}
			}
		}
		else if (StoreInst* s = dyn_cast<StoreInst>(&I))
		{
			if (!config->isRegister(s->getPointerOperand()))
			{
				continue;
			}

			auto* d = RDA.getDef(s);
			if (d == nullptr)
			{
				continue;
			}

			auto* vo = llvm_utils::skipCasts(s->getValueOperand());
			if (isa<CallInst>(vo) && canBeLocalized(d))
			{
				IrModifier::localize(d->def, d->uses, false);
			}
			else if (isa<Argument>(vo) && canBeLocalized(d))
			{
				IrModifier::localize(d->def, d->uses, false);
			}
		}
	}

	return false;
}

} // namespace bin2llvmir
} // namespace retdec
