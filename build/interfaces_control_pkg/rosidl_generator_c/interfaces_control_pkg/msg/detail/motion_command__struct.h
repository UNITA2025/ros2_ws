// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from interfaces_control_pkg:msg/MotionCommand.idl
// generated code does not contain a copyright notice

#ifndef INTERFACES_CONTROL_PKG__MSG__DETAIL__MOTION_COMMAND__STRUCT_H_
#define INTERFACES_CONTROL_PKG__MSG__DETAIL__MOTION_COMMAND__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

/// Struct defined in msg/MotionCommand in the package interfaces_control_pkg.
typedef struct interfaces_control_pkg__msg__MotionCommand
{
  int32_t steering;
  int32_t left_speed;
  int32_t right_speed;
} interfaces_control_pkg__msg__MotionCommand;

// Struct for a sequence of interfaces_control_pkg__msg__MotionCommand.
typedef struct interfaces_control_pkg__msg__MotionCommand__Sequence
{
  interfaces_control_pkg__msg__MotionCommand * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} interfaces_control_pkg__msg__MotionCommand__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // INTERFACES_CONTROL_PKG__MSG__DETAIL__MOTION_COMMAND__STRUCT_H_
