# coding=utf-8
# Copyright (c) 2015-2021 Vector 35 Inc
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

import ctypes

import binaryninja
from . import _binaryninjacore as core
from . import decorators
from .enums import RegisterValueType, VariableSourceType

class LookupTableEntry(object):
	def __init__(self, from_values, to_value):
		self._from_values = from_values
		self._to_value = to_value

	def __repr__(self):
		return "[%s] -> %#x" % (', '.join(["%#x" % i for i in self.from_values]), self.to_value)

	def __eq__(self, other):
		if not isinstance(other, self.__class__):
			return NotImplemented
		return (self._from_values, self._to_value) == (other._from_values, other._to_value)

	def __ne__(self, other):
		if not isinstance(other, self.__class__):
			return NotImplemented
		return not (self == other)

	def __hash__(self):
		return hash((self._from_values, self._to_value))

	@property
	def from_values(self):
		""" """
		return self._from_values

	@from_values.setter
	def from_values(self, value):
		""" """
		self._from_values = value

	@property
	def to_value(self):
		""" """
		return self._to_value

	@to_value.setter
	def to_value(self, value):
		""" """
		self._to_value = value


class RegisterValue(object):
	def __init__(self, arch = None, value = None, confidence = core.max_confidence):
		self._is_constant = False
		self._value = None
		self._arch = None
		self._reg = None
		self._is_constant = False
		self._offset = None
		if value is None:
			self._type = RegisterValueType.UndeterminedValue
		else:
			self._type = RegisterValueType(value.state)
			if value.state == RegisterValueType.EntryValue:
				self._arch = arch
				if arch is not None:
					self._reg = arch.get_reg_name(value.value)
				else:
					self._reg = value.value
			elif (value.state == RegisterValueType.ConstantValue) or (value.state == RegisterValueType.ConstantPointerValue):
				self._value = value.value
				self._is_constant = True
			elif value.state == RegisterValueType.StackFrameOffset:
				self._offset = value.value
			elif value.state == RegisterValueType.ImportedAddressValue:
				self._value = value.value
		self._confidence = confidence

	def __repr__(self):
		if self._type == RegisterValueType.EntryValue:
			return "<entry %s>" % self._reg
		if self._type == RegisterValueType.ConstantValue:
			return "<const %#x>" % self._value
		if self._type == RegisterValueType.ConstantPointerValue:
			return "<const ptr %#x>" % self._value
		if self._type == RegisterValueType.StackFrameOffset:
			return "<stack frame offset %#x>" % self._offset
		if self._type == RegisterValueType.ReturnAddressValue:
			return "<return address>"
		if self._type == RegisterValueType.ImportedAddressValue:
			return "<imported address from entry %#x>" % self._value
		return "<undetermined>"

	def __hash__(self):
		if self._type in [RegisterValueType.ConstantValue, RegisterValueType.ConstantPointerValue, RegisterValueType.ImportedAddressValue, RegisterValueType.ReturnAddressValue]:
			return hash(self._value)
		elif self.type == RegisterValueType.EntryValue:
			return hash(self._reg)
		elif self._type == RegisterValueType.StackFrameOffset:
			return hash(self._offset)

	def __eq__(self, other):
		if self._type in [RegisterValueType.ConstantValue, RegisterValueType.ConstantPointerValue, RegisterValueType.ImportedAddressValue, RegisterValueType.ReturnAddressValue] and isinstance(other, int):
			return self._value == other
		elif self._type in [RegisterValueType.ConstantValue, RegisterValueType.ConstantPointerValue, RegisterValueType.ImportedAddressValue, RegisterValueType.ReturnAddressValue] and hasattr(other, 'type') and other.type == self._type:
			return self._value == other.value
		elif self._type == RegisterValueType.EntryValue and hasattr(other, "type") and other.type == self._type:
			return self._reg == other.reg
		elif self._type == RegisterValueType.StackFrameOffset and hasattr(other, 'type') and other.type == self._type:
			return self._offset == other.offset
		elif self._type == RegisterValueType.StackFrameOffset and isinstance(other, int):
			return self._offset == other
		return NotImplemented

	def __ne__(self, other):
		if not isinstance(other, self.__class__):
			return NotImplemented
		return not (self == other)

	def _to_api_object(self):
		result = core.BNRegisterValue()
		result.type = self._type
		result._value = 0
		if self._type == RegisterValueType.EntryValue:
			if self._arch is not None:
				result._value = self._arch.get_reg_index(self._reg)
			else:
				result._value = self._reg
		elif (self._type == RegisterValueType.ConstantValue) or (self._type == RegisterValueType.ConstantPointerValue):
			result._value = self._value
		elif self._type == RegisterValueType.StackFrameOffset:
			result._value = self._offset
		elif self._type == RegisterValueType.ImportedAddressValue:
			result._value = self._value
		return result

	@classmethod
	def undetermined(self):
		return RegisterValue()

	@classmethod
	def entry_value(self, arch, reg):
		result = RegisterValue()
		result._type = RegisterValueType.EntryValue
		result._arch = arch
		result._reg = reg
		return result

	@classmethod
	def constant(self, value):
		result = RegisterValue()
		result._type = RegisterValueType.ConstantValue
		result._value = value
		result._is_constant = True
		return result

	@classmethod
	def constant_ptr(self, value):
		result = RegisterValue()
		result._type = RegisterValueType.ConstantPointerValue
		result._value = value
		result._is_constant = True
		return result

	@classmethod
	def stack_frame_offset(self, offset):
		result = RegisterValue()
		result._type = RegisterValueType.StackFrameOffset
		result._offset = offset
		return result

	@classmethod
	def imported_address(self, value):
		result = RegisterValue()
		result._type = RegisterValueType.ImportedAddressValue
		result._value = value
		return result

	@classmethod
	def return_address(self):
		result = RegisterValue()
		result._type = RegisterValueType.ReturnAddressValue
		return result

	@property
	def is_constant(self):
		"""Boolean for whether the RegisterValue is known to be constant (read-only)"""
		return self._is_constant

	@property
	def type(self):
		""":class:`~enums.RegisterValueType` (read-only)"""
		return self._type

	@property
	def arch(self):
		"""Architecture where it exists, None otherwise (read-only)"""
		return self._arch

	@property
	def reg(self):
		"""Register where the Architecture exists, None otherwise (read-only)"""
		return self._reg

	@property
	def value(self):
		"""Value where it exists, None otherwise (read-only)"""
		return self._value

	@property
	def offset(self):
		"""Offset where it exists, None otherwise (read-only)"""
		return self._offset

	@property
	def confidence(self):
		"""Confidence where it exists, None otherwise (read-only)"""
		return self._confidence


