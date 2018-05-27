/**
 * @file src/bin2llvmir/analyses/symbolic_tree.cpp
 * @brief Construction of symbolic tree from the given node.
 * @copyright (c) 2017 Avast Software, licensed under the MIT license
 */

#include <iostream>
#include <ostream>
#include <sstream>

#include <llvm/IR/Constants.h>
#include <llvm/IR/LLVMContext.h>
#include <llvm/IR/Operator.h>

#include "retdec/utils/string.h"
#include "retdec/bin2llvmir/analyses/symbolic_tree.h"
#include "retdec/bin2llvmir/utils/llvm.h"
#include "retdec/bin2llvmir/providers/asm_instruction.h"
#include "retdec/bin2llvmir/providers/config.h"
#include "retdec/bin2llvmir/utils/debug.h"

using namespace llvm;

#define debug_enabled false

namespace retdec {
namespace bin2llvmir {

Abi* SymbolicTree::_abi = nullptr;
bool SymbolicTree::_val2valUsed = false;
bool SymbolicTree::_trackThroughAllocaLoads = true;
bool SymbolicTree::_trackThroughGeneralRegisterLoads = true;
bool SymbolicTree::_trackOnlyFlagRegisters = false;

/**
 * No ReachingDefinitionsAnalysis -> on-demand UseDef/DefUse chains are used.
 */
SymbolicTree::SymbolicTree(
		llvm::Value* v,
		unsigned maxNodeLevel)
		:
		SymbolicTree(nullptr, v, nullptr, maxNodeLevel)
{

}

SymbolicTree::SymbolicTree(
		ReachingDefinitionsAnalysis& rda,
		llvm::Value* v,
		unsigned maxNodeLevel)
		:
		SymbolicTree(&rda, v, nullptr, maxNodeLevel)
{

}

SymbolicTree::SymbolicTree(
		ReachingDefinitionsAnalysis& rda,
		llvm::Value* v,
		std::map<llvm::Value*, llvm::Value*>* val2val,
		unsigned maxNodeLevel)
		:
		SymbolicTree(&rda, v, val2val, maxNodeLevel)
{

}

/**
 * Them main "public" ctor -- it is not really public, but all public ctors
 * end up here and it does all the work.
 */
SymbolicTree::SymbolicTree(
		ReachingDefinitionsAnalysis* rda,
		llvm::Value* v,
		std::map<llvm::Value*, llvm::Value*>* val2val,
		unsigned maxNodeLevel)
		:
		value(v)
{
	_val2valUsed = false;

	if (val2val)
	{
		auto fIt = val2val->find(value);
		if (fIt != val2val->end())
		{
			value = fIt->second;
			_val2valUsed = true;
			return;
		}
	}

	if (getLevel() == maxNodeLevel)
	{
		return;
	}

	std::unordered_set<Value*> processed;
	expandNode(rda, val2val, maxNodeLevel, processed);
}

SymbolicTree::SymbolicTree(
		ReachingDefinitionsAnalysis* rda,
		llvm::Value* v,
		llvm::Value* u,
		std::unordered_set<llvm::Value*>& processed,
		unsigned nodeLevel,
		unsigned maxNodeLevel,
		std::map<llvm::Value*, llvm::Value*>* val2val)
		:
		value(v),
		user(u),
		_level(nodeLevel)
{
	if (val2val)
	{
		auto fIt = val2val->find(value);
		if (fIt != val2val->end())
		{
			value = fIt->second;
			_val2valUsed = true;
			return;
		}
	}

	if (getLevel() == maxNodeLevel)
	{
		return;
	}

	expandNode(rda, val2val, maxNodeLevel, processed);
}

unsigned SymbolicTree::getLevel() const
{
	return _level;
}

SymbolicTree& SymbolicTree::operator=(SymbolicTree&& other)
{
	if (this != &other)
	{
		value = other.value;
		user = other.user;
		// Do NOT use `ops = std::move(other.ops);` to allow use like
		// `*this = ops[0];`. Use std::swap() instead.
		std::swap(ops, other.ops);
	}
	return *this;
}

bool SymbolicTree::operator==(const SymbolicTree& o) const
{
	if (ops != o.ops)
	{
		return false;
	}
	if (isa<Constant>(value) && isa<Constant>(o.value))
	{
		return value == o.value;
	}
	else if (isa<Instruction>(value) && isa<Instruction>(o.value))
	{
		auto* i1 = cast<Instruction>(value);
		auto* i2 = cast<Instruction>(o.value);
		return i1->isSameOperationAs(i2);
	}
	else
	{
		return false;
	}
}

bool SymbolicTree::operator!=(const SymbolicTree& o) const
{
	return !(*this == o);
}

void SymbolicTree::expandNode(
		ReachingDefinitionsAnalysis* RDA,
		std::map<llvm::Value*, llvm::Value*>* val2val,
		unsigned maxNodeLevel,
		std::unordered_set<llvm::Value*>& processed)
{
	if (RDA && RDA->wasRun())
	{
		auto fIt = processed.find(value);
		if (fIt != processed.end())
		{
			return;
		}
	}

	if (User* U = dyn_cast<User>(value))
	{
		processed.insert(value);
		Instruction *I = dyn_cast<Instruction>(value);

		if (auto* l = dyn_cast<LoadInst>(value))
		{
			if (!_trackThroughAllocaLoads
					&& isa<AllocaInst>(l->getPointerOperand()))
			{
				return;
			}

			if (_trackOnlyFlagRegisters
					&& _abi
					&& _abi->isRegister(l->getPointerOperand())
					&& !_abi->isFlagRegister(l->getPointerOperand()))
			{
				return;
			}

			if (!_trackThroughGeneralRegisterLoads
					&& _abi
					&& _abi->isGeneralPurposeRegister(l->getPointerOperand()))
			{
				return;
			}

			if (RDA && RDA->wasRun())
			{
				auto defs = RDA->defsFromUse(I);
				for (auto* d : defs)
				{
					ops.emplace_back(
							RDA,
							d->def,
							I,
							processed,
							getLevel() + 1,
							maxNodeLevel,
							val2val);
				}
			}
			else
			{
				auto defs = ReachingDefinitionsAnalysis::defsFromUse_onDemand(I);
				for (auto* d : defs)
				{
					ops.emplace_back(
							RDA,
							d,
							I,
							processed,
							getLevel() + 1,
							maxNodeLevel,
							val2val);
				}
			}

			if (ops.empty())
			{
				ops.emplace_back(
						RDA,
						l->getPointerOperand(),
						l,
						processed,
						getLevel() + 1,
						maxNodeLevel,
						val2val);
			}
		}
		else if (isa<StoreInst>(value))
		{
			ops.emplace_back(
					RDA,
					I->getOperand(0),
					I,
					processed,
					getLevel() + 1,
					maxNodeLevel,
					val2val);
		}
		else if (isa<AllocaInst>(value)
				|| isa<CallInst>(value)
				|| (_abi
						&& _abi->isRegister(value)
						&& !_abi->isStackPointerRegister(value)
						&& !(_abi->isMips() && value == _abi->getRegister(MIPS_REG_ZERO))
						&& !(_abi->isMips() && value == _abi->getRegister(MIPS_REG_GP))
						&& !(_abi->isMips() && value == _abi->getRegister(MIPS_REG_T9)))
				)
		{
			// nothing
		}
		else
		{
			for (unsigned i = 0; i < U->getNumOperands(); ++i)
			{
				ops.emplace_back(
						RDA,
						U->getOperand(i),
						U,
						processed,
						getLevel() + 1,
						maxNodeLevel,
						val2val);
			}
		}
	}
}

void SymbolicTree::simplifyNode(Config* config)
{
	_simplifyNode(config);
	fixLevel();
}

void SymbolicTree::_simplifyNode(Config* config)
{
	if (ops.empty())
	{
		return;
	}

	for (auto &o : ops)
	{
		o._simplifyNode(config);
	}

	if (isa<LoadInst>(value) && ops.size() > 1)
	{
		bool allEq = true;

		SymbolicTree& op0 = ops[0];
		for (auto &o : ops)
		{
			if (op0 != o)
			{
				allEq = false;
				break;
			}
		}

		if (allEq)
		{
			ops.erase(ops.begin()+1, ops.end());
		}
	}

	if (isa<CastInst>(value))
	{
		*this = std::move(ops[0]);
	}
	else if (ConstantExpr* ce = dyn_cast<ConstantExpr>(value))
	{
		if (ce->isCast())
			*this = std::move(ops[0]);
	}
	else if (isa<StoreInst>(value))
	{
		*this = std::move(ops[0]);
	}
	// MIPS, use function address for t9.
	//
	else if (config->getConfig().architecture.isMipsOrPic32()
			&& isa<LoadInst>(value)
			&& ops.size() == 1
			&& isa<GlobalVariable>(ops[0].value)
			&& cast<GlobalVariable>(ops[0].value)->getName() == "t9"
			&& ops[0].ops.size() == 1
			&& isa<ConstantInt>(ops[0].ops[0].value)
			&& cast<ConstantInt>(ops[0].ops[0].value)->isZero())
	{
		auto* l = cast<LoadInst>(value);
		auto addr = AsmInstruction::getFunctionAddress(l->getFunction());

		auto* ci = cast<ConstantInt>(ops[0].ops[0].value);
		ops[0].ops[0].value = ConstantInt::get(ci->getType(), addr);
		*this = std::move(ops[0].ops[0]);
	}
	// >|  %addr = load @gv_1
	//     >|  @gv_1 = value
	// =>
	// >|  value
	//
	else if (isa<LoadInst>(value)
			&& ops.size() == 1
			&& isa<GlobalVariable>(ops[0].value)
			&& ops[0].value == dyn_cast<LoadInst>(value)->getOperand(0)
			&& ops[0].ops.size() == 1)
	{
		*this = std::move(ops[0].ops[0]);
	}
	else if (auto* l = dyn_cast<LoadInst>(value))
	{
			auto* ptr = l->getPointerOperand();
			ptr = llvm_utils::skipCasts(ptr);
			if (isa<AllocaInst>(ptr) || isa<GlobalVariable>(ptr))
			{
					if (ops.size() == 1)
					{
							*this = std::move(ops[0]);
					}
			}
	}
	else if (ops.size() == 2
			&& isa<ConstantInt>(ops[0].value)
			&& isa<ConstantInt>(ops[1].value))
	{
		ConstantInt* op1 = cast<ConstantInt>(ops[0].value);
		ConstantInt* op2 = cast<ConstantInt>(ops[1].value);

		if (isa<AddOperator>(value))
		{
			value = ConstantInt::get(
					op1->getType(),
					op1->getSExtValue() + op2->getSExtValue());
			ops.clear();
		}
		else if (isa<SubOperator>(value))
		{
			value = ConstantInt::get(
					op1->getType(),
					op1->getSExtValue() - op2->getSExtValue());
			ops.clear();
		}
		else if (auto* op = dyn_cast<BinaryOperator>(value))
		{
			if (op->getOpcode() == BinaryOperator::Or)
			{
				value = ConstantInt::get(
						op1->getType(),
						op1->getSExtValue() | op2->getSExtValue());
				ops.clear();
			}
			else if (op->getOpcode() == BinaryOperator::And)
			{
				value = ConstantInt::get(
						op1->getType(),
						op1->getSExtValue() & op2->getSExtValue());
				ops.clear();
			}
		}
	}
	else if (ops.size() == 2
			&& isa<GlobalVariable>(ops[0].value)
			&& ops[0].user
			&& !isa<LoadInst>(ops[0].user)
			&& isa<ConstantInt>(ops[1].value))
	{
		GlobalVariable* op1 = cast<GlobalVariable>(ops[0].value);
		ConstantInt* op2 = cast<ConstantInt>(ops[1].value);

		if (config)
		{
			auto* cgv = config->getConfigGlobalVariable(op1);
			if (isa<AddOperator>(value) && cgv)
			{
				value = ConstantInt::get(
						op2->getType(),
						cgv->getStorage().getAddress() + op2->getSExtValue());
				ops.clear();
			}
		}
	}
	// TODO: this is to specific, make it more general to catch more patterns.
	//
	// >|   %u3_401566 = add i32 %u2_401566, 8
	// >|   %phitmp_401560 = add i32 %u1_401560, -4
	//        >| @esp = internal global i32 0
	//        >| i32 -4
	// >| i32 8
	//
	// >|   %u3_401566 = add i32 %u2_401566, 8
	// >| @esp = internal global i32 0
	// >| i32 4
	//
	else if (ops.size() == 2
			&& isa<AddOperator>(value)
			&& isa<AddOperator>(ops[0].value)
			&& ops[0].ops.size() == 2
			&& isa<ConstantInt>(ops[0].ops[1].value)
			&& isa<ConstantInt>(ops[1].value))
	{
		ConstantInt* ci1 = cast<ConstantInt>(ops[0].ops[1].value);
		ConstantInt* ci2 = cast<ConstantInt>(ops[1].value);

		ops[0] = std::move(ops[0].ops[0]);
		ops[1].value = ConstantInt::get(
				ci1->getType(),
				ci1->getSExtValue() + ci2->getSExtValue());
	}
	else if (ops.size() == 2
			&& (isa<AddOperator>(value) || isa<SubOperator>(value))
			&& isa<ConstantInt>(ops[1].value)
			&& cast<ConstantInt>(ops[1].value)->isZero())
	{
		*this = std::move(ops[0]);
	}

	// Move Constants from ops[0] to ops[1].
	//
	auto* i = dyn_cast<Instruction>(value);
	if (i && (i->isCommutative() || isa<LoadInst>(i))
			&& ops.size() == 2
			&& isa<Constant>(ops[0].value)
			&& !isa<Constant>(ops[1].value))
	{
		std::swap(ops[0], ops[1]);
	}
}

/**
 * If at address 33888 in @a image is value 76092 then transform:
 * >|   %u6_83f0 = load i32, i32* inttoptr (i32 33888 to i32*), align 32
 *        >| i32 33888
 * Into:
 * >|   76092
 *
 */
void SymbolicTree::solveMemoryLoads(FileImage* image)
{
	for (auto &o : ops)
	{
		o.solveMemoryLoads(image);
	}

	auto* t = dyn_cast<IntegerType>(value->getType());
	if (isa<LoadInst>(value)
			&& t
			&& ops.size() == 1
			&& isa<ConstantInt>(ops[0].value))
	{
		auto* ci = cast<ConstantInt>(ops[0].value);
		auto* seg = image->getImage()->getSegmentFromAddress(ci->getZExtValue());
		auto* sec = seg ? seg->getSecSeg() : nullptr;
		if (seg && (sec == nullptr || !sec->isBss()))
		{
			auto* res = image->getConstantInt(t, ci->getZExtValue());
			if (res)
			{
				value = res;
				ops.clear();
			}
		}
	}
}

SymbolicTree* SymbolicTree::getMaxIntValue()
{
	SymbolicTree* max = nullptr;

	if (!isa<GlobalVariable>(value))
	for (auto &o : ops)
	{
		auto* m = o.getMaxIntValue();
		auto* mc = m ? dyn_cast_or_null<ConstantInt>(m->value) : nullptr;
		auto* maxc = max ? dyn_cast_or_null<ConstantInt>(max->value) : nullptr;
		if (max == nullptr || maxc == nullptr)
		{
			max = m;
		}
		else if (m && mc && mc->getSExtValue() > maxc->getSExtValue())
		{
			max = m;
		}
	}

	if (auto* c = dyn_cast<ConstantInt>(value))
	{
		auto* maxc = max ? dyn_cast_or_null<ConstantInt>(max->value) : nullptr;
		if (max == nullptr || maxc == nullptr)
		{
			max = this;
		}
		else if (c->getSExtValue() > maxc->getSExtValue())
		{
			max = this;
		}
	}

	return max;
}

std::string SymbolicTree::print(unsigned indent) const
{
	std::stringstream out;
	if (Function* F = dyn_cast<Function>(value))
		out << retdec::utils::getIndentation(indent) << ">| "
			<< F->getName().str() << std::endl;
	else
		out << retdec::utils::getIndentation(indent) << ">| "
			<< llvmObjToString(value) << std::endl;

	++indent;
	for (const auto& o : ops)
		out << o.print(indent);
	return out.str();
}

std::ostream& operator<<(std::ostream& out, const SymbolicTree& s)
{
	out << "-----------------------------------------------" << std::endl;
	out << s.print(0);
	out << "-----------------------------------------------" << std::endl;
	return out;
}

/**
 * @return Tree nodes linearized using a pre-order traversal.
 * @note You can change the nodes (they are not constant) but keep in mind
 * that your changes might make the vector inconsistent -- i.e. changes you
 * make are not reflected in it. For example, if you change children of some
 * node and then continue to iterate over the vector, vector elements will
 * not be the real children after the change.
 * Post-order vector is much more suitable for modifications.
 */
std::vector<SymbolicTree*> SymbolicTree::getPreOrder() const
{
	std::vector<SymbolicTree*> ret;
	_getPreOrder(ret);
	return ret;
}

/**
 * @return Tree nodes linearized using a post-order traversal.
 * @note See note for @c getPreOrder(). The same holds here -- you may damage
 * vector's consistency if you make changes to nodes as you iterate over them.
 * However, thanks to the bottom-up nature of post-order traversal, this may
 * not be a problem if you modify only the actual node and its children -- they
 * were already iterated over.
 */
std::vector<SymbolicTree*> SymbolicTree::getPostOrder() const
{
	std::vector<SymbolicTree*> ret;
	_getPostOrder(ret);
	return ret;
}

/**
 * @return Tree nodes linearized using a level-order traversal.
 */
std::vector<SymbolicTree*> SymbolicTree::getLevelOrder() const
{
	std::vector<SymbolicTree*> ret;
	_getPreOrder(ret);

	std::stable_sort(ret.begin(), ret.end(),
			[](const SymbolicTree* a, const SymbolicTree* b) -> bool
			{
				return a->getLevel() < b->getLevel();
			});

	return ret;
}

void SymbolicTree::_getPreOrder(std::vector<SymbolicTree*>& res) const
{
	res.emplace_back(const_cast<SymbolicTree*>(this));
	for (auto &o : ops)
	{
		o._getPreOrder(res);
	}
}

void SymbolicTree::_getPostOrder(std::vector<SymbolicTree*>& res) const
{
	for (auto &o : ops)
	{
		o._getPostOrder(res);
	}
	res.emplace_back(const_cast<SymbolicTree*>(this));
}

void SymbolicTree::fixLevel(unsigned level)
{
	if (level == 0)
	{
		level = _level;
	}
	else
	{
		_level = level;
	}
	for (auto &o : ops)
	{
		o.fixLevel(level + 1);
	}
}

bool SymbolicTree::isNullary() const
{
	return ops.size() == 0;
}

bool SymbolicTree::isUnary() const
{
	return ops.size() == 1;
}

bool SymbolicTree::isBinary() const
{
	return ops.size() == 2;
}

bool SymbolicTree::isTernary() const
{
	return ops.size() == 3;
}

bool SymbolicTree::isNary(unsigned N) const
{
	return ops.size() == N;
}

//
//==============================================================================
// Static methods.
//==============================================================================
//

bool SymbolicTree::isVal2ValMapUsed()
{
	return _val2valUsed;
}

void SymbolicTree::setAbi(Abi* abi)
{
	_abi = abi;
}

void SymbolicTree::setToDefaultConfiguration()
{
	_trackThroughAllocaLoads = true;
	_trackThroughGeneralRegisterLoads = true;
	_trackOnlyFlagRegisters = false;
}

void SymbolicTree::setTrackThroughAllocaLoads(bool b)
{
	_trackThroughAllocaLoads = b;
}

void SymbolicTree::setTrackThroughGeneralRegisterLoads(bool b)
{
	_trackThroughGeneralRegisterLoads = b;
}

void SymbolicTree::setTrackOnlyFlagRegisters(bool b)
{
	_trackOnlyFlagRegisters = b;
}

} // namespace bin2llvmir
} // namespace retdec
