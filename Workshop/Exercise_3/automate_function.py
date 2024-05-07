from pydantic import Field
from speckle_automate import AutomationContext, AutomateBase
from Utilities.helpers import flatten_base, speckle_print

from Workshop.Exercise_3.rules import RevitRules


class FunctionInputs(AutomateBase):
    """These are function author defined values.

    Automate will make sure to supply them matching the types specified here.
    Please use the pydantic model schema to define your inputs:
    https://docs.pydantic.dev/latest/usage/models/
    """

    # In this exercise, we will add two new input fields to the FunctionInputs class.
    category: str = Field(
        title="Revit Category",
        description="This is the category objects to check.",
    )
    property: str = Field(
        title="Property Name",
        description="This is the property to check.",
    )


def automate_function(
    automate_context: AutomationContext,
    function_inputs: FunctionInputs,
) -> None:
    """This version of the function will add a check for the new provide inputs.

    Args:
        automate_context: A context helper object, that carries relevant information
            about the runtime context of this function.
            It gives access to the Speckle project data, that triggered this run.
            It also has convenience methods attach result data to the Speckle model.
        function_inputs: An instance object matching the defined schema.
    """

    # the context provides a convenient way, to receive the triggering version
    version_root_object = automate_context.receive_version()

    # We can continue to work with a flattened list of objects.
    flat_list_of_objects = list(flatten_base(version_root_object))

    # filter to only include objects that are in the specified category
    in_category_objects = [
        speckle_object
        for speckle_object in flat_list_of_objects
        if RevitRules.is_category(speckle_object, function_inputs.category)
    ]

    # check if the property exists on the objects
    non_property_objects = [
        obj
        for obj in in_category_objects
        if not RevitRules.has_parameter(obj, function_inputs.property)
    ]

    property_objects = [
        obj
        for obj in in_category_objects
        if RevitRules.has_parameter(obj, function_inputs.property)
    ]

    # property_objects should be those where while the property is present,
    # is not an empty string or the default value
    valid_property_objects = [
        obj
        for obj in property_objects
        if RevitRules.get_parameter_value(obj, function_inputs.property)
        not in ["", "Default", None]
    ]

    for obj in valid_property_objects:
        speckle_print(RevitRules.get_parameter_value(obj, function_inputs.property))

    # invalid_property_objects property_objects not in valid_property_objects
    invalid_property_objects = [
        obj for obj in property_objects if obj not in valid_property_objects
    ]

    # mark all the non-property objects as failed

    (
        automate_context.attach_error_to_objects(
            category=f"Missing Property {function_inputs.category} Objects",
            object_ids=[obj.id for obj in non_property_objects],
            message=f"This {function_inputs.category} does not have the specified property {function_inputs.property}",
        )
        if non_property_objects
        else None
    )

    # mark all the invalid property objects as warning
    (
        automate_context.attach_warning_to_objects(
            category=f"Invalid Property {function_inputs.category} Objects",
            object_ids=[obj.id for obj in invalid_property_objects],
            message=f"This {function_inputs.category} has the specified property {function_inputs.property} but it is "
            f"empty or default",
        )
        if invalid_property_objects
        else None
    )

    # mark all the property objects as successful
    (
        automate_context.attach_info_to_objects(
            category=f"Valid Property {function_inputs.category} Objects",
            object_ids=[obj.id for obj in property_objects],
            message=f"This {function_inputs.category} has the specified property {function_inputs.property}",
        )
        if property_objects
        else None
    )

    if len(non_property_objects) > 0:
        automate_context.mark_run_failed(
            "Some objects do not have the specified property."
        )
    elif len(invalid_property_objects) > 0:
        automate_context.mark_run_success(
            "Some objects have the specified property but it is empty or default.",
        )

    else:
        automate_context.mark_run_success(
            f"All {function_inputs.category} objects have the {function_inputs.property} property."
        )

    # set the automation context view, to the original model / version view
    automate_context.set_context_view()
