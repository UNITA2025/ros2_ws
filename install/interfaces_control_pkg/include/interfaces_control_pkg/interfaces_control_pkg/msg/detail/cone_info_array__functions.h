// generated from rosidl_generator_c/resource/idl__functions.h.em
// with input from interfaces_control_pkg:msg/ConeInfoArray.idl
// generated code does not contain a copyright notice

#ifndef INTERFACES_CONTROL_PKG__MSG__DETAIL__CONE_INFO_ARRAY__FUNCTIONS_H_
#define INTERFACES_CONTROL_PKG__MSG__DETAIL__CONE_INFO_ARRAY__FUNCTIONS_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stdlib.h>

#include "rosidl_runtime_c/visibility_control.h"
#include "interfaces_control_pkg/msg/rosidl_generator_c__visibility_control.h"

#include "interfaces_control_pkg/msg/detail/cone_info_array__struct.h"

/// Initialize msg/ConeInfoArray message.
/**
 * If the init function is called twice for the same message without
 * calling fini inbetween previously allocated memory will be leaked.
 * \param[in,out] msg The previously allocated message pointer.
 * Fields without a default value will not be initialized by this function.
 * You might want to call memset(msg, 0, sizeof(
 * interfaces_control_pkg__msg__ConeInfoArray
 * )) before or use
 * interfaces_control_pkg__msg__ConeInfoArray__create()
 * to allocate and initialize the message.
 * \return true if initialization was successful, otherwise false
 */
ROSIDL_GENERATOR_C_PUBLIC_interfaces_control_pkg
bool
interfaces_control_pkg__msg__ConeInfoArray__init(interfaces_control_pkg__msg__ConeInfoArray * msg);

/// Finalize msg/ConeInfoArray message.
/**
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_interfaces_control_pkg
void
interfaces_control_pkg__msg__ConeInfoArray__fini(interfaces_control_pkg__msg__ConeInfoArray * msg);

/// Create msg/ConeInfoArray message.
/**
 * It allocates the memory for the message, sets the memory to zero, and
 * calls
 * interfaces_control_pkg__msg__ConeInfoArray__init().
 * \return The pointer to the initialized message if successful,
 * otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_interfaces_control_pkg
interfaces_control_pkg__msg__ConeInfoArray *
interfaces_control_pkg__msg__ConeInfoArray__create();

/// Destroy msg/ConeInfoArray message.
/**
 * It calls
 * interfaces_control_pkg__msg__ConeInfoArray__fini()
 * and frees the memory of the message.
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_interfaces_control_pkg
void
interfaces_control_pkg__msg__ConeInfoArray__destroy(interfaces_control_pkg__msg__ConeInfoArray * msg);

/// Check for msg/ConeInfoArray message equality.
/**
 * \param[in] lhs The message on the left hand size of the equality operator.
 * \param[in] rhs The message on the right hand size of the equality operator.
 * \return true if messages are equal, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_interfaces_control_pkg
bool
interfaces_control_pkg__msg__ConeInfoArray__are_equal(const interfaces_control_pkg__msg__ConeInfoArray * lhs, const interfaces_control_pkg__msg__ConeInfoArray * rhs);

/// Copy a msg/ConeInfoArray message.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source message pointer.
 * \param[out] output The target message pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer is null
 *   or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_interfaces_control_pkg
bool
interfaces_control_pkg__msg__ConeInfoArray__copy(
  const interfaces_control_pkg__msg__ConeInfoArray * input,
  interfaces_control_pkg__msg__ConeInfoArray * output);

/// Initialize array of msg/ConeInfoArray messages.
/**
 * It allocates the memory for the number of elements and calls
 * interfaces_control_pkg__msg__ConeInfoArray__init()
 * for each element of the array.
 * \param[in,out] array The allocated array pointer.
 * \param[in] size The size / capacity of the array.
 * \return true if initialization was successful, otherwise false
 * If the array pointer is valid and the size is zero it is guaranteed
 # to return true.
 */
ROSIDL_GENERATOR_C_PUBLIC_interfaces_control_pkg
bool
interfaces_control_pkg__msg__ConeInfoArray__Sequence__init(interfaces_control_pkg__msg__ConeInfoArray__Sequence * array, size_t size);

/// Finalize array of msg/ConeInfoArray messages.
/**
 * It calls
 * interfaces_control_pkg__msg__ConeInfoArray__fini()
 * for each element of the array and frees the memory for the number of
 * elements.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_interfaces_control_pkg
void
interfaces_control_pkg__msg__ConeInfoArray__Sequence__fini(interfaces_control_pkg__msg__ConeInfoArray__Sequence * array);

/// Create array of msg/ConeInfoArray messages.
/**
 * It allocates the memory for the array and calls
 * interfaces_control_pkg__msg__ConeInfoArray__Sequence__init().
 * \param[in] size The size / capacity of the array.
 * \return The pointer to the initialized array if successful, otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_interfaces_control_pkg
interfaces_control_pkg__msg__ConeInfoArray__Sequence *
interfaces_control_pkg__msg__ConeInfoArray__Sequence__create(size_t size);

/// Destroy array of msg/ConeInfoArray messages.
/**
 * It calls
 * interfaces_control_pkg__msg__ConeInfoArray__Sequence__fini()
 * on the array,
 * and frees the memory of the array.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_interfaces_control_pkg
void
interfaces_control_pkg__msg__ConeInfoArray__Sequence__destroy(interfaces_control_pkg__msg__ConeInfoArray__Sequence * array);

/// Check for msg/ConeInfoArray message array equality.
/**
 * \param[in] lhs The message array on the left hand size of the equality operator.
 * \param[in] rhs The message array on the right hand size of the equality operator.
 * \return true if message arrays are equal in size and content, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_interfaces_control_pkg
bool
interfaces_control_pkg__msg__ConeInfoArray__Sequence__are_equal(const interfaces_control_pkg__msg__ConeInfoArray__Sequence * lhs, const interfaces_control_pkg__msg__ConeInfoArray__Sequence * rhs);

/// Copy an array of msg/ConeInfoArray messages.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source array pointer.
 * \param[out] output The target array pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer
 *   is null or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_interfaces_control_pkg
bool
interfaces_control_pkg__msg__ConeInfoArray__Sequence__copy(
  const interfaces_control_pkg__msg__ConeInfoArray__Sequence * input,
  interfaces_control_pkg__msg__ConeInfoArray__Sequence * output);

#ifdef __cplusplus
}
#endif

#endif  // INTERFACES_CONTROL_PKG__MSG__DETAIL__CONE_INFO_ARRAY__FUNCTIONS_H_
