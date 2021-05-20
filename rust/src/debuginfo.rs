// Copyright 2021 Vector 35 Inc.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

use binaryninjacore_sys::*;

// TODO : Documentation
//   Types need to be created in a specific order; if you have a pointer to a struct, you need to define that struct and all its fields before you can define what a pointer to that struct is
//   Though in reality we might need to forward declare all structs and classes and come back later to populate them
//   Either way, this being the case, you're required to give each type a UID for all your types with which Binary Ninja can track dependencies efficiently
//   The intended workflow of using DebugInfo is to first create `FunctionInfoBuilder`s, iterating your debug info and gathering whatever information you can about your functions (creating types for return values and parameters along the way and adding them to the DebugInfo, but not registering them with the BV)
//   Then destill that information into `FunctionInfo` and adding those to the DebugInfo,
// TODO : Move the code that converts FunctionInfoBuilder's into TypeInfo from the module into the core library
// TODO : Or move all the FunctionInfoBuilder stuff out
//   Then you're done and BN will take your DebugInfo and apply it to the binary best we can

// TODO : ensure feature equivalence

use crate::{
    binaryview::BinaryView,
    rc::*,
    string::{raw_to_string, BnStrCompatible, BnString},
    types::{DataVariableAndName, NameAndType, Type},
};

use std::{
    hash::Hash,
    mem,
    os::raw::{c_char, c_void},
    ptr, slice,
};

//////////////////////
//  DebugInfoParser

#[derive(PartialEq, Eq, Hash)]
pub struct DebugInfoParser {
    pub(crate) handle: *mut BNDebugInfoParser,
}

impl DebugInfoParser {
    pub(crate) unsafe fn from_raw(handle: *mut BNDebugInfoParser) -> Ref<Self> {
        debug_assert!(!handle.is_null());

        Ref::new(Self { handle })
    }

    pub fn from_name<S: BnStrCompatible>(name: S) -> Result<Ref<Self>, ()> {
        let name = name.as_bytes_with_nul();
        let parser = unsafe { BNGetDebugInfoParserByName(name.as_ref().as_ptr() as *mut _) };

        if parser.is_null() {
            Err(())
        } else {
            unsafe { Ok(Self::from_raw(parser)) }
        }
    }

    // TODO : do I need to "init plugins?"
    pub fn list() -> Array<DebugInfoParser> {
        let mut count: usize = unsafe { mem::zeroed() };
        let raw_parsers = unsafe { BNGetDebugInfoParsers(&mut count as *mut _) };
        unsafe { Array::new(raw_parsers, count, ()) }
    }

    pub fn name(&self) -> BnString {
        unsafe { BnString::from_raw(BNGetDebugInfoParserName(self.handle)) }
    }

    pub fn is_valid_for_view(&self, view: BinaryView) -> bool {
        unsafe { BNIsDebugInfoParserValidForView(self.handle, view.handle) }
    }

    pub fn parse_debug_info(&self, view: BinaryView) -> Ref<DebugInfo> {
        unsafe { DebugInfo::from_raw(BNParseDebugInfo(self.handle, view.handle)) }
    }

    pub fn register<S, C>(name: S, parser_callbacks: C) -> Ref<Self>
    where
        S: BnStrCompatible,
        C: CustomDebugInfoParser,
    {
        extern "C" fn cb_is_valid<C>(ctxt: *mut c_void, view: *mut BNBinaryView) -> bool
        where
            C: CustomDebugInfoParser,
        {
            ffi_wrap!("CustomDebugInfoParser::is_valid", unsafe {
                let cmd = &*(ctxt as *const C);
                let view = BinaryView::from_raw(view);

                cmd.is_valid(&view)
            })
        }

        extern "C" fn cb_parse_info<C>(
            ctxt: *mut c_void,
            debug_info: *mut BNDebugInfo,
            view: *mut BNBinaryView,
        ) where
            C: CustomDebugInfoParser,
        {
            ffi_wrap!("CustomDebugInfoParser::parse_info", unsafe {
                let cmd = &*(ctxt as *const C);
                let view = BinaryView::from_raw(view);
                let mut debug_info = DebugInfo::from_raw(debug_info);

                cmd.parse_info(&mut debug_info, &view);
            })
        }

        let name = name.as_bytes_with_nul();
        let name_ptr = name.as_ref().as_ptr() as *mut _;
        let ctxt = Box::into_raw(Box::new(parser_callbacks));

        unsafe {
            DebugInfoParser::from_raw(BNRegisterDebugInfoParser(
                name_ptr,
                Some(cb_is_valid::<C>),
                Some(cb_parse_info::<C>),
                ctxt as *mut _,
            ))
        }
    }
}

