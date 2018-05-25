/**
* @file tests/bin2llvmir/utils/tests/ir_modifier_tests.cpp
* @brief Tests for the @c IrModifier utils module.
* @copyright (c) 2017 Avast Software, licensed under the MIT license
*/

#include <gtest/gtest.h>

#include "retdec/bin2llvmir/utils/ir_modifier.h"
#include "bin2llvmir/utils/llvmir_tests.h"

using namespace ::testing;
using namespace llvm;

namespace retdec {
namespace bin2llvmir {
namespace tests {

/**
 * @brief Tests for the @c IrModifier module.
 */
class IrModifierTests : public LlvmIrTests
{

};

//
// convertValueToType()
//

TEST_F(IrModifierTests, convertValueToTypeFloatToInt32)
{
	parseInput(R"(
		define void @fnc() {
			%a = fadd float 1.0, 2.0
			ret void
		}
	)");
	auto* a = getValueByName("a");
	auto* b = getNthInstruction<ReturnInst>();

	IrModifier::convertValueToType(a, Type::getInt32Ty(context), b);

	std::string exp = R"(
		define void @fnc() {
			%a = fadd float 1.0, 2.0
			%1 = bitcast float %a to i32
			ret void
		}
	)";
	checkModuleAgainstExpectedIr(exp);
}

TEST_F(IrModifierTests, convertValueToTypeInt32ToFloat)
{
	parseInput(R"(
		define void @fnc() {
			%a = add i32 1, 2
			ret void
		}
	)");
	auto* a = getValueByName("a");
	auto* b = getNthInstruction<ReturnInst>();

	IrModifier::convertValueToType(a, Type::getFloatTy(context), b);

	std::string exp = R"(
		define void @fnc() {
			%a = add i32 1, 2
			%1 = bitcast i32 %a to float
			ret void
		}
	)";
	checkModuleAgainstExpectedIr(exp);
}

TEST_F(IrModifierTests, convertValueToTypeFunctionToPointer)
{
	parseInput(R"(
		declare void @import()
		define void @fnc() {
			ret void
		}
	)");
	auto* import = getValueByName("import");
	auto* r = getNthInstruction<ReturnInst>();
	auto* i32 = Type::getInt32Ty(context);
	auto* t = PointerType::get(
			FunctionType::get(
					i32,
					{i32, i32},
					false), // isVarArg
			0);

	IrModifier::convertValueToType(import, t, r);

	std::string exp = R"(
		declare void @import()
		define void @fnc() {
			%1 = bitcast void()* @import to i32(i32, i32)*
			ret void
		}
	)";
	checkModuleAgainstExpectedIr(exp);
}

//
// convertValueToAfter()
//

TEST_F(IrModifierTests, convertValueToTypeAfterInt32ToDouble)
{
	parseInput(R"(
		define void @fnc() {
			%a = add i32 1, 2
			%b = add i32 1, 2
			ret void
		}
	)");
	auto* a = getValueByName("a");
	auto* b = getInstructionByName("b");

	IrModifier::convertValueToTypeAfter(a, Type::getDoubleTy(context), b);

	std::string exp = R"(
		define void @fnc() {
			%a = add i32 1, 2
			%b = add i32 1, 2
			%1 = sext i32 %a to i64
			%2 = bitcast i64 %1 to double
			ret void
		}
	)";
	checkModuleAgainstExpectedIr(exp);
}

TEST_F(IrModifierTests, convertValueToTypeAfterItselfInt32ToDouble)
{
	parseInput(R"(
		define void @fnc() {
			%a = add i32 1, 2
			ret void
		}
	)");
	auto* a = getInstructionByName("a");

	IrModifier::convertValueToTypeAfter(a, Type::getDoubleTy(context), a);

	std::string exp = R"(
		define void @fnc() {
			%a = add i32 1, 2
			%1 = sext i32 %a to i64
			%2 = bitcast i64 %1 to double
			ret void
		}
	)";
	checkModuleAgainstExpectedIr(exp);
}

} // namespace tests
} // namespace bin2llvmir
} // namespace retdec
