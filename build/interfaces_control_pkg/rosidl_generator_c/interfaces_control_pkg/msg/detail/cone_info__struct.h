// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from interfaces_control_pkg:msg/ConeInfo.idl
// generated code does not contain a copyright notice

#ifndef INTERFACES_CONTROL_PKG__MSG__DETAIL__CONE_INFO__STRUCT_H_
#define INTERFACES_CONTROL_PKG__MSG__DETAIL__CONE_INFO__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'cone_color'
#include "rosidl_runtime_c/string.h"

/// Struct defined in msg/ConeInfo in the package interfaces_control_pkg.
typedef struct interfaces_control_pkg__msg__ConeInfo
{
  float x;
  float y;
  float z;
  float distance;
  rosidl_runtime_c__String cone_color;
} interfaces_control_pkg__msg__ConeInfo;

// Struct for a sequence of interfaces_control_pkg__msg__ConeInfo.
typedef struct interfaces_control_pkg__msg__ConeInfo__Sequence
{
  interfaces_control_pkg__msg__ConeInfo * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} interfaces_control_pkg__msg__ConeInfo__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // INTERFACES_CONTROL_PKG__MSG__DETAIL__CONE_INFO__STRUCT_H_
