// NOLINT: This file starts with a BOM since it contain non-ASCII characters
// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from interfaces_control_pkg:msg/ErpCmdMsg.idl
// generated code does not contain a copyright notice

#ifndef INTERFACES_CONTROL_PKG__MSG__DETAIL__ERP_CMD_MSG__STRUCT_H_
#define INTERFACES_CONTROL_PKG__MSG__DETAIL__ERP_CMD_MSG__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

/// Struct defined in msg/ErpCmdMsg in the package interfaces_control_pkg.
typedef struct interfaces_control_pkg__msg__ErpCmdMsg
{
  /// 긴급 정지 신호
  bool e_stop;
  /// 0: 중립, 1: 전진, 2: 후진
  uint8_t gear;
  /// 0 ~ 200
  uint8_t speed;
  /// ±2000 (조향 각도)
  int32_t steer;
  /// 0 ~ 33
  uint8_t brake;
} interfaces_control_pkg__msg__ErpCmdMsg;

// Struct for a sequence of interfaces_control_pkg__msg__ErpCmdMsg.
typedef struct interfaces_control_pkg__msg__ErpCmdMsg__Sequence
{
  interfaces_control_pkg__msg__ErpCmdMsg * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} interfaces_control_pkg__msg__ErpCmdMsg__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // INTERFACES_CONTROL_PKG__MSG__DETAIL__ERP_CMD_MSG__STRUCT_H_
