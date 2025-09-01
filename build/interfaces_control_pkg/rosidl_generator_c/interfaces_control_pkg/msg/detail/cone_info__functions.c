// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from interfaces_control_pkg:msg/ConeInfo.idl
// generated code does not contain a copyright notice
#include "interfaces_control_pkg/msg/detail/cone_info__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `cone_color`
#include "rosidl_runtime_c/string_functions.h"

bool
interfaces_control_pkg__msg__ConeInfo__init(interfaces_control_pkg__msg__ConeInfo * msg)
{
  if (!msg) {
    return false;
  }
  // x
  // y
  // z
  // distance
  // cone_color
  if (!rosidl_runtime_c__String__init(&msg->cone_color)) {
    interfaces_control_pkg__msg__ConeInfo__fini(msg);
    return false;
  }
  return true;
}

void
interfaces_control_pkg__msg__ConeInfo__fini(interfaces_control_pkg__msg__ConeInfo * msg)
{
  if (!msg) {
    return;
  }
  // x
  // y
  // z
  // distance
  // cone_color
  rosidl_runtime_c__String__fini(&msg->cone_color);
}

bool
interfaces_control_pkg__msg__ConeInfo__are_equal(const interfaces_control_pkg__msg__ConeInfo * lhs, const interfaces_control_pkg__msg__ConeInfo * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // x
  if (lhs->x != rhs->x) {
    return false;
  }
  // y
  if (lhs->y != rhs->y) {
    return false;
  }
  // z
  if (lhs->z != rhs->z) {
    return false;
  }
  // distance
  if (lhs->distance != rhs->distance) {
    return false;
  }
  // cone_color
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->cone_color), &(rhs->cone_color)))
  {
    return false;
  }
  return true;
}

bool
interfaces_control_pkg__msg__ConeInfo__copy(
  const interfaces_control_pkg__msg__ConeInfo * input,
  interfaces_control_pkg__msg__ConeInfo * output)
{
  if (!input || !output) {
    return false;
  }
  // x
  output->x = input->x;
  // y
  output->y = input->y;
  // z
  output->z = input->z;
  // distance
  output->distance = input->distance;
  // cone_color
  if (!rosidl_runtime_c__String__copy(
      &(input->cone_color), &(output->cone_color)))
  {
    return false;
  }
  return true;
}

interfaces_control_pkg__msg__ConeInfo *
interfaces_control_pkg__msg__ConeInfo__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  interfaces_control_pkg__msg__ConeInfo * msg = (interfaces_control_pkg__msg__ConeInfo *)allocator.allocate(sizeof(interfaces_control_pkg__msg__ConeInfo), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(interfaces_control_pkg__msg__ConeInfo));
  bool success = interfaces_control_pkg__msg__ConeInfo__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
interfaces_control_pkg__msg__ConeInfo__destroy(interfaces_control_pkg__msg__ConeInfo * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    interfaces_control_pkg__msg__ConeInfo__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
interfaces_control_pkg__msg__ConeInfo__Sequence__init(interfaces_control_pkg__msg__ConeInfo__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  interfaces_control_pkg__msg__ConeInfo * data = NULL;

  if (size) {
    data = (interfaces_control_pkg__msg__ConeInfo *)allocator.zero_allocate(size, sizeof(interfaces_control_pkg__msg__ConeInfo), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = interfaces_control_pkg__msg__ConeInfo__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        interfaces_control_pkg__msg__ConeInfo__fini(&data[i - 1]);
      }
      allocator.deallocate(data, allocator.state);
      return false;
    }
  }
  array->data = data;
  array->size = size;
  array->capacity = size;
  return true;
}

void
interfaces_control_pkg__msg__ConeInfo__Sequence__fini(interfaces_control_pkg__msg__ConeInfo__Sequence * array)
{
  if (!array) {
    return;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();

  if (array->data) {
    // ensure that data and capacity values are consistent
    assert(array->capacity > 0);
    // finalize all array elements
    for (size_t i = 0; i < array->capacity; ++i) {
      interfaces_control_pkg__msg__ConeInfo__fini(&array->data[i]);
    }
    allocator.deallocate(array->data, allocator.state);
    array->data = NULL;
    array->size = 0;
    array->capacity = 0;
  } else {
    // ensure that data, size, and capacity values are consistent
    assert(0 == array->size);
    assert(0 == array->capacity);
  }
}

interfaces_control_pkg__msg__ConeInfo__Sequence *
interfaces_control_pkg__msg__ConeInfo__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  interfaces_control_pkg__msg__ConeInfo__Sequence * array = (interfaces_control_pkg__msg__ConeInfo__Sequence *)allocator.allocate(sizeof(interfaces_control_pkg__msg__ConeInfo__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = interfaces_control_pkg__msg__ConeInfo__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
interfaces_control_pkg__msg__ConeInfo__Sequence__destroy(interfaces_control_pkg__msg__ConeInfo__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    interfaces_control_pkg__msg__ConeInfo__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
interfaces_control_pkg__msg__ConeInfo__Sequence__are_equal(const interfaces_control_pkg__msg__ConeInfo__Sequence * lhs, const interfaces_control_pkg__msg__ConeInfo__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!interfaces_control_pkg__msg__ConeInfo__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
interfaces_control_pkg__msg__ConeInfo__Sequence__copy(
  const interfaces_control_pkg__msg__ConeInfo__Sequence * input,
  interfaces_control_pkg__msg__ConeInfo__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(interfaces_control_pkg__msg__ConeInfo);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    interfaces_control_pkg__msg__ConeInfo * data =
      (interfaces_control_pkg__msg__ConeInfo *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!interfaces_control_pkg__msg__ConeInfo__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          interfaces_control_pkg__msg__ConeInfo__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!interfaces_control_pkg__msg__ConeInfo__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
