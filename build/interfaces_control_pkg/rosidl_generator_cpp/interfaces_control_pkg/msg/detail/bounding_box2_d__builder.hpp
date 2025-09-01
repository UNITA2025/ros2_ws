// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from interfaces_control_pkg:msg/BoundingBox2D.idl
// generated code does not contain a copyright notice

#ifndef INTERFACES_CONTROL_PKG__MSG__DETAIL__BOUNDING_BOX2_D__BUILDER_HPP_
#define INTERFACES_CONTROL_PKG__MSG__DETAIL__BOUNDING_BOX2_D__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "interfaces_control_pkg/msg/detail/bounding_box2_d__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace interfaces_control_pkg
{

namespace msg
{

namespace builder
{

class Init_BoundingBox2D_size
{
public:
  explicit Init_BoundingBox2D_size(::interfaces_control_pkg::msg::BoundingBox2D & msg)
  : msg_(msg)
  {}
  ::interfaces_control_pkg::msg::BoundingBox2D size(::interfaces_control_pkg::msg::BoundingBox2D::_size_type arg)
  {
    msg_.size = std::move(arg);
    return std::move(msg_);
  }

private:
  ::interfaces_control_pkg::msg::BoundingBox2D msg_;
};

class Init_BoundingBox2D_center
{
public:
  Init_BoundingBox2D_center()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_BoundingBox2D_size center(::interfaces_control_pkg::msg::BoundingBox2D::_center_type arg)
  {
    msg_.center = std::move(arg);
    return Init_BoundingBox2D_size(msg_);
  }

private:
  ::interfaces_control_pkg::msg::BoundingBox2D msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::interfaces_control_pkg::msg::BoundingBox2D>()
{
  return interfaces_control_pkg::msg::builder::Init_BoundingBox2D_center();
}

}  // namespace interfaces_control_pkg

#endif  // INTERFACES_CONTROL_PKG__MSG__DETAIL__BOUNDING_BOX2_D__BUILDER_HPP_
