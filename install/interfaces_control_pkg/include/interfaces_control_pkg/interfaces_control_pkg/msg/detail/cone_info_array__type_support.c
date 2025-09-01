// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from interfaces_control_pkg:msg/ConeInfoArray.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "interfaces_control_pkg/msg/detail/cone_info_array__rosidl_typesupport_introspection_c.h"
#include "interfaces_control_pkg/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "interfaces_control_pkg/msg/detail/cone_info_array__functions.h"
#include "interfaces_control_pkg/msg/detail/cone_info_array__struct.h"


// Include directives for member types
// Member `cones`
#include "interfaces_control_pkg/msg/cone_info.h"
// Member `cones`
#include "interfaces_control_pkg/msg/detail/cone_info__rosidl_typesupport_introspection_c.h"

#ifdef __cplusplus
extern "C"
{
#endif

void interfaces_control_pkg__msg__ConeInfoArray__rosidl_typesupport_introspection_c__ConeInfoArray_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  interfaces_control_pkg__msg__ConeInfoArray__init(message_memory);
}

void interfaces_control_pkg__msg__ConeInfoArray__rosidl_typesupport_introspection_c__ConeInfoArray_fini_function(void * message_memory)
{
  interfaces_control_pkg__msg__ConeInfoArray__fini(message_memory);
}

size_t interfaces_control_pkg__msg__ConeInfoArray__rosidl_typesupport_introspection_c__size_function__ConeInfoArray__cones(
  const void * untyped_member)
{
  const interfaces_control_pkg__msg__ConeInfo__Sequence * member =
    (const interfaces_control_pkg__msg__ConeInfo__Sequence *)(untyped_member);
  return member->size;
}

const void * interfaces_control_pkg__msg__ConeInfoArray__rosidl_typesupport_introspection_c__get_const_function__ConeInfoArray__cones(
  const void * untyped_member, size_t index)
{
  const interfaces_control_pkg__msg__ConeInfo__Sequence * member =
    (const interfaces_control_pkg__msg__ConeInfo__Sequence *)(untyped_member);
  return &member->data[index];
}

void * interfaces_control_pkg__msg__ConeInfoArray__rosidl_typesupport_introspection_c__get_function__ConeInfoArray__cones(
  void * untyped_member, size_t index)
{
  interfaces_control_pkg__msg__ConeInfo__Sequence * member =
    (interfaces_control_pkg__msg__ConeInfo__Sequence *)(untyped_member);
  return &member->data[index];
}

void interfaces_control_pkg__msg__ConeInfoArray__rosidl_typesupport_introspection_c__fetch_function__ConeInfoArray__cones(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const interfaces_control_pkg__msg__ConeInfo * item =
    ((const interfaces_control_pkg__msg__ConeInfo *)
    interfaces_control_pkg__msg__ConeInfoArray__rosidl_typesupport_introspection_c__get_const_function__ConeInfoArray__cones(untyped_member, index));
  interfaces_control_pkg__msg__ConeInfo * value =
    (interfaces_control_pkg__msg__ConeInfo *)(untyped_value);
  *value = *item;
}

void interfaces_control_pkg__msg__ConeInfoArray__rosidl_typesupport_introspection_c__assign_function__ConeInfoArray__cones(
  void * untyped_member, size_t index, const void * untyped_value)
{
  interfaces_control_pkg__msg__ConeInfo * item =
    ((interfaces_control_pkg__msg__ConeInfo *)
    interfaces_control_pkg__msg__ConeInfoArray__rosidl_typesupport_introspection_c__get_function__ConeInfoArray__cones(untyped_member, index));
  const interfaces_control_pkg__msg__ConeInfo * value =
    (const interfaces_control_pkg__msg__ConeInfo *)(untyped_value);
  *item = *value;
}

bool interfaces_control_pkg__msg__ConeInfoArray__rosidl_typesupport_introspection_c__resize_function__ConeInfoArray__cones(
  void * untyped_member, size_t size)
{
  interfaces_control_pkg__msg__ConeInfo__Sequence * member =
    (interfaces_control_pkg__msg__ConeInfo__Sequence *)(untyped_member);
  interfaces_control_pkg__msg__ConeInfo__Sequence__fini(member);
  return interfaces_control_pkg__msg__ConeInfo__Sequence__init(member, size);
}

static rosidl_typesupport_introspection_c__MessageMember interfaces_control_pkg__msg__ConeInfoArray__rosidl_typesupport_introspection_c__ConeInfoArray_message_member_array[1] = {
  {
    "cones",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(interfaces_control_pkg__msg__ConeInfoArray, cones),  // bytes offset in struct
    NULL,  // default value
    interfaces_control_pkg__msg__ConeInfoArray__rosidl_typesupport_introspection_c__size_function__ConeInfoArray__cones,  // size() function pointer
    interfaces_control_pkg__msg__ConeInfoArray__rosidl_typesupport_introspection_c__get_const_function__ConeInfoArray__cones,  // get_const(index) function pointer
    interfaces_control_pkg__msg__ConeInfoArray__rosidl_typesupport_introspection_c__get_function__ConeInfoArray__cones,  // get(index) function pointer
    interfaces_control_pkg__msg__ConeInfoArray__rosidl_typesupport_introspection_c__fetch_function__ConeInfoArray__cones,  // fetch(index, &value) function pointer
    interfaces_control_pkg__msg__ConeInfoArray__rosidl_typesupport_introspection_c__assign_function__ConeInfoArray__cones,  // assign(index, value) function pointer
    interfaces_control_pkg__msg__ConeInfoArray__rosidl_typesupport_introspection_c__resize_function__ConeInfoArray__cones  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers interfaces_control_pkg__msg__ConeInfoArray__rosidl_typesupport_introspection_c__ConeInfoArray_message_members = {
  "interfaces_control_pkg__msg",  // message namespace
  "ConeInfoArray",  // message name
  1,  // number of fields
  sizeof(interfaces_control_pkg__msg__ConeInfoArray),
  interfaces_control_pkg__msg__ConeInfoArray__rosidl_typesupport_introspection_c__ConeInfoArray_message_member_array,  // message members
  interfaces_control_pkg__msg__ConeInfoArray__rosidl_typesupport_introspection_c__ConeInfoArray_init_function,  // function to initialize message memory (memory has to be allocated)
  interfaces_control_pkg__msg__ConeInfoArray__rosidl_typesupport_introspection_c__ConeInfoArray_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t interfaces_control_pkg__msg__ConeInfoArray__rosidl_typesupport_introspection_c__ConeInfoArray_message_type_support_handle = {
  0,
  &interfaces_control_pkg__msg__ConeInfoArray__rosidl_typesupport_introspection_c__ConeInfoArray_message_members,
  get_message_typesupport_handle_function,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_interfaces_control_pkg
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, interfaces_control_pkg, msg, ConeInfoArray)() {
  interfaces_control_pkg__msg__ConeInfoArray__rosidl_typesupport_introspection_c__ConeInfoArray_message_member_array[0].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, interfaces_control_pkg, msg, ConeInfo)();
  if (!interfaces_control_pkg__msg__ConeInfoArray__rosidl_typesupport_introspection_c__ConeInfoArray_message_type_support_handle.typesupport_identifier) {
    interfaces_control_pkg__msg__ConeInfoArray__rosidl_typesupport_introspection_c__ConeInfoArray_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &interfaces_control_pkg__msg__ConeInfoArray__rosidl_typesupport_introspection_c__ConeInfoArray_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif
