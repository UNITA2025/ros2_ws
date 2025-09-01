// generated from rosidl_typesupport_introspection_cpp/resource/idl__type_support.cpp.em
// with input from interfaces_control_pkg:msg/ConeInfoArray.idl
// generated code does not contain a copyright notice

#include "array"
#include "cstddef"
#include "string"
#include "vector"
#include "rosidl_runtime_c/message_type_support_struct.h"
#include "rosidl_typesupport_cpp/message_type_support.hpp"
#include "rosidl_typesupport_interface/macros.h"
#include "interfaces_control_pkg/msg/detail/cone_info_array__struct.hpp"
#include "rosidl_typesupport_introspection_cpp/field_types.hpp"
#include "rosidl_typesupport_introspection_cpp/identifier.hpp"
#include "rosidl_typesupport_introspection_cpp/message_introspection.hpp"
#include "rosidl_typesupport_introspection_cpp/message_type_support_decl.hpp"
#include "rosidl_typesupport_introspection_cpp/visibility_control.h"

namespace interfaces_control_pkg
{

namespace msg
{

namespace rosidl_typesupport_introspection_cpp
{

void ConeInfoArray_init_function(
  void * message_memory, rosidl_runtime_cpp::MessageInitialization _init)
{
  new (message_memory) interfaces_control_pkg::msg::ConeInfoArray(_init);
}

void ConeInfoArray_fini_function(void * message_memory)
{
  auto typed_message = static_cast<interfaces_control_pkg::msg::ConeInfoArray *>(message_memory);
  typed_message->~ConeInfoArray();
}

size_t size_function__ConeInfoArray__cones(const void * untyped_member)
{
  const auto * member = reinterpret_cast<const std::vector<interfaces_control_pkg::msg::ConeInfo> *>(untyped_member);
  return member->size();
}

const void * get_const_function__ConeInfoArray__cones(const void * untyped_member, size_t index)
{
  const auto & member =
    *reinterpret_cast<const std::vector<interfaces_control_pkg::msg::ConeInfo> *>(untyped_member);
  return &member[index];
}

void * get_function__ConeInfoArray__cones(void * untyped_member, size_t index)
{
  auto & member =
    *reinterpret_cast<std::vector<interfaces_control_pkg::msg::ConeInfo> *>(untyped_member);
  return &member[index];
}

void fetch_function__ConeInfoArray__cones(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const auto & item = *reinterpret_cast<const interfaces_control_pkg::msg::ConeInfo *>(
    get_const_function__ConeInfoArray__cones(untyped_member, index));
  auto & value = *reinterpret_cast<interfaces_control_pkg::msg::ConeInfo *>(untyped_value);
  value = item;
}

void assign_function__ConeInfoArray__cones(
  void * untyped_member, size_t index, const void * untyped_value)
{
  auto & item = *reinterpret_cast<interfaces_control_pkg::msg::ConeInfo *>(
    get_function__ConeInfoArray__cones(untyped_member, index));
  const auto & value = *reinterpret_cast<const interfaces_control_pkg::msg::ConeInfo *>(untyped_value);
  item = value;
}

void resize_function__ConeInfoArray__cones(void * untyped_member, size_t size)
{
  auto * member =
    reinterpret_cast<std::vector<interfaces_control_pkg::msg::ConeInfo> *>(untyped_member);
  member->resize(size);
}

static const ::rosidl_typesupport_introspection_cpp::MessageMember ConeInfoArray_message_member_array[1] = {
  {
    "cones",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    ::rosidl_typesupport_introspection_cpp::get_message_type_support_handle<interfaces_control_pkg::msg::ConeInfo>(),  // members of sub message
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(interfaces_control_pkg::msg::ConeInfoArray, cones),  // bytes offset in struct
    nullptr,  // default value
    size_function__ConeInfoArray__cones,  // size() function pointer
    get_const_function__ConeInfoArray__cones,  // get_const(index) function pointer
    get_function__ConeInfoArray__cones,  // get(index) function pointer
    fetch_function__ConeInfoArray__cones,  // fetch(index, &value) function pointer
    assign_function__ConeInfoArray__cones,  // assign(index, value) function pointer
    resize_function__ConeInfoArray__cones  // resize(index) function pointer
  }
};

static const ::rosidl_typesupport_introspection_cpp::MessageMembers ConeInfoArray_message_members = {
  "interfaces_control_pkg::msg",  // message namespace
  "ConeInfoArray",  // message name
  1,  // number of fields
  sizeof(interfaces_control_pkg::msg::ConeInfoArray),
  ConeInfoArray_message_member_array,  // message members
  ConeInfoArray_init_function,  // function to initialize message memory (memory has to be allocated)
  ConeInfoArray_fini_function  // function to terminate message instance (will not free memory)
};

static const rosidl_message_type_support_t ConeInfoArray_message_type_support_handle = {
  ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  &ConeInfoArray_message_members,
  get_message_typesupport_handle_function,
};

}  // namespace rosidl_typesupport_introspection_cpp

}  // namespace msg

}  // namespace interfaces_control_pkg


namespace rosidl_typesupport_introspection_cpp
{

template<>
ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_message_type_support_t *
get_message_type_support_handle<interfaces_control_pkg::msg::ConeInfoArray>()
{
  return &::interfaces_control_pkg::msg::rosidl_typesupport_introspection_cpp::ConeInfoArray_message_type_support_handle;
}

}  // namespace rosidl_typesupport_introspection_cpp

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, interfaces_control_pkg, msg, ConeInfoArray)() {
  return &::interfaces_control_pkg::msg::rosidl_typesupport_introspection_cpp::ConeInfoArray_message_type_support_handle;
}

#ifdef __cplusplus
}
#endif