class ValueRange(object):
	def __init__(self, start, end, step):
		self._start = start
		self._end = end
		self._step = step

	def __repr__(self):
		if self.step == 1:
			return "<range: %#x to %#x>" % (self.start, self.end)
		return "<range: %#x to %#x, step %#x>" % (self.start, self.end, self.step)

	def __eq__(self, other):
		if not isinstance(other, self.__class__):
			return NotImplemented
		return self.start == other.start and self.end == other.end and self.step == other.step

	def __contains__(self, other):
		if not isinstance(other, int):
			return NotImplemented
		return other in range(self._start, self._end, self._step)

	@property
	def start(self):
		""" """
		return self._start

	@start.setter
	def start(self, value):
		""" """
		self._start = value

	@property
	def end(self):
		""" """
		return self._end

	@end.setter
	def end(self, value):
		""" """
		self._end = value

	@property
	def step(self):
		""" """
		return self._step

	@step.setter
	def step(self, value):
		""" """
		self._step = value


class PossibleValueSet(object):
	"""
	`class PossibleValueSet` PossibleValueSet is used to define possible values
	that a variable can take. It contains methods to instantiate different
	value sets such as Constant, Signed/Unsigned Ranges, etc.
	"""
	def __init__(self, arch = None, value = None):
		if value is None:
			self._type = RegisterValueType.UndeterminedValue
			return
		self._type = RegisterValueType(value.state)
		if value.state == RegisterValueType.EntryValue:
			if arch is None:
				self._reg = value.value
			else:
				self._reg = arch.get_reg_name(value.value)
		elif value.state == RegisterValueType.ConstantValue:
			self._value = value.value
		elif value.state == RegisterValueType.ConstantPointerValue:
			self._value = value.value
		elif value.state == RegisterValueType.StackFrameOffset:
			self._offset = value.value
		elif value.state == RegisterValueType.SignedRangeValue:
			self._offset = value.value
			self._ranges = []
			for i in range(0, value.count):
				start = value.ranges[i].start
				end = value.ranges[i].end
				step = value.ranges[i].step
				if start & (1 << 63):
					start |= ~((1 << 63) - 1)
				if end & (1 << 63):
					end |= ~((1 << 63) - 1)
				self._ranges.append(ValueRange(start, end, step))
		elif value.state == RegisterValueType.UnsignedRangeValue:
			self._offset = value.value
			self._ranges = []
			for i in range(0, value.count):
				start = value.ranges[i].start
				end = value.ranges[i].end
				step = value.ranges[i].step
				self._ranges.append(ValueRange(start, end, step))
		elif value.state == RegisterValueType.LookupTableValue:
			self._table = []
			self._mapping = {}
			for i in range(0, value.count):
				from_list = []
				for j in range(0, value.table[i].fromCount):
					from_list.append(value.table[i].fromValues[j])
					self._mapping[value.table[i].fromValues[j]] = value.table[i].toValue
				self._table.append(LookupTableEntry(from_list, value.table[i].toValue))
		elif (value.state == RegisterValueType.InSetOfValues) or (value.state == RegisterValueType.NotInSetOfValues):
			self._values = set()
			for i in range(0, value.count):
				self._values.add(value.valueSet[i])
		self._count = value.count

	def __repr__(self):
		if self._type == RegisterValueType.EntryValue:
			return "<entry %s>" % self.reg
		if self._type == RegisterValueType.ConstantValue:
			return "<const %#x>" % self.value
		if self._type == RegisterValueType.ConstantPointerValue:
			return "<const ptr %#x>" % self.value
		if self._type == RegisterValueType.StackFrameOffset:
			return "<stack frame offset %#x>" % self._offset
		if self._type == RegisterValueType.SignedRangeValue:
			return "<signed ranges: %s>" % repr(self.ranges)
		if self._type == RegisterValueType.UnsignedRangeValue:
			return "<unsigned ranges: %s>" % repr(self.ranges)
		if self._type == RegisterValueType.LookupTableValue:
			return "<table: %s>" % ', '.join([repr(i) for i in self.table])
		if self._type == RegisterValueType.InSetOfValues:
			return "<in set(%s)>" % '[{}]'.format(', '.join(hex(i) for i in sorted(self.values)))
		if self._type == RegisterValueType.NotInSetOfValues:
			return "<not in set(%s)>" % '[{}]'.format(', '.join(hex(i) for i in sorted(self.values)))
		if self._type == RegisterValueType.ReturnAddressValue:
			return "<return address>"
		return "<undetermined>"

	def __contains__(self, other):
		if self.type in [RegisterValueType.ConstantValue, RegisterValueType.ConstantPointerValue] and isinstance(other, int):
			return self.value == other
		if self.type in [RegisterValueType.ConstantValue, RegisterValueType.ConstantPointerValue] and hasattr(other, "value"):
			return self.value == other.value
		if not isinstance(other, int):
			return NotImplemented
		#Initial implementation only checks numbers, no set logic
		if self.type == RegisterValueType.StackFrameOffset:
			return NotImplemented
		if self.type in [RegisterValueType.SignedRangeValue, RegisterValueType.UnsignedRangeValue]:
			for rng in self.ranges:
				if other in rng:
					return True
			return False
		if self.type == RegisterValueType.InSetOfValues:
			return other in self.values
		if self.type == RegisterValueType.NotInSetOfValues:
			return not other in self.values
		return NotImplemented

	def __eq__(self, other):
		if self.type in [RegisterValueType.ConstantValue, RegisterValueType.ConstantPointerValue] and isinstance(other, int):
			return self.value == other
		if not isinstance(other, self.__class__):
			return NotImplemented
		if self.type in [RegisterValueType.ConstantValue, RegisterValueType.ConstantPointerValue]:
			return self.value == other.value
		elif self.type == RegisterValueType.StackFrameOffset:
			return self.offset == other.offset
		elif self.type in [RegisterValueType.SignedRangeValue, RegisterValueType.UnsignedRangeValue]:
			return self.ranges == other.ranges
		elif self.type in [RegisterValueType.InSetOfValues, RegisterValueType.NotInSetOfValues]:
			return self.values == other.values
		elif self.type == RegisterValueType.UndeterminedValue and hasattr(other, 'type'):
			return self.type == other.type
		else:
			return self == other

	def __ne__(self, other):
		if not isinstance(other, self.__class__):
			return NotImplemented
		return not (self == other)

	def _to_api_object(self):
		result = core.BNPossibleValueSet()
		result.state = RegisterValueType(self.type)
		if self.type == RegisterValueType.UndeterminedValue:
			return result
		elif self.type == RegisterValueType.ConstantValue:
			result.value = self.value
		elif self.type == RegisterValueType.ConstantPointerValue:
			result.value = self.value
		elif self.type == RegisterValueType.StackFrameOffset:
			result.offset = self.value
		elif self.type == RegisterValueType.SignedRangeValue:
			result.offset = self.value
			result.ranges = (core.BNValueRange * self.count)()
			for i in range(0, self.count):
				start = self.ranges[i].start
				end = self.ranges[i].end
				if start & (1 << 63):
					start |= ~((1 << 63) - 1)
				if end & (1 << 63):
					end |= ~((1 << 63) - 1)
				value_range = core.BNValueRange()
				value_range.start = start
				value_range.end = end
				value_range.step = self.ranges[i].step
				result.ranges[i] = value_range
			result.count = self.count
		elif self.type == RegisterValueType.UnsignedRangeValue:
			result.offset = self.value
			result.ranges = (core.BNValueRange * self.count)()
			for i in range(0, self.count):
				value_range = core.BNValueRange()
				value_range.start = self.ranges[i].start
				value_range.end = self.ranges[i].end
				value_range.step = self.ranges[i].step
				result.ranges[i] = value_range
			result.count = self.count
		elif self.type == RegisterValueType.LookupTableValue:
			result.table = []
			result.mapping = {}
			for i in range(self.count):
				from_list = []
				for j in range(0, self.table[i].fromCount):
					from_list.append(self.table[i].fromValues[j])
					result.mapping[self.table[i].fromValues[j]] = result.table[i].toValue
				result.table.append(LookupTableEntry(from_list, result.table[i].toValue))
			result.count = self.count
		elif (self.type == RegisterValueType.InSetOfValues) or (self.type == RegisterValueType.NotInSetOfValues):
			values = (ctypes.c_longlong * self.count)()
			i = 0
			for value in self.values:
				values[i] = value
				i += 1
			result.valueSet = ctypes.cast(values, ctypes.POINTER(ctypes.c_longlong))
			result.count = self.count
		return result

	@property
	def type(self):
		""" """
		return self._type

	@type.setter
	def type(self, value):
		""" """
		self._type = value

	@property
	def reg(self):
		""" """
		return self._reg

	@reg.setter
	def reg(self, value):
		""" """
		self._reg = value

	@property
	def value(self):
		""" """
		return self._value

	@value.setter
	def value(self, value):
		""" """
		self._value = value

	@property
	def offset(self):
		""" """
		return self._offset

	@offset.setter
	def offset(self, value):
		""" """
		self._offset = value

	@property
	def ranges(self):
		""" """
		return self._ranges

	@ranges.setter
	def ranges(self, value):
		""" """
		self._ranges = value

	@property
	def table(self):
		""" """
		return self._table

	@table.setter
	def table(self, value):
		""" """
		self._table = value

	@property
	def mapping(self):
		""" """
		return self._mapping

	@mapping.setter
	def mapping(self, value):
		""" """
		self._mapping = value

	@property
	def values(self):
		""" """
		return self._values

	@values.setter
	def values(self, value):
		""" """
		self._values = value

	@property
	def count(self):
		""" """
		return self._count

	@count.setter
	def count(self, value):
		self._count = value

	@classmethod
	def undetermined(self):
		"""
		Create a PossibleValueSet object of type UndeterminedValue.

		:return: PossibleValueSet object of type UndeterminedValue
		:rtype: PossibleValueSet
		"""
		return PossibleValueSet()

	@classmethod
	def constant(self, value):
		"""
		Create a constant valued PossibleValueSet object.

		:param int value: Integer value of the constant
		:rtype: PossibleValueSet
		"""
		result = PossibleValueSet()
		result.type = RegisterValueType.ConstantValue
		result.value = value
		return result

	@classmethod
	def constant_ptr(self, value):
		"""
		Create constant pointer valued PossibleValueSet object.

		:param int value: Integer value of the constant pointer
		:rtype: PossibleValueSet
		"""
		result = PossibleValueSet()
		result.type = RegisterValueType.ConstantPointerValue
		result.value = value
		return result

	@classmethod
	def stack_frame_offset(self, offset):
		"""
		Create a PossibleValueSet object for a stack frame offset.

		:param int value: Integer value of the offset
		:rtype: PossibleValueSet
		"""
		result = PossibleValueSet()
		result.type = RegisterValueType.StackFrameOffset
		result.offset = offset
		return result

	@classmethod
	def signed_range_value(self, ranges):
		"""
		Create a PossibleValueSet object for a signed range of values.

		:param list(ValueRange) ranges: List of ValueRanges
		:rtype: PossibleValueSet
		:Example:

			>>> v_1 = ValueRange(-5, -1, 1)
			>>> v_2 = ValueRange(7, 10, 1)
			>>> val = PossibleValueSet.signed_range_value([v_1, v_2])
			<signed ranges: [<range: -0x5 to -0x1>, <range: 0x7 to 0xa>]>
		"""
		result = PossibleValueSet()
		result.value = 0
		result.type = RegisterValueType.SignedRangeValue
		result.ranges = ranges
		result.count = len(ranges)
		return result

	@classmethod
	def unsigned_range_value(self, ranges):
		"""
		Create a PossibleValueSet object for a unsigned signed range of values.

		:param list(ValueRange) ranges: List of ValueRanges
		:rtype: PossibleValueSet
		:Example:

			>>> v_1 = ValueRange(0, 5, 1)
			>>> v_2 = ValueRange(7, 10, 1)
			>>> val = PossibleValueSet.unsigned_range_value([v_1, v_2])
			<unsigned ranges: [<range: 0x0 to 0x5>, <range: 0x7 to 0xa>]>
		"""
		result = PossibleValueSet()
		result.value = 0
		result.type = RegisterValueType.UnsignedRangeValue
		result.ranges = ranges
		result.count = len(ranges)
		return result

	@classmethod
	def in_set_of_values(self, values):
		"""
		Create a PossibleValueSet object for a value in a set of values.

		:param list(int) values: List of integer values
		:rtype: PossibleValueSet
		"""
		result = PossibleValueSet()
		result.type = RegisterValueType.InSetOfValues
		result.values = set(values)
		result.count = len(values)
		return result

	@classmethod
	def not_in_set_of_values(self, values):
		"""
		Create a PossibleValueSet object for a value NOT in a set of values.

		:param list(int) values: List of integer values
		:rtype: PossibleValueSet
		"""
		result = PossibleValueSet()
		result.type = RegisterValueType.NotInSetOfValues
		result.values = set(values)
		result.count = len(values)
		return result

	@classmethod
	def lookup_table_value(self, lookup_table, mapping):
		"""
		Create a PossibleValueSet object for a value which is a member of a
		lookuptable.

		:param list(LookupTableEntry) lookup_table: List of table entries
		:param dict of (int, int) mapping: Mapping used for resolution
		:rtype: PossibleValueSet
		"""
		result = PossibleValueSet()
		result.type = RegisterValueType.LookupTableValue
		result.table = lookup_table
		result.mapping = mapping
		return result


