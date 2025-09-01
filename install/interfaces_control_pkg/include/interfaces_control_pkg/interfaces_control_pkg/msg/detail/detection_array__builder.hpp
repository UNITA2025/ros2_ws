// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from interfaces_control_pkg:msg/DetectionArray.idl
// generated code does not contain a copyright notice

#ifndef INTERFACES_CONTROL_PKG__MSG__DETAIL__DETECTION_ARRAY__BUILDER_HPP_
#define INTERFACES_CONTROL_PKG__MSG__DETAIL__DETECTION_ARRAY__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "interfaces_control_pkg/msg/detail/detection_array__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace interfaces_control_pkg
{

namespace msg
{

namespace builder
{

class Init_DetectionArray_detections
{
public:
  explicit Init_DetectionArray_detections(::interfaces_control_pkg::msg::DetectionArray & msg)
  : msg_(msg)
  {}
  ::interfaces_control_pkg::msg::DetectionArray detections(::interfaces_control_pkg::msg::DetectionArray::_detections_type arg)
  {
    msg_.detections = std::move(arg);
    return std::move(msg_);
  }

private:
  ::interfaces_control_pkg::msg::DetectionArray msg_;
};

class Init_DetectionArray_header
{
public:
  Init_DetectionArray_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_DetectionArray_detections header(::interfaces_control_pkg::msg::DetectionArray::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_DetectionArray_detections(msg_);
  }

private:
  ::interfaces_control_pkg::msg::DetectionArray msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::interfaces_control_pkg::msg::DetectionArray>()
{
  return interfaces_control_pkg::msg::builder::Init_DetectionArray_header();
}

}  // namespace interfaces_control_pkg

#endif  // INTERFACES_CONTROL_PKG__MSG__DETAIL__DETECTION_ARRAY__BUILDER_HPP_
