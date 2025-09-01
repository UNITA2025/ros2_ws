// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from interfaces_control_pkg:msg/ConeInfoArray.idl
// generated code does not contain a copyright notice

#ifndef INTERFACES_CONTROL_PKG__MSG__DETAIL__CONE_INFO_ARRAY__BUILDER_HPP_
#define INTERFACES_CONTROL_PKG__MSG__DETAIL__CONE_INFO_ARRAY__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "interfaces_control_pkg/msg/detail/cone_info_array__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace interfaces_control_pkg
{

namespace msg
{

namespace builder
{

class Init_ConeInfoArray_cones
{
public:
  Init_ConeInfoArray_cones()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  ::interfaces_control_pkg::msg::ConeInfoArray cones(::interfaces_control_pkg::msg::ConeInfoArray::_cones_type arg)
  {
    msg_.cones = std::move(arg);
    return std::move(msg_);
  }

private:
  ::interfaces_control_pkg::msg::ConeInfoArray msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::interfaces_control_pkg::msg::ConeInfoArray>()
{
  return interfaces_control_pkg::msg::builder::Init_ConeInfoArray_cones();
}

}  // namespace interfaces_control_pkg

#endif  // INTERFACES_CONTROL_PKG__MSG__DETAIL__CONE_INFO_ARRAY__BUILDER_HPP_