class StackVariableReference(object):
	def __init__(self, src_operand, t, name, var, ref_ofs, size):
		self._source_operand = src_operand
		self._type = t
		self._name = name
		self._var = var
		self._referenced_offset = ref_ofs
		self._size = size
		if self._source_operand == 0xffffffff:
			self._source_operand = None

	def __repr__(self):
		if self._source_operand is None:
			if self._referenced_offset != self._var.storage:
				return "<ref to %s%+#x>" % (self._name, self._referenced_offset - self._var.storage)
			return "<ref to %s>" % self._name
		if self._referenced_offset != self._var.storage:
			return "<operand %d ref to %s%+#x>" % (self._source_operand, self._name, self._var.storage)
		return "<operand %d ref to %s>" % (self._source_operand, self._name)

	def __eq__(self, other):
		if not isinstance(other, self.__class__):
			return NotImplemented
		return (self._source_operand, self._type, self._name, self._var, self._referenced_offset, self._size) == \
			(other._source_operand, other._type, other._name, other._var, other._referenced_offset, other._size)

	def __ne__(self, other):
		if not isinstance(other, self.__class__):
			return NotImplemented
		return not (self == other)

	def __hash__(self):
		return hash((self._source_operand, self._type, self._name, self._var, self._referenced_offset, self._size))

	@property
	def source_operand(self):
		""" """
		return self._source_operand

	@source_operand.setter
	def source_operand(self, value):
		self._source_operand = value

	@property
	def type(self):
		""" """
		return self._type

	@type.setter
	def type(self, value):
		self._type = value

	@property
	def name(self):
		""" """
		return self._name

	@name.setter
	def name(self, value):
		self._name = value

	@property
	def var(self):
		""" """
		return self._var

	@var.setter
	def var(self, value):
		self._var = value

	@property
	def referenced_offset(self):
		""" """
		return self._referenced_offset

	@referenced_offset.setter
	def referenced_offset(self, value):
		self._referenced_offset = value

	@property
	def size(self):
		""" """
		return self._size

	@size.setter
	def size(self, value):
		self._size = value

