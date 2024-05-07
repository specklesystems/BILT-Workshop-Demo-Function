from pydantic import Field
from speckle_automate import AutomationContext, AutomateBase
from Utilities.helpers import flatten_base, speckle_print
import random


class FunctionInputs(AutomateBase):
    """These are function author defined values.

    Automate will make sure to supply them matching the types specified here.
    Please use the pydantic model schema to define your inputs:
    https://docs.pydantic.dev/latest/usage/models/
    """

    comment_phrase: str = Field(
        title="Comment Phrase",
        description="This phrase will be added to a random model element.",
    )

    # We now want to specify the number of elements to which the comment phrase will be added.
    number_of_elements: int = Field(
        title="Number of Elements",
        description="The number of elements to which the comment phrase will be added.",
    )


def automate_function(
    automate_context: AutomationContext,
    function_inputs: FunctionInputs,
) -> None:
    """This is an example Speckle Automate function.

    Args:
        automate_context: A context helper object, that carries relevant information
            about the runtime context of this function.
            It gives access to the Speckle project data, that triggered this run.
            It also has convenience methods attach result data to the Speckle model.
        function_inputs: An instance object matching the defined schema.
    """

    # the context provides a convenient way, to receive the triggering version
    version_root_object = automate_context.receive_version()

    flat_list_of_objects = list(flatten_base(version_root_object))

    # filter the list to only include objects that are displayable.
    # this is a simple example, that checks if the object has a displayValue
    displayable_objects = [
        speckle_object
        for speckle_object in flat_list_of_objects
        if (
            getattr(speckle_object, "displayValue", None)
            or getattr(speckle_object, "@displayValue", None)
        )
        and getattr(speckle_object, "id", None) is not None
    ]

    # a better displayable_objects should also include those instance objects that have a definition property
    # that cross-references to a speckle id, that is in turn displayable, so we need to add those objects to the list
    displayable_objects += [
        instance_object
        for instance_object in flat_list_of_objects
        if (
            getattr(instance_object, "definition", None)
            and (
                (
                    getattr(
                        getattr(instance_object, "definition"), "displayValue", None
                    )
                    or getattr(
                        getattr(instance_object, "definition"), "@displayValue", None
                    )
                )
                and getattr(getattr(instance_object, "definition"), "id", None)
                is not None
            )
        )
    ]

    if len(displayable_objects) == 0:
        automate_context.mark_run_failed(
            "Automation failed: No displayable objects found."
        )

    else:
        # select a random object from the list
        # random_object = random.choice(displayable_objects)

        # instead of a single object we will select a random subset of displayable objects from the provided dataset
        real_number_of_elements = min(
            # We cant take more elements than we have
            function_inputs.number_of_elements,
            len(displayable_objects),
        )

        selected_objects = random.sample(
            displayable_objects,
            real_number_of_elements,
        )

        # create a list of object ids for all selected objects
        selected_object_ids = [obj.id for obj in selected_objects]

        # ACTIONS

        # attach comment phrase to all selected objects
        # it is possible to attach the same comment phrase to multiple objects
        # the category "Selected Objects" is used to group the objects in the viewer
        # grouping results in this way is a clean way to organize the objects in the viewer
        comment_message = f"{function_inputs.comment_phrase}"
        automate_context.attach_info_to_objects(
            category="Selected Objects",
            object_ids=selected_object_ids,
            message=comment_message,
        )

        # attach index as gradient value for all selected objects. this will be used for visualisation purposes
        # the category "Index Visualisation" is used to group the objects in the viewer
        gradient_values = {
            object_id: {"gradientValue": index + 1}
            for index, object_id in enumerate(selected_object_ids)
        }

        automate_context.attach_info_to_objects(
            category="Index Visualisation",
            metadata={
                "gradient": True,
                "gradientValues": gradient_values,
            },
            message="Object Indexes",
            object_ids=selected_object_ids,
        )

        automate_context.mark_run_success(
            f"Added comment to {real_number_of_elements} random objects."
        )

    # set the automation context view, to the original model / version view
    automate_context.set_context_view()