unsafe impl RefCountable for DebugInfoParser {
    unsafe fn inc_ref(handle: &Self) -> Ref<Self> {
        Ref::new(Self {
            handle: BNNewDebugInfoParserReference(handle.handle),
        })
    }

    unsafe fn dec_ref(handle: &Self) {
        BNFreeDebugInfoParserReference(handle.handle);
    }
}

impl AsRef<DebugInfoParser> for DebugInfoParser {
    fn as_ref(&self) -> &Self {
        self
    }
}

impl ToOwned for DebugInfoParser {
    type Owned = Ref<Self>;

    fn to_owned(&self) -> Self::Owned {
        unsafe { RefCountable::inc_ref(self) }
    }
}

unsafe impl CoreOwnedArrayProvider for DebugInfoParser {
    type Raw = *mut BNDebugInfoParser;
    type Context = ();

    unsafe fn free(raw: *mut Self::Raw, count: usize, _: &Self::Context) {
        BNFreeDebugInfoParserList(raw, count);
    }
}

///////////////////////
// DebugFunctionInfo

pub struct DebugFunctionInfo<S1: BnStrCompatible, S2: BnStrCompatible> {
    short_name: S1,
    full_name: S1,
    raw_name: S1,
    return_type: Ref<Type>,
    address: u64,
    parameters: Vec<(S2, Ref<Type>)>,
}

impl From<&BNDebugFunctionInfo> for DebugFunctionInfo<String, String> {
    fn from(raw: &BNDebugFunctionInfo) -> Self {
        let raw_parameter_names: &[*mut ::std::os::raw::c_char] =
            unsafe { slice::from_raw_parts(raw.parameterNames as *mut _, raw.parameterCount) };
        let raw_parameter_types: &[*mut BNType] =
            unsafe { slice::from_raw_parts(raw.parameterTypes as *mut _, raw.parameterCount) };

        let parameters: Vec<(String, Ref<Type>)> = (0..raw.parameterCount)
            .map(|i| {
                (raw_to_string(raw_parameter_names[i]), unsafe {
                    Type::ref_from_raw(raw_parameter_types[i])
                })
            })
            .collect();

        Self {
            short_name: raw_to_string(raw.shortName),
            full_name: raw_to_string(raw.fullName),
            raw_name: raw_to_string(raw.rawName),
            return_type: unsafe { Type::ref_from_raw(raw.returnType) },
            address: raw.address,
            parameters,
        }
    }
}

