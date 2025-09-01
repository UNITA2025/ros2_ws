// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from interfaces_control_pkg:msg/ConeInfoArray.idl
// generated code does not contain a copyright notice

#ifndef INTERFACES_CONTROL_PKG__MSG__DETAIL__CONE_INFO_ARRAY__TRAITS_HPP_
#define INTERFACES_CONTROL_PKG__MSG__DETAIL__CONE_INFO_ARRAY__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "interfaces_control_pkg/msg/detail/cone_info_array__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'cones'
#include "interfaces_control_pkg/msg/detail/cone_info__traits.hpp"

namespace interfaces_control_pkg
{

namespace msg
{

inline void to_flow_style_yaml(
  const ConeInfoArray & msg,
  std::ostream & out)
{
  out << "{";
  // member: cones
  {
    if (msg.cones.size() == 0) {
      out << "cones: []";
    } else {
      out << "cones: [";
      size_t pending_items = msg.cones.size();
      for (auto item : msg.cones) {
        to_flow_style_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const ConeInfoArray & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: cones
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.cones.size() == 0) {
      out << "cones: []\n";
    } else {
      out << "cones:\n";
      for (auto item : msg.cones) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "-\n";
        to_block_style_yaml(item, out, indentation + 2);
      }
    }
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const ConeInfoArray & msg, bool use_flow_style = false)
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
  const interfaces_control_pkg::msg::ConeInfoArray & msg,
  std::ostream & out, size_t indentation = 0)
{
  interfaces_control_pkg::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use interfaces_control_pkg::msg::to_yaml() instead")]]
inline std::string to_yaml(const interfaces_control_pkg::msg::ConeInfoArray & msg)
{
  return interfaces_control_pkg::msg::to_yaml(msg);
}

template<>
inline const char * data_type<interfaces_control_pkg::msg::ConeInfoArray>()
{
  return "interfaces_control_pkg::msg::ConeInfoArray";
}

template<>
inline const char * name<interfaces_control_pkg::msg::ConeInfoArray>()
{
  return "interfaces_control_pkg/msg/ConeInfoArray";
}

template<>
struct has_fixed_size<interfaces_control_pkg::msg::ConeInfoArray>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<interfaces_control_pkg::msg::ConeInfoArray>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<interfaces_control_pkg::msg::ConeInfoArray>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // INTERFACES_CONTROL_PKG__MSG__DETAIL__CONE_INFO_ARRAY__TRAITS_HPP_
