// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from interfaces_control_pkg:msg/ErpCmdMsg.idl
// generated code does not contain a copyright notice

#ifndef INTERFACES_CONTROL_PKG__MSG__DETAIL__ERP_CMD_MSG__TRAITS_HPP_
#define INTERFACES_CONTROL_PKG__MSG__DETAIL__ERP_CMD_MSG__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "interfaces_control_pkg/msg/detail/erp_cmd_msg__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

namespace interfaces_control_pkg
{

namespace msg
{

inline void to_flow_style_yaml(
  const ErpCmdMsg & msg,
  std::ostream & out)
{
  out << "{";
  // member: e_stop
  {
    out << "e_stop: ";
    rosidl_generator_traits::value_to_yaml(msg.e_stop, out);
    out << ", ";
  }

  // member: gear
  {
    out << "gear: ";
    rosidl_generator_traits::value_to_yaml(msg.gear, out);
    out << ", ";
  }

  // member: speed
  {
    out << "speed: ";
    rosidl_generator_traits::value_to_yaml(msg.speed, out);
    out << ", ";
  }

  // member: steer
  {
    out << "steer: ";
    rosidl_generator_traits::value_to_yaml(msg.steer, out);
    out << ", ";
  }

  // member: brake
  {
    out << "brake: ";
    rosidl_generator_traits::value_to_yaml(msg.brake, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const ErpCmdMsg & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: e_stop
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "e_stop: ";
    rosidl_generator_traits::value_to_yaml(msg.e_stop, out);
    out << "\n";
  }

  // member: gear
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "gear: ";
    rosidl_generator_traits::value_to_yaml(msg.gear, out);
    out << "\n";
  }

  // member: speed
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "speed: ";
    rosidl_generator_traits::value_to_yaml(msg.speed, out);
    out << "\n";
  }

  // member: steer
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "steer: ";
    rosidl_generator_traits::value_to_yaml(msg.steer, out);
    out << "\n";
  }

  // member: brake
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "brake: ";
    rosidl_generator_traits::value_to_yaml(msg.brake, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const ErpCmdMsg & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace msg

}  // namespace interfaces_control_pkg

namespace rosidl_generator_traits
{

[[deprecated("use interfaces_control_pkg::msg::to_block_style_yaml() instead")]]
inline void to_yaml(
  const interfaces_control_pkg::msg::ErpCmdMsg & msg,
  std::ostream & out, size_t indentation = 0)
{
  interfaces_control_pkg::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use interfaces_control_pkg::msg::to_yaml() instead")]]
inline std::string to_yaml(const interfaces_control_pkg::msg::ErpCmdMsg & msg)
{
  return interfaces_control_pkg::msg::to_yaml(msg);
}

template<>
inline const char * data_type<interfaces_control_pkg::msg::ErpCmdMsg>()
{
  return "interfaces_control_pkg::msg::ErpCmdMsg";
}

template<>
inline const char * name<interfaces_control_pkg::msg::ErpCmdMsg>()
{
  return "interfaces_control_pkg/msg/ErpCmdMsg";
}

template<>
struct has_fixed_size<interfaces_control_pkg::msg::ErpCmdMsg>
  : std::integral_constant<bool, true> {};

template<>
struct has_bounded_size<interfaces_control_pkg::msg::ErpCmdMsg>
  : std::integral_constant<bool, true> {};

template<>
struct is_message<interfaces_control_pkg::msg::ErpCmdMsg>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // INTERFACES_CONTROL_PKG__MSG__DETAIL__ERP_CMD_MSG__TRAITS_HPP_