impl<S1: BnStrCompatible, S2: BnStrCompatible> Into<BNDebugFunctionInfo>
    for DebugFunctionInfo<S1, S2>
{
    fn into(self) -> BNDebugFunctionInfo {
        let parameter_count: usize = self.parameters.len();

        let short_name = self.short_name.as_bytes_with_nul();
        let full_name = self.full_name.as_bytes_with_nul();
        let raw_name = self.raw_name.as_bytes_with_nul();

        let (_parameter_name_bytes, mut parameter_names, mut parameter_types): (
            Vec<S2::Result>,
            Vec<*mut c_char>,
            Vec<*mut BNType>,
        ) = self.parameters.into_iter().fold(
            (
                Vec::with_capacity(parameter_count),
                Vec::with_capacity(parameter_count),
                Vec::with_capacity(parameter_count),
            ),
            |(mut parameter_name_bytes, mut parameter_names, mut parameter_types), (n, t)| {
                parameter_name_bytes.push(n.as_bytes_with_nul());
                parameter_names
                    .push(parameter_name_bytes.last().unwrap().as_ref().as_ptr() as *mut c_char);
                parameter_types.push(t.handle);
                (parameter_name_bytes, parameter_names, parameter_types)
            },
        );

        BNDebugFunctionInfo {
            shortName: short_name.as_ref().as_ptr() as *mut _,
            fullName: full_name.as_ref().as_ptr() as *mut _,
            rawName: raw_name.as_ref().as_ptr() as *mut _,
            address: self.address,
            returnType: self.return_type.handle,
            parameterNames: parameter_names.as_mut_ptr(),
            parameterTypes: parameter_types.as_mut_ptr(),
            parameterCount: parameter_count,
        }
    }
}

impl<S1: BnStrCompatible, S2: BnStrCompatible> DebugFunctionInfo<S1, S2> {
    pub fn new(
        short_name: S1,
        full_name: S1,
        raw_name: S1,
        return_type: Ref<Type>,
        address: u64,
        parameters: Vec<(S2, Ref<Type>)>,
    ) -> Self {
        Self {
            short_name,
            full_name,
            raw_name,
            return_type,
            address,
            parameters,
        }
    }
}

///////////////
// DebugInfo

#[derive(PartialEq, Eq, Hash)]
pub struct DebugInfo {
    pub(crate) handle: *mut BNDebugInfo,
}

impl DebugInfo {
    pub(crate) unsafe fn from_raw(handle: *mut BNDebugInfo) -> Ref<Self> {
        debug_assert!(!handle.is_null());

        Ref::new(Self { handle })
    }

    pub fn types_by_name<S: BnStrCompatible>(&self, parser_name: S) -> Vec<NameAndType<String>> {
        let parser_name = parser_name.as_bytes_with_nul();

        let mut count: usize = 0;
        let debug_types_ptr = unsafe {
            BNGetDebugTypes(
                self.handle,
                parser_name.as_ref().as_ptr() as *mut _,
                &mut count,
            )
        };
        let result: Vec<NameAndType<String>> = unsafe {
            slice::from_raw_parts_mut(debug_types_ptr, count)
                .iter()
                .map(NameAndType::<String>::from_raw)
                .collect()
        };

        unsafe { BNFreeDebugTypes(debug_types_ptr, count) };
        result
    }

    pub fn types(&self) -> Vec<NameAndType<String>> {
        let mut count: usize = 0;
        let debug_types_ptr = unsafe { BNGetDebugTypes(self.handle, ptr::null_mut(), &mut count) };
        let result: Vec<NameAndType<String>> = unsafe {
            slice::from_raw_parts_mut(debug_types_ptr, count)
                .iter()
                .map(NameAndType::<String>::from_raw)
                .collect()
        };

        unsafe { BNFreeDebugTypes(debug_types_ptr, count) };
        result
    }

    pub fn functions_by_name<S: BnStrCompatible>(
        &self,
        parser_name: S,
    ) -> Vec<DebugFunctionInfo<String, String>> {
        let parser_name = parser_name.as_bytes_with_nul();

        let mut count: usize = 0;
        let functions_ptr = unsafe {
            BNGetDebugFunctions(
                self.handle,
                parser_name.as_ref().as_ptr() as *mut _,
                &mut count,
            )
        };

        let result: Vec<DebugFunctionInfo<String, String>> = unsafe {
            slice::from_raw_parts_mut(functions_ptr, count)
                .iter()
                .map(DebugFunctionInfo::<String, String>::from)
                .collect()
        };

        unsafe { BNFreeDebugFunctions(functions_ptr, count) };
        result
    }
    pub fn functions(&self) -> Vec<DebugFunctionInfo<String, String>> {
        let mut count: usize = 0;
        let functions_ptr =
            unsafe { BNGetDebugFunctions(self.handle, ptr::null_mut(), &mut count) };

        let result: Vec<DebugFunctionInfo<String, String>> = unsafe {
            slice::from_raw_parts_mut(functions_ptr, count)
                .iter()
                .map(DebugFunctionInfo::<String, String>::from)
                .collect()
        };

        unsafe { BNFreeDebugFunctions(functions_ptr, count) };
        result
    }