@decorators.passive
class Variable(object):
	def __init__(self, func, source_type, index, storage, name = None, var_type = None, identifier = None):
		self._function = func
		self._source_type = source_type
		self._index = index
		self._storage = storage
		self._identifier = identifier
		self._name = name
		self._type = var_type

	def __repr__(self):
		return "<var %s %s%s>" % (self.type.get_string_before_name(), self.name, self.type.get_string_after_name())

	def __str__(self):
		return self.name

	def __eq__(self, other):
		if not isinstance(other, self.__class__):
			return NotImplemented
		return (self.identifier, self.function) == (other.identifier, other.function)

	def __ne__(self, other):
		if not isinstance(other, self.__class__):
			return NotImplemented
		return not (self == other)

	def __hash__(self):
		return hash((self.identifier, self.function))

	@property
	def function(self):
		"""Function where the variable is defined"""
		return self._function

	@function.setter
	def function(self, value):
		self._function = value

	@property
	def source_type(self):
		""":class:`~enums.VariableSourceType`"""
		if not isinstance(self._source_type, VariableSourceType):
			self._source_type = VariableSourceType(self._source_type)

		return self._source_type

	@source_type.setter
	def source_type(self, value):
		self._source_type = value

	@property
	def index(self):
		""" """
		return self._index

	@index.setter
	def index(self, value):
		self._index = value

	@property
	def storage(self):
		"""Stack offset for StackVariableSourceType, register index for RegisterVariableSourceType"""
		return self._storage

	@storage.setter
	def storage(self, value):
		self._storage = value

	@property
	def identifier(self):
		""" """
		if self._identifier is None:
			self._identifier = core.BNToVariableIdentifier(self.to_BNVariable())
		return self._identifier

	@identifier.setter
	def identifier(self, value):
		self._identifier = value

	@property
	def name(self):
		"""Name of the variable, set to an empty string to delete"""
		if self._name is None:
			if self._function is not None:
				self._name = core.BNGetVariableName(self._function.handle, self.to_BNVariable())
		return self._name

	@name.setter
	def name(self, value):
		self._name = value

	@property
	def type(self):
		""" """
		if self._type is None:
			if self._function is not None:
				var_type_conf = core.BNGetVariableType(self._function.handle, self.to_BNVariable())
				if var_type_conf.type:
					self._type = binaryninja.types.Type(var_type_conf.type, platform = self._function.platform, confidence = var_type_conf.confidence)
		return self._type

	@type.setter
	def type(self, value):
		self._type = value

	def to_BNVariable(self):
		v = core.BNVariable()
		v.type = self.source_type
		v.index = self._index
		v.storage = self._storage
		return v

	@property
	def dead_store_elimination(self):
		if self._function is not None and self._identifier is not None:
			return DeadStoreElimination(core.BNGetFunctionVariableDeadStoreElimination(self._function.handle, self.to_BNVariable()))
		return None

	@dead_store_elimination.setter
	def dead_store_elimination(self, value):
		core.BNSetFunctionVariableDeadStoreElimination(self._function.handle, self.to_BNVariable(), value)

	@classmethod
	def from_identifier(self, func, identifier, name=None, var_type=None):
		var = core.BNFromVariableIdentifier(identifier)
		return Variable(func, VariableSourceType(var.type), var.index, var.storage, name, var_type, identifier)

class ConstantReference(object):
	def __init__(self, val, size, ptr, intermediate):
		self._value = val
		self._size = size
		self._pointer = ptr
		self._intermediate = intermediate

	def __repr__(self):
		if self.pointer:
			return "<constant pointer %#x>" % self.value
		if self.size == 0:
			return "<constant %#x>" % self.value
		return "<constant %#x size %d>" % (self.value, self.size)

	@property
	def value(self):
		""" """
		return self._value

	@value.setter
	def value(self, value):
		self._value = value

	@property
	def size(self):
		""" """
		return self._size

	@size.setter
	def size(self, value):
		self._size = value

	@property
	def pointer(self):
		""" """
		return self._pointer

	@pointer.setter
	def pointer(self, value):
		self._pointer = value

	@property
	def intermediate(self):
		""" """
		return self._intermediate

	@intermediate.setter
	def intermediate(self, value):
		self._intermediate = value


class UserVariableValueInfo(object):
	def __init__(self, var, def_site, value):
		self.var = var
		self.def_site = def_site
		self.value = value

	def __repr__(self):
		return "<user value for %s @ %s:%#x -> %s>" % (self.var, self.def_site.arch.name, self.def_site.addr, self.value)


class IndirectBranchInfo(object):
	def __init__(self, source_arch, source_addr, dest_arch, dest_addr, auto_defined):
		self.source_arch = source_arch
		self.source_addr = source_addr
		self.dest_arch = dest_arch
		self.dest_addr = dest_addr
		self.auto_defined = auto_defined

	def __repr__(self):
		return "<branch %s:%#x -> %s:%#x>" % (self.source_arch.name, self.source_addr, self.dest_arch.name, self.dest_addr)


