// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from interfaces_control_pkg:msg/ConeInfoArray.idl
// generated code does not contain a copyright notice

#ifndef INTERFACES_CONTROL_PKG__MSG__DETAIL__CONE_INFO_ARRAY__STRUCT_HPP_
#define INTERFACES_CONTROL_PKG__MSG__DETAIL__CONE_INFO_ARRAY__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


// Include directives for member types
// Member 'cones'
#include "interfaces_control_pkg/msg/detail/cone_info__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__interfaces_control_pkg__msg__ConeInfoArray __attribute__((deprecated))
#else
# define DEPRECATED__interfaces_control_pkg__msg__ConeInfoArray __declspec(deprecated)
#endif

namespace interfaces_control_pkg
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct ConeInfoArray_
{
  using Type = ConeInfoArray_<ContainerAllocator>;

  explicit ConeInfoArray_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    (void)_init;
  }

  explicit ConeInfoArray_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    (void)_init;
    (void)_alloc;
  }

  // field types and members
  using _cones_type =
    std::vector<interfaces_control_pkg::msg::ConeInfo_<ContainerAllocator>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<interfaces_control_pkg::msg::ConeInfo_<ContainerAllocator>>>;
  _cones_type cones;

  // setters for named parameter idiom
  Type & set__cones(
    const std::vector<interfaces_control_pkg::msg::ConeInfo_<ContainerAllocator>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<interfaces_control_pkg::msg::ConeInfo_<ContainerAllocator>>> & _arg)
  {
    this->cones = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    interfaces_control_pkg::msg::ConeInfoArray_<ContainerAllocator> *;
  using ConstRawPtr =
    const interfaces_control_pkg::msg::ConeInfoArray_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<interfaces_control_pkg::msg::ConeInfoArray_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<interfaces_control_pkg::msg::ConeInfoArray_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      interfaces_control_pkg::msg::ConeInfoArray_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<interfaces_control_pkg::msg::ConeInfoArray_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      interfaces_control_pkg::msg::ConeInfoArray_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<interfaces_control_pkg::msg::ConeInfoArray_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<interfaces_control_pkg::msg::ConeInfoArray_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<interfaces_control_pkg::msg::ConeInfoArray_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__interfaces_control_pkg__msg__ConeInfoArray
    std::shared_ptr<interfaces_control_pkg::msg::ConeInfoArray_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__interfaces_control_pkg__msg__ConeInfoArray
    std::shared_ptr<interfaces_control_pkg::msg::ConeInfoArray_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const ConeInfoArray_ & other) const
  {
    if (this->cones != other.cones) {
      return false;
    }
    return true;
  }
  bool operator!=(const ConeInfoArray_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct ConeInfoArray_

// alias to use template instance with default allocator
using ConeInfoArray =
  interfaces_control_pkg::msg::ConeInfoArray_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace interfaces_control_pkg

#endif  // INTERFACES_CONTROL_PKG__MSG__DETAIL__CONE_INFO_ARRAY__STRUCT_HPP_