    pub fn data_variables_by_name<S: BnStrCompatible>(
        &self,
        parser_name: S,
    ) -> Vec<DataVariableAndName<String>> {
        let parser_name = parser_name.as_bytes_with_nul();

        let mut count: usize = 0;
        let data_variables_ptr = unsafe {
            BNGetDebugDataVariables(
                self.handle,
                parser_name.as_ref().as_ptr() as *mut _,
                &mut count,
            )
        };

        let result: Vec<DataVariableAndName<String>> = unsafe {
            slice::from_raw_parts_mut(data_variables_ptr, count)
                .iter()
                .map(DataVariableAndName::<String>::from_raw)
                .collect()
        };

        unsafe { BNFreeDataVariablesAndName(data_variables_ptr, count) };
        result
    }

    pub fn data_variables(&self) -> Vec<DataVariableAndName<String>> {
        let mut count: usize = 0;
        let data_variables_ptr =
            unsafe { BNGetDebugDataVariables(self.handle, ptr::null_mut(), &mut count) };

        let result: Vec<DataVariableAndName<String>> = unsafe {
            slice::from_raw_parts_mut(data_variables_ptr, count)
                .iter()
                .map(DataVariableAndName::<String>::from_raw)
                .collect()
        };

        unsafe { BNFreeDataVariablesAndName(data_variables_ptr, count) };
        result
    }

    // TODO : Return the type that was added instead of whether or not the type was added (type wasn't previously added)?
    pub fn add_type<S: BnStrCompatible>(&mut self, name: S, new_type: &Type) -> bool {
        let name = name.as_bytes_with_nul();
        unsafe {
            BNAddDebugType(
                self.handle,
                name.as_ref().as_ptr() as *mut _,
                new_type.handle,
            )
        }
    }

    pub fn add_function<S1: BnStrCompatible, S2: BnStrCompatible>(
        &mut self,
        new_func: DebugFunctionInfo<S1, S2>,
    ) -> bool {
        unsafe { BNAddDebugFunction(self.handle, &mut new_func.into() as *mut _) }
    }

    pub fn add_data_variable<S: BnStrCompatible>(
        &self,
        address: u64,
        t: &Type,
        name: Option<S>,
    ) -> bool {
        match name {
            Some(name) => {
                let name = name.as_bytes_with_nul();
                unsafe {
                    BNAddDebugDataVariable(
                        self.handle,
                        address,
                        t.handle,
                        name.as_ref().as_ptr() as *mut _,
                    )
                }
            }
            None => unsafe {
                BNAddDebugDataVariable(self.handle, address, t.handle, ptr::null_mut())
            },
        }
    }
}

unsafe impl RefCountable for DebugInfo {
    unsafe fn inc_ref(handle: &Self) -> Ref<Self> {
        Ref::new(Self {
            handle: BNNewDebugInfoReference(handle.handle),
        })
    }

    unsafe fn dec_ref(handle: &Self) {
        BNFreeDebugInfoReference(handle.handle);
    }
}

impl AsRef<DebugInfo> for DebugInfo {
    fn as_ref(&self) -> &Self {
        self
    }
}

impl ToOwned for DebugInfo {
    type Owned = Ref<Self>;

    fn to_owned(&self) -> Self::Owned {
        unsafe { RefCountable::inc_ref(self) }
    }
}

////////////////////////////
//  CustomDebugInfoParser

// TODO : Make the names/traits impls creative so it's pretty to implement

pub trait CustomDebugInfoParser: 'static + Sync {
    fn is_valid(&self, view: &BinaryView) -> bool;
    fn parse_info(&self, debug_info: &mut DebugInfo, view: &BinaryView);
}
