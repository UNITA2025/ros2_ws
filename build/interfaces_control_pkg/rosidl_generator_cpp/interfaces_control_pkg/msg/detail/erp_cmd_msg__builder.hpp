// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from interfaces_control_pkg:msg/ErpCmdMsg.idl
// generated code does not contain a copyright notice

#ifndef INTERFACES_CONTROL_PKG__MSG__DETAIL__ERP_CMD_MSG__BUILDER_HPP_
#define INTERFACES_CONTROL_PKG__MSG__DETAIL__ERP_CMD_MSG__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "interfaces_control_pkg/msg/detail/erp_cmd_msg__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace interfaces_control_pkg
{

namespace msg
{

namespace builder
{

class Init_ErpCmdMsg_brake
{
public:
  explicit Init_ErpCmdMsg_brake(::interfaces_control_pkg::msg::ErpCmdMsg & msg)
  : msg_(msg)
  {}
  ::interfaces_control_pkg::msg::ErpCmdMsg brake(::interfaces_control_pkg::msg::ErpCmdMsg::_brake_type arg)
  {
    msg_.brake = std::move(arg);
    return std::move(msg_);
  }

private:
  ::interfaces_control_pkg::msg::ErpCmdMsg msg_;
};

class Init_ErpCmdMsg_steer
{
public:
  explicit Init_ErpCmdMsg_steer(::interfaces_control_pkg::msg::ErpCmdMsg & msg)
  : msg_(msg)
  {}
  Init_ErpCmdMsg_brake steer(::interfaces_control_pkg::msg::ErpCmdMsg::_steer_type arg)
  {
    msg_.steer = std::move(arg);
    return Init_ErpCmdMsg_brake(msg_);
  }

private:
  ::interfaces_control_pkg::msg::ErpCmdMsg msg_;
};

class Init_ErpCmdMsg_speed
{
public:
  explicit Init_ErpCmdMsg_speed(::interfaces_control_pkg::msg::ErpCmdMsg & msg)
  : msg_(msg)
  {}
  Init_ErpCmdMsg_steer speed(::interfaces_control_pkg::msg::ErpCmdMsg::_speed_type arg)
  {
    msg_.speed = std::move(arg);
    return Init_ErpCmdMsg_steer(msg_);
  }

private:
  ::interfaces_control_pkg::msg::ErpCmdMsg msg_;
};

class Init_ErpCmdMsg_gear
{
public:
  explicit Init_ErpCmdMsg_gear(::interfaces_control_pkg::msg::ErpCmdMsg & msg)
  : msg_(msg)
  {}
  Init_ErpCmdMsg_speed gear(::interfaces_control_pkg::msg::ErpCmdMsg::_gear_type arg)
  {
    msg_.gear = std::move(arg);
    return Init_ErpCmdMsg_speed(msg_);
  }

private:
  ::interfaces_control_pkg::msg::ErpCmdMsg msg_;
};

class Init_ErpCmdMsg_e_stop
{
public:
  Init_ErpCmdMsg_e_stop()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_ErpCmdMsg_gear e_stop(::interfaces_control_pkg::msg::ErpCmdMsg::_e_stop_type arg)
  {
    msg_.e_stop = std::move(arg);
    return Init_ErpCmdMsg_gear(msg_);
  }

private:
  ::interfaces_control_pkg::msg::ErpCmdMsg msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::interfaces_control_pkg::msg::ErpCmdMsg>()
{
  return interfaces_control_pkg::msg::builder::Init_ErpCmdMsg_e_stop();
}

}  // namespace interfaces_control_pkg

#endif  // INTERFACES_CONTROL_PKG__MSG__DETAIL__ERP_CMD_MSG__BUILDER_HPP_
