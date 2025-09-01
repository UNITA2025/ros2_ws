// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from interfaces_control_pkg:msg/ConeInfo.idl
// generated code does not contain a copyright notice

#ifndef INTERFACES_CONTROL_PKG__MSG__DETAIL__CONE_INFO__BUILDER_HPP_
#define INTERFACES_CONTROL_PKG__MSG__DETAIL__CONE_INFO__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "interfaces_control_pkg/msg/detail/cone_info__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace interfaces_control_pkg
{

namespace msg
{

namespace builder
{

class Init_ConeInfo_cone_color
{
public:
  explicit Init_ConeInfo_cone_color(::interfaces_control_pkg::msg::ConeInfo & msg)
  : msg_(msg)
  {}
  ::interfaces_control_pkg::msg::ConeInfo cone_color(::interfaces_control_pkg::msg::ConeInfo::_cone_color_type arg)
  {
    msg_.cone_color = std::move(arg);
    return std::move(msg_);
  }

private:
  ::interfaces_control_pkg::msg::ConeInfo msg_;
};

class Init_ConeInfo_distance
{
public:
  explicit Init_ConeInfo_distance(::interfaces_control_pkg::msg::ConeInfo & msg)
  : msg_(msg)
  {}
  Init_ConeInfo_cone_color distance(::interfaces_control_pkg::msg::ConeInfo::_distance_type arg)
  {
    msg_.distance = std::move(arg);
    return Init_ConeInfo_cone_color(msg_);
  }

private:
  ::interfaces_control_pkg::msg::ConeInfo msg_;
};

class Init_ConeInfo_z
{
public:
  explicit Init_ConeInfo_z(::interfaces_control_pkg::msg::ConeInfo & msg)
  : msg_(msg)
  {}
  Init_ConeInfo_distance z(::interfaces_control_pkg::msg::ConeInfo::_z_type arg)
  {
    msg_.z = std::move(arg);
    return Init_ConeInfo_distance(msg_);
  }

private:
  ::interfaces_control_pkg::msg::ConeInfo msg_;
};

class Init_ConeInfo_y
{
public:
  explicit Init_ConeInfo_y(::interfaces_control_pkg::msg::ConeInfo & msg)
  : msg_(msg)
  {}
  Init_ConeInfo_z y(::interfaces_control_pkg::msg::ConeInfo::_y_type arg)
  {
    msg_.y = std::move(arg);
    return Init_ConeInfo_z(msg_);
  }

private:
  ::interfaces_control_pkg::msg::ConeInfo msg_;
};

class Init_ConeInfo_x
{
public:
  Init_ConeInfo_x()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_ConeInfo_y x(::interfaces_control_pkg::msg::ConeInfo::_x_type arg)
  {
    msg_.x = std::move(arg);
    return Init_ConeInfo_y(msg_);
  }

private:
  ::interfaces_control_pkg::msg::ConeInfo msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::interfaces_control_pkg::msg::ConeInfo>()
{
  return interfaces_control_pkg::msg::builder::Init_ConeInfo_x();
}

}  // namespace interfaces_control_pkg

#endif  // INTERFACES_CONTROL_PKG__MSG__DETAIL__CONE_INFO__BUILDER_HPP_
