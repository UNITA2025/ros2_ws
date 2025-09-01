// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from interfaces_control_pkg:msg/ConeInfoArray.idl
// generated code does not contain a copyright notice

#ifndef INTERFACES_CONTROL_PKG__MSG__DETAIL__CONE_INFO_ARRAY__STRUCT_H_
#define INTERFACES_CONTROL_PKG__MSG__DETAIL__CONE_INFO_ARRAY__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'cones'
#include "interfaces_control_pkg/msg/detail/cone_info__struct.h"

/// Struct defined in msg/ConeInfoArray in the package interfaces_control_pkg.
typedef struct interfaces_control_pkg__msg__ConeInfoArray
{
  interfaces_control_pkg__msg__ConeInfo__Sequence cones;
} interfaces_control_pkg__msg__ConeInfoArray;

// Struct for a sequence of interfaces_control_pkg__msg__ConeInfoArray.
typedef struct interfaces_control_pkg__msg__ConeInfoArray__Sequence
{
  interfaces_control_pkg__msg__ConeInfoArray * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} interfaces_control_pkg__msg__ConeInfoArray__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // INTERFACES_CONTROL_PKG__MSG__DETAIL__CONE_INFO_ARRAY__STRUCT_H_
