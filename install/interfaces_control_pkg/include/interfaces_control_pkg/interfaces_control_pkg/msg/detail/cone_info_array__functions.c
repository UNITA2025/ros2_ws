// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from interfaces_control_pkg:msg/ConeInfoArray.idl
// generated code does not contain a copyright notice
#include "interfaces_control_pkg/msg/detail/cone_info_array__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `cones`
#include "interfaces_control_pkg/msg/detail/cone_info__functions.h"

bool
interfaces_control_pkg__msg__ConeInfoArray__init(interfaces_control_pkg__msg__ConeInfoArray * msg)
{
  if (!msg) {
    return false;
  }
  // cones
  if (!interfaces_control_pkg__msg__ConeInfo__Sequence__init(&msg->cones, 0)) {
    interfaces_control_pkg__msg__ConeInfoArray__fini(msg);
    return false;
  }
  return true;
}

void
interfaces_control_pkg__msg__ConeInfoArray__fini(interfaces_control_pkg__msg__ConeInfoArray * msg)
{
  if (!msg) {
    return;
  }
  // cones
  interfaces_control_pkg__msg__ConeInfo__Sequence__fini(&msg->cones);
}

bool
interfaces_control_pkg__msg__ConeInfoArray__are_equal(const interfaces_control_pkg__msg__ConeInfoArray * lhs, const interfaces_control_pkg__msg__ConeInfoArray * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // cones
  if (!interfaces_control_pkg__msg__ConeInfo__Sequence__are_equal(
      &(lhs->cones), &(rhs->cones)))
  {
    return false;
  }
  return true;
}

bool
interfaces_control_pkg__msg__ConeInfoArray__copy(
  const interfaces_control_pkg__msg__ConeInfoArray * input,
  interfaces_control_pkg__msg__ConeInfoArray * output)
{
  if (!input || !output) {
    return false;
  }
  // cones
  if (!interfaces_control_pkg__msg__ConeInfo__Sequence__copy(
      &(input->cones), &(output->cones)))
  {
    return false;
  }
  return true;
}

interfaces_control_pkg__msg__ConeInfoArray *
interfaces_control_pkg__msg__ConeInfoArray__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  interfaces_control_pkg__msg__ConeInfoArray * msg = (interfaces_control_pkg__msg__ConeInfoArray *)allocator.allocate(sizeof(interfaces_control_pkg__msg__ConeInfoArray), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(interfaces_control_pkg__msg__ConeInfoArray));
  bool success = interfaces_control_pkg__msg__ConeInfoArray__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
interfaces_control_pkg__msg__ConeInfoArray__destroy(interfaces_control_pkg__msg__ConeInfoArray * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    interfaces_control_pkg__msg__ConeInfoArray__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
interfaces_control_pkg__msg__ConeInfoArray__Sequence__init(interfaces_control_pkg__msg__ConeInfoArray__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  interfaces_control_pkg__msg__ConeInfoArray * data = NULL;

  if (size) {
    data = (interfaces_control_pkg__msg__ConeInfoArray *)allocator.zero_allocate(size, sizeof(interfaces_control_pkg__msg__ConeInfoArray), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = interfaces_control_pkg__msg__ConeInfoArray__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        interfaces_control_pkg__msg__ConeInfoArray__fini(&data[i - 1]);
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
interfaces_control_pkg__msg__ConeInfoArray__Sequence__fini(interfaces_control_pkg__msg__ConeInfoArray__Sequence * array)
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
      interfaces_control_pkg__msg__ConeInfoArray__fini(&array->data[i]);
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

interfaces_control_pkg__msg__ConeInfoArray__Sequence *
interfaces_control_pkg__msg__ConeInfoArray__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  interfaces_control_pkg__msg__ConeInfoArray__Sequence * array = (interfaces_control_pkg__msg__ConeInfoArray__Sequence *)allocator.allocate(sizeof(interfaces_control_pkg__msg__ConeInfoArray__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = interfaces_control_pkg__msg__ConeInfoArray__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
interfaces_control_pkg__msg__ConeInfoArray__Sequence__destroy(interfaces_control_pkg__msg__ConeInfoArray__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    interfaces_control_pkg__msg__ConeInfoArray__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
interfaces_control_pkg__msg__ConeInfoArray__Sequence__are_equal(const interfaces_control_pkg__msg__ConeInfoArray__Sequence * lhs, const interfaces_control_pkg__msg__ConeInfoArray__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!interfaces_control_pkg__msg__ConeInfoArray__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
interfaces_control_pkg__msg__ConeInfoArray__Sequence__copy(
  const interfaces_control_pkg__msg__ConeInfoArray__Sequence * input,
  interfaces_control_pkg__msg__ConeInfoArray__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(interfaces_control_pkg__msg__ConeInfoArray);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    interfaces_control_pkg__msg__ConeInfoArray * data =
      (interfaces_control_pkg__msg__ConeInfoArray *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!interfaces_control_pkg__msg__ConeInfoArray__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          interfaces_control_pkg__msg__ConeInfoArray__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!interfaces_control_pkg__msg__ConeInfoArray__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