class ParameterVariables(object):
	def __init__(self, var_list, confidence = core.max_confidence, func = None):
		self._vars = var_list
		self._confidence = confidence
		self._func = func

	def __repr__(self):
		return repr(self._vars)

	def __len__(self):
		return len(self._vars)

	def __iter__(self):
		for var in self._vars:
			yield var

	def __getitem__(self, idx):
		return self._vars[idx]

	def __setitem__(self, idx, value):
		self._vars[idx] = value
		if self._func is not None:
			self._func.parameter_vars = self

	def with_confidence(self, confidence):
		return ParameterVariables(list(self._vars), confidence, self._func)

	@property
	def vars(self):
		""" """
		return self._vars

	@vars.setter
	def vars(self, value):
		self._vars = value

	@property
	def confidence(self):
		""" """
		return self._confidence

	@confidence.setter
	def confidence(self, value):
		self._confidence = value


class ILReferenceSource(object):
	def __init__(self, func, arch, addr, il_type, expr_id):
		self._function = func
		self._arch = arch
		self._address = addr
		self._il_type = il_type
		self._expr_id = expr_id

	def get_il_name(self, il_type):
		if il_type == FunctionGraphType.NormalFunctionGraph:
			return 'disassembly'
		if il_type == FunctionGraphType.LowLevelILFunctionGraph:
			return 'llil'
		if il_type == FunctionGraphType.LiftedILFunctionGraph:
			return 'lifted_llil'
		if il_type == FunctionGraphType.LowLevelILSSAFormFunctionGraph:
			return 'llil_ssa'
		if il_type == FunctionGraphType.MediumLevelILFunctionGraph:
			return 'mlil'
		if il_type == FunctionGraphType.MediumLevelILSSAFormFunctionGraph:
			return 'mlil_ssa'
		if il_type == FunctionGraphType.MappedMediumLevelILFunctionGraph:
			return 'mapped_mlil'
		if il_type == FunctionGraphType.MappedMediumLevelILSSAFormFunctionGraph:
			return 'mapped_mlil_ssa'
		if il_type == FunctionGraphType.HighLevelILFunctionGraph:
			return 'hlil'
		if il_type == FunctionGraphType.HighLevelILSSAFormFunctionGraph:
			return 'hlil_ssa'

	def __repr__(self):
		if self._arch:
			return "<ref: %s@%#x, %s@%d>" %\
				(self._arch.name, self._address, self.get_il_name(self._il_type), self.expr_id)
		else:
			return "<ref: %#x, %s@%d>" %\
				(self._address, self.get_il_name(self._il_type), self.expr_id)

	def __eq__(self, other):
		if not isinstance(other, self.__class__):
			return NotImplemented
		return (self.function, self.arch, self.address, self.il_type, self.expr_id) ==\
			(other.address, other.function, other.arch, other.il_type, other.expr_id)

	def __ne__(self, other):
		if not isinstance(other, self.__class__):
			return NotImplemented
		return not (self == other)

	def __lt__(self, other):
		if not isinstance(other, self.__class__):
			return NotImplemented
		if self.function < other.function:
			return True
		if self.function > other.function:
			return False
		if self.arch < other.arch:
			return True
		if self.arch > other.arch:
			return False
		if self.address < other.address:
			return True
		if self.address > other.address:
			return False
		if self.il_type < other.il_type:
			return True
		if self.il_type > other.il_type:
			return False
		return self.expr_id < other.expr_id

	def __gt__(self, other):
		if not isinstance(other, self.__class__):
			return NotImplemented
		if self.function > other.function:
			return True
		if self.function < other.function:
			return False
		if self.arch > other.arch:
			return True
		if self.arch < other.arch:
			return False
		if self.address > other.address:
			return True
		if self.address < other.address:
			return False
		if self.il_type > other.il_type:
			return True
		if self.il_type < other.il_type:
			return False
		return self.expr_id > other.expr_id

	def __ge__(self, other):
		if not isinstance(other, self.__class__):
			return NotImplemented
		return (self == other) or (self > other)

	def __le__(self, other):
		if not isinstance(other, self.__class__):
			return NotImplemented
		return (self == other) or (self < other)

	def __hash__(self):
		return hash((self._function, self._arch, self._address, self._il_type, self._expr_id))

	@property
	def function(self):
		""" """
		return self._function

	@function.setter
	def function(self, value):
		self._function = value

	@property
	def arch(self):
		""" """
		return self._arch

	@arch.setter
	def arch(self, value):
		self._arch = value

	@property
	def address(self):
		""" """
		return self._address

	@address.setter
	def address(self, value):
		self._address = value

	@property
	def il_type(self):
		""" """
		return self._il_type

	@il_type.setter
	def il_type(self, value):
		self._il_type = value

	@property
	def expr_id(self):
		""" """
		return self._expr_id

	@expr_id.setter
	def expr_id(self, value):
		self._expr_id = value


