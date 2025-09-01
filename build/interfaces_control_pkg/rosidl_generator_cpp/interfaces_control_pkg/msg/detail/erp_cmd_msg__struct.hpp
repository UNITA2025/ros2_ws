// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from interfaces_control_pkg:msg/ErpCmdMsg.idl
// generated code does not contain a copyright notice

#ifndef INTERFACES_CONTROL_PKG__MSG__DETAIL__ERP_CMD_MSG__STRUCT_HPP_
#define INTERFACES_CONTROL_PKG__MSG__DETAIL__ERP_CMD_MSG__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


#ifndef _WIN32
# define DEPRECATED__interfaces_control_pkg__msg__ErpCmdMsg __attribute__((deprecated))
#else
# define DEPRECATED__interfaces_control_pkg__msg__ErpCmdMsg __declspec(deprecated)
#endif

namespace interfaces_control_pkg
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct ErpCmdMsg_
{
  using Type = ErpCmdMsg_<ContainerAllocator>;

  explicit ErpCmdMsg_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->e_stop = false;
      this->gear = 0;
      this->speed = 0;
      this->steer = 0l;
      this->brake = 0;
    }
  }

  explicit ErpCmdMsg_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    (void)_alloc;
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->e_stop = false;
      this->gear = 0;
      this->speed = 0;
      this->steer = 0l;
      this->brake = 0;
    }
  }

  // field types and members
  using _e_stop_type =
    bool;
  _e_stop_type e_stop;
  using _gear_type =
    uint8_t;
  _gear_type gear;
  using _speed_type =
    uint8_t;
  _speed_type speed;
  using _steer_type =
    int32_t;
  _steer_type steer;
  using _brake_type =
    uint8_t;
  _brake_type brake;

  // setters for named parameter idiom
  Type & set__e_stop(
    const bool & _arg)
  {
    this->e_stop = _arg;
    return *this;
  }
  Type & set__gear(
    const uint8_t & _arg)
  {
    this->gear = _arg;
    return *this;
  }
  Type & set__speed(
    const uint8_t & _arg)
  {
    this->speed = _arg;
    return *this;
  }
  Type & set__steer(
    const int32_t & _arg)
  {
    this->steer = _arg;
    return *this;
  }
  Type & set__brake(
    const uint8_t & _arg)
  {
    this->brake = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    interfaces_control_pkg::msg::ErpCmdMsg_<ContainerAllocator> *;
  using ConstRawPtr =
    const interfaces_control_pkg::msg::ErpCmdMsg_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<interfaces_control_pkg::msg::ErpCmdMsg_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<interfaces_control_pkg::msg::ErpCmdMsg_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      interfaces_control_pkg::msg::ErpCmdMsg_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<interfaces_control_pkg::msg::ErpCmdMsg_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      interfaces_control_pkg::msg::ErpCmdMsg_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<interfaces_control_pkg::msg::ErpCmdMsg_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<interfaces_control_pkg::msg::ErpCmdMsg_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<interfaces_control_pkg::msg::ErpCmdMsg_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__interfaces_control_pkg__msg__ErpCmdMsg
    std::shared_ptr<interfaces_control_pkg::msg::ErpCmdMsg_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__interfaces_control_pkg__msg__ErpCmdMsg
    std::shared_ptr<interfaces_control_pkg::msg::ErpCmdMsg_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const ErpCmdMsg_ & other) const
  {
    if (this->e_stop != other.e_stop) {
      return false;
    }
    if (this->gear != other.gear) {
      return false;
    }
    if (this->speed != other.speed) {
      return false;
    }
    if (this->steer != other.steer) {
      return false;
    }
    if (this->brake != other.brake) {
      return false;
    }
    return true;
  }
  bool operator!=(const ErpCmdMsg_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct ErpCmdMsg_

// alias to use template instance with default allocator
using ErpCmdMsg =
  interfaces_control_pkg::msg::ErpCmdMsg_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace interfaces_control_pkg

#endif  // INTERFACES_CONTROL_PKG__MSG__DETAIL__ERP_CMD_MSG__STRUCT_HPP_
