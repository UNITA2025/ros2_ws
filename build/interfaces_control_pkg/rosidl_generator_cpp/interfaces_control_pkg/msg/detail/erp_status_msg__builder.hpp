// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from interfaces_control_pkg:msg/ErpStatusMsg.idl
// generated code does not contain a copyright notice

#ifndef INTERFACES_CONTROL_PKG__MSG__DETAIL__ERP_STATUS_MSG__BUILDER_HPP_
#define INTERFACES_CONTROL_PKG__MSG__DETAIL__ERP_STATUS_MSG__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "interfaces_control_pkg/msg/detail/erp_status_msg__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace interfaces_control_pkg
{

namespace msg
{

namespace builder
{

class Init_ErpStatusMsg_alive
{
public:
  explicit Init_ErpStatusMsg_alive(::interfaces_control_pkg::msg::ErpStatusMsg & msg)
  : msg_(msg)
  {}
  ::interfaces_control_pkg::msg::ErpStatusMsg alive(::interfaces_control_pkg::msg::ErpStatusMsg::_alive_type arg)
  {
    msg_.alive = std::move(arg);
    return std::move(msg_);
  }

private:
  ::interfaces_control_pkg::msg::ErpStatusMsg msg_;
};

class Init_ErpStatusMsg_encoder
{
public:
  explicit Init_ErpStatusMsg_encoder(::interfaces_control_pkg::msg::ErpStatusMsg & msg)
  : msg_(msg)
  {}
  Init_ErpStatusMsg_alive encoder(::interfaces_control_pkg::msg::ErpStatusMsg::_encoder_type arg)
  {
    msg_.encoder = std::move(arg);
    return Init_ErpStatusMsg_alive(msg_);
  }

private:
  ::interfaces_control_pkg::msg::ErpStatusMsg msg_;
};

class Init_ErpStatusMsg_brake
{
public:
  explicit Init_ErpStatusMsg_brake(::interfaces_control_pkg::msg::ErpStatusMsg & msg)
  : msg_(msg)
  {}
  Init_ErpStatusMsg_encoder brake(::interfaces_control_pkg::msg::ErpStatusMsg::_brake_type arg)
  {
    msg_.brake = std::move(arg);
    return Init_ErpStatusMsg_encoder(msg_);
  }

private:
  ::interfaces_control_pkg::msg::ErpStatusMsg msg_;
};

class Init_ErpStatusMsg_steer
{
public:
  explicit Init_ErpStatusMsg_steer(::interfaces_control_pkg::msg::ErpStatusMsg & msg)
  : msg_(msg)
  {}
  Init_ErpStatusMsg_brake steer(::interfaces_control_pkg::msg::ErpStatusMsg::_steer_type arg)
  {
    msg_.steer = std::move(arg);
    return Init_ErpStatusMsg_brake(msg_);
  }

private:
  ::interfaces_control_pkg::msg::ErpStatusMsg msg_;
};

class Init_ErpStatusMsg_speed
{
public:
  explicit Init_ErpStatusMsg_speed(::interfaces_control_pkg::msg::ErpStatusMsg & msg)
  : msg_(msg)
  {}
  Init_ErpStatusMsg_steer speed(::interfaces_control_pkg::msg::ErpStatusMsg::_speed_type arg)
  {
    msg_.speed = std::move(arg);
    return Init_ErpStatusMsg_steer(msg_);
  }

private:
  ::interfaces_control_pkg::msg::ErpStatusMsg msg_;
};

class Init_ErpStatusMsg_gear
{
public:
  explicit Init_ErpStatusMsg_gear(::interfaces_control_pkg::msg::ErpStatusMsg & msg)
  : msg_(msg)
  {}
  Init_ErpStatusMsg_speed gear(::interfaces_control_pkg::msg::ErpStatusMsg::_gear_type arg)
  {
    msg_.gear = std::move(arg);
    return Init_ErpStatusMsg_speed(msg_);
  }

private:
  ::interfaces_control_pkg::msg::ErpStatusMsg msg_;
};

class Init_ErpStatusMsg_e_stop
{
public:
  explicit Init_ErpStatusMsg_e_stop(::interfaces_control_pkg::msg::ErpStatusMsg & msg)
  : msg_(msg)
  {}
  Init_ErpStatusMsg_gear e_stop(::interfaces_control_pkg::msg::ErpStatusMsg::_e_stop_type arg)
  {
    msg_.e_stop = std::move(arg);
    return Init_ErpStatusMsg_gear(msg_);
  }

private:
  ::interfaces_control_pkg::msg::ErpStatusMsg msg_;
};

class Init_ErpStatusMsg_control_mode
{
public:
  Init_ErpStatusMsg_control_mode()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_ErpStatusMsg_e_stop control_mode(::interfaces_control_pkg::msg::ErpStatusMsg::_control_mode_type arg)
  {
    msg_.control_mode = std::move(arg);
    return Init_ErpStatusMsg_e_stop(msg_);
  }

private:
  ::interfaces_control_pkg::msg::ErpStatusMsg msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::interfaces_control_pkg::msg::ErpStatusMsg>()
{
  return interfaces_control_pkg::msg::builder::Init_ErpStatusMsg_control_mode();
}

}  // namespace interfaces_control_pkg

#endif  // INTERFACES_CONTROL_PKG__MSG__DETAIL__ERP_STATUS_MSG__BUILDER_HPP_