class VariableReferenceSource(object):
	def __init__(self, var, src):
		self._var = var
		self._src = src

	def __repr__(self):
		return "<var: %s, src: %s>" % (repr(self._var), repr(self._src))

	def __eq__(self, other):
		if not isinstance(other, self.__class__):
			return NotImplemented
		return (self.var == other.var) and (self.src == other.src)

	def __ne__(self, other):
		if not isinstance(other, self.__class__):
			return NotImplemented
		return not (self == other)

	def __lt__(self, other):
		if not isinstance(other, self.__class__):
			return NotImplemented
		if self.var < other.var:
			return True
		if self.var > other.var:
			return False
		return self.src < other.src

	def __gt__(self, other):
		if not isinstance(other, self.__class__):
			return NotImplemented
		if self.var > other.var:
			return True
		if self.var < other.var:
			return False
		return self.src > other.src

	def __ge__(self, other):
		if not isinstance(other, self.__class__):
			return NotImplemented
		if self.var >= other.var:
			return True
		if self.var < other.var:
			return False
		return self.src >= other.src

	def __le__(self, other):
		if not isinstance(other, self.__class__):
			return NotImplemented
		if self.var <= other.var:
			return True
		if self.var > other.var:
			return False
		return self.src <= other.src

	@property
	def var(self):
		return self._var
	@var.setter
	def var(self, value):
		self._var = value

	@property
	def src(self):
		return self._src

	@src.setter
	def src(self, value):
		self._src = value




class AddressRange(object):
	def __init__(self, start, end):
		self._start = start
		self._end = end

	def __repr__(self):
		return "<%#x-%#x>" % (self._start, self._end)

	def __len__(self):
		return self._end - self.start

	def __eq__(self, other):
		if not isinstance(other, self.__class__):
			return NotImplemented
		return (self._start, self._end) == (other._start, other._end)

	def __ne__(self, other):
		if not isinstance(other, self.__class__):
			return NotImplemented
		return not (self == other)

	def __hash__(self):
		return hash((self._start, self._end))

	@property
	def length(self):
		return self._end - self._start

	@property
	def start(self):
		""" """
		return self._start

	@start.setter
	def start(self, value):
		self._start = value

	@property
	def end(self):
		""" """
		return self._end

	@end.setter
	def end(self, value):
		self._end = value
