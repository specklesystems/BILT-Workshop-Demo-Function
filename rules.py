from typing import List, Optional, Tuple, Callable, Dict, Any, cast, Union
from specklepy.objects.base import Base
from Levenshtein import ratio
import re

# We're going to define a set of rules that will allow us to filter and
# process parameters in our Speckle objects. These rules will be encapsulated
# in a class called `Rules`. We'll also define a set of rules specific to Revit
# objects in a class called `RevitRules`.


class Rules:
    """
    A collection of rules for processing properties in Speckle objects.

    Simple rules can be straightforwardly implemented as static methods that
    return boolean value to be used either as a filter or a condition.
    These can then be abstracted into returning lambda functions that  we can
    use in our main processing logic. By encapsulating these rules, we can easily
    extend or modify them in the future.
    """

    @staticmethod
    def try_get_display_value(
        speckle_object: Base,
    ) -> Optional[List[Base]]:
        """Try fetching the display value from a Speckle object.

        This method encapsulates the logic for attempting to retrieve the display value from a Speckle object.
        It returns a list containing the display values if found, otherwise it returns None.

        Args:
            speckle_object (Base): The Speckle object to extract the display value from.

        Returns:
            Optional[List[Base]]: A list containing the display values. If no display value is found,
                                   returns None.
        """
        # Attempt to get the display value from the speckle_object
        raw_display_value = getattr(speckle_object, "displayValue", None) or getattr(
            speckle_object, "@displayValue", None
        )

        # If no display value found, return None
        if raw_display_value is None:
            return None

        # If display value found, filter out non-Base objects
        display_values = [
            value for value in raw_display_value if isinstance(value, Base)
        ]

        # If no valid display values found, return None
        if not display_values:
            return None

        return display_values

    @staticmethod
    def is_displayable_object(speckle_object: Base) -> bool:
        """
        Determines if a given Speckle object is displayable.

        This method encapsulates the logic for determining if a Speckle object is displayable.
        It checks if the speckle_object has a display value and returns True if it does, otherwise it returns False.

        Args:
            speckle_object (Base): The Speckle object to check.

        Returns:
            bool: True if the object has a display value, False otherwise.
        """
        # Check if the speckle_object has a display value using the try_get_display_value method
        display_values = Rules.try_get_display_value(speckle_object)
        if display_values and getattr(speckle_object, "id", None) is not None:
            return True

        # Check for displayable state via definition, using try_get_display_value on the definition object
        definition = getattr(speckle_object, "definition", None)
        if definition:
            definition_display_values = Rules.try_get_display_value(definition)
            if (
                definition_display_values
                and getattr(definition, "id", None) is not None
            ):
                return True

        return False

    # Below are more speculatively defined rules that could be used in a traversal of flat list parsing

    @staticmethod
    def speckle_type_rule(
        desired_type: str,
    ) -> Callable[[Base], bool]:
        """
        Rule: Check if a parameter's speckle_type matches the desired type.
        """
        return lambda prop: getattr(prop, "speckle_type", None) == desired_type

    @staticmethod
    def is_speckle_type(prop: Base, desired_type: str) -> bool:
        """
        Rule: Check if a parameter's speckle_type matches the desired type.
        """
        return getattr(prop, "speckle_type", None) == desired_type

    @staticmethod
    def has_missing_value(prop: Dict[str, str]) -> bool:
        """
        Rule: Missing Value Check.

        The AEC industry often requires all parameters to have meaningful values.
        This rule checks if a parameter is missing its value, potentially indicating
        an oversight during data entry or transfer.
        """
        return not prop.get("value")

    @staticmethod
    def has_default_value(prop: Dict[str, str], default="Default") -> bool:
        """
        Rule: Default Value Check.

        Default values can sometimes creep into final datasets due to software defaults.
        This rule identifies parameters that still have their default values, helping
        to highlight areas where real, meaningful values need to be provided.
        """
        return prop.get("value") == default

    @staticmethod
    def parameter_exists(prop_name: str, parent_object: Dict[str, str]) -> bool:
        """
        Rule: Parameter Existence Check.

        For certain critical parameters, their mere presence (or lack thereof) is vital.
        This rule verifies if a specific parameter exists within an object, allowing
        teams to ensure that key data points are always present.
        """
        return prop_name in parent_object.get("parameters", {})


def get_displayable_objects(flat_list_of_objects: List[Base]) -> List[Base]:
    # modify this lambda from before to use the static method from the Checks class
    return [
        speckle_object
        for speckle_object in flat_list_of_objects
        if Rules.is_displayable_object(speckle_object)
        and getattr(speckle_object, "id", None)
    ]

    # and the same logic that could be modified to traverse a tree of objects


# Now we're going to define a set of rules that are specific to Revit objects.
class RevitRules:
    @staticmethod
    def has_parameter(speckle_object: Base, parameter_name: str) -> bool:
        """
        Checks if the speckle_object has a Revit parameter with the given name.

        This method checks if the speckle_object has a parameter with the specified name,
        considering the following cases:
        1. The parameter is a named property at the root object level.
        2. The parameter is stored as a key in the "parameters" dictionary.
        3. The parameter is stored as a nested dictionary within the "parameters" property,
           and the parameter name is stored as the value of the "name" property within each nested dictionary.

        If the parameter exists, it returns True; otherwise, it returns False.

        Args:
            speckle_object (Base): The Speckle object to check.
            parameter_name (str): The name of the parameter to check for.

        Returns:
            bool: True if the object has the parameter, False otherwise.
        """
        if hasattr(speckle_object, parameter_name):
            return True

        parameters = cast(Base, getattr(speckle_object, "parameters", None))

        if parameters is None:
            return False

        # the parameters object can function like a dict but isn't one.
        # convert a Base object to a dict
        parameters_dict = {}

        for parameter_key in parameters.get_dynamic_member_names():
            parameters_dict[parameter_key] = getattr(parameters, parameter_key, None)

        if parameter_name in parameters_dict:
            return True

        return any(
            getattr(param_value, "name", None) == parameter_name
            for param_value in parameters_dict.values()
        )

    @staticmethod
    def get_parameter_value(
        speckle_object: Base,
        parameter_name: str,
        default_value: Any = None,
    ) -> Any | None:
        """
        Retrieves the value of the specified Revit parameter from the speckle_object.

        This method checks if the speckle_object has a parameter with the specified name,
        considering the following cases:
        1. The parameter is a named property at the root object level.
        2. The parameter is stored as a key in the "parameters" dictionary.
        3. The parameter is stored as a nested dictionary within the "parameters" property,
           and the parameter name is stored as the value of the "name" property within each nested dictionary.

        If the parameter exists and its value is not None or the specified default_value, it returns the value.
        If the parameter does not exist or its value is None or the specified default_value, it returns None.

        Args:
            speckle_object (Base): The Speckle object to retrieve the parameter value from.
            parameter_name (str): The name of the parameter to retrieve the value for.
            default_value: The default value to compare against. If the parameter value matches this value,
                           it will be treated the same as None.

        Returns:
            The value of the parameter if it exists and is not None or the specified default_value, or None otherwise.
        """
        # Attempt to retrieve the parameter from the root object level
        value = getattr(speckle_object, parameter_name, None)
        if value not in [None, default_value]:
            return value

        # If the "parameters" attribute is a Base object, extract its dynamic members
        parameters = getattr(speckle_object, "parameters", None)
        if parameters is None:
            return None

        # Prepare a dictionary of parameter values from the dynamic members of the parameters attribute
        parameters_dict = {
            key: getattr(parameters, key)
            for key in parameters.get_dynamic_member_names()
        }

        # Search for a direct match or a nested match in the parameters dictionary
        param_value = parameters_dict.get(parameter_name)
        if param_value is not None:
            if isinstance(param_value, Base):
                # Extract the nested value from a Base object if available
                nested_value = getattr(param_value, "value", None)
                if nested_value not in [None, default_value]:
                    return nested_value
            elif param_value not in [None, default_value]:
                return param_value

        # Use a generator to find the first matching 'value' for shared parameters stored in Base objects
        return next(
            (
                getattr(p, "value", None)
                for p in parameters_dict.values()
                if isinstance(p, Base) and getattr(p, "name", None) == parameter_name
            ),
            None,
        )

    @staticmethod
    def is_parameter_value(
        speckle_object: Base, parameter_name: str, value_to_match: Any
    ) -> bool:
        """
        Checks if the value of the specified parameter matches the given value.

        Args:
            speckle_object (Base): The Speckle object to check.
            parameter_name (str): The name of the parameter to check.
            value_to_match (Any): The value to match against.

        Returns:
            bool: True if the parameter value matches the given value, False otherwise.
        """
        parameter_value = RevitRules.get_parameter_value(speckle_object, parameter_name)
        return parameter_value == value_to_match

    @staticmethod
    def is_like_parameter_value(
        speckle_object: Base,
        parameter_name: str,
        pattern: str,
        fuzzy: bool = False,
        threshold: float = 0.8,
    ) -> bool:
        """
        Checks if the value of the specified parameter matches the given pattern.

        Args:
            speckle_object (Base): The Speckle object to check.
            parameter_name (str): The name of the parameter to check.
            pattern (str): The pattern to match against.
            fuzzy (bool): If True, performs fuzzy matching using Levenshtein distance.
                          If False (default), performs exact pattern matching using regular expressions.
            threshold (float): The similarity threshold for fuzzy matching (default: 0.8).
                               Only applicable when fuzzy=True.

        Returns:
            bool: True if the parameter value matches the pattern (exact or fuzzy), False otherwise.
        """
        parameter_value = RevitRules.get_parameter_value(speckle_object, parameter_name)
        if parameter_value is None:
            return False

        if fuzzy:
            similarity = ratio(str(parameter_value), pattern)
            return similarity >= threshold
        else:
            return bool(re.match(pattern, str(parameter_value)))

    @staticmethod
    def is_parameter_value_greater_than(
        speckle_object: Base, parameter_name: str, threshold: Union[int, float]
    ) -> bool:
        """
        Checks if the value of the specified parameter is greater than the given threshold.

        Args:
            speckle_object (Base): The Speckle object to check.
            parameter_name (str): The name of the parameter to check.
            threshold (Union[int, float]): The threshold value to compare against.

        Returns:
            bool: True if the parameter value is greater than the threshold, False otherwise.
        """
        parameter_value = RevitRules.get_parameter_value(speckle_object, parameter_name)
        if parameter_value is None:
            return False
        if not isinstance(parameter_value, (int, float)):
            raise ValueError(
                f"Parameter value must be a number, got {type(parameter_value)}"
            )
        return parameter_value > threshold

    @staticmethod
    def is_parameter_value_less_than(
        speckle_object: Base, parameter_name: str, threshold: Union[int, float]
    ) -> bool:
        """
        Checks if the value of the specified parameter is less than the given threshold.

        Args:
            speckle_object (Base): The Speckle object to check.
            parameter_name (str): The name of the parameter to check.
            threshold (Union[int, float]): The threshold value to compare against.

        Returns:
            bool: True if the parameter value is less than the threshold, False otherwise.
        """
        parameter_value = RevitRules.get_parameter_value(speckle_object, parameter_name)
        if parameter_value is None:
            return False
        if not isinstance(parameter_value, (int, float)):
            raise ValueError(
                f"Parameter value must be a number, got {type(parameter_value)}"
            )
        return parameter_value < threshold

    @staticmethod
    def is_parameter_value_in_range(
        speckle_object: Base,
        parameter_name: str,
        min_value: Union[int, float],
        max_value: Union[int, float],
        inclusive: bool = True,
    ) -> bool:
        """
        Checks if the value of the specified parameter falls within the given range.

        Args:
            speckle_object (Base): The Speckle object to check.
            parameter_name (str): The name of the parameter to check.
            min_value (Union[int, float]): The minimum value of the range.
            max_value (Union[int, float]): The maximum value of the range.
            inclusive (bool): If True (default), the range is inclusive (min <= value <= max).
                              If False, the range is exclusive (min < value < max).

        Returns:
            bool: True if the parameter value falls within the range (inclusive), False otherwise.
        """
        parameter_value = RevitRules.get_parameter_value(speckle_object, parameter_name)
        if parameter_value is None:
            return False
        if not isinstance(parameter_value, (int, float)):
            raise ValueError(
                f"Parameter value must be a number, got {type(parameter_value)}"
            )

        return (
            min_value <= parameter_value <= max_value
            if inclusive
            else min_value < parameter_value < max_value
        )

    @staticmethod
    def is_parameter_value_in_list(
        speckle_object: Base, parameter_name: str, value_list: List[Any]
    ) -> bool:
        """
        Checks if the value of the specified parameter is present in the given list of values.

        Args:
            speckle_object (Base): The Speckle object to check.
            parameter_name (str): The name of the parameter to check.
            value_list (List[Any]): The list of values to check against.

        Returns:
            bool: True if the parameter value is found in the list, False otherwise.
        """
        parameter_value = RevitRules.get_parameter_value(speckle_object, parameter_name)
        return parameter_value in value_list

    @staticmethod
    def is_parameter_value_true(speckle_object: Base, parameter_name: str) -> bool:
        """
        Checks if the value of the specified parameter is True.

        Args:
            speckle_object (Base): The Speckle object to check.
            parameter_name (str): The name of the parameter to check.

        Returns:
            bool: True if the parameter value is True, False otherwise.
        """
        parameter_value = RevitRules.get_parameter_value(speckle_object, parameter_name)
        return parameter_value is True

    @staticmethod
    def is_parameter_value_false(speckle_object: Base, parameter_name: str) -> bool:
        """
        Checks if the value of the specified parameter is False.

        Args:
            speckle_object (Base): The Speckle object to check.
            parameter_name (str): The name of the parameter to check.

        Returns:
            bool: True if the parameter value is False, False otherwise.
        """
        parameter_value = RevitRules.get_parameter_value(speckle_object, parameter_name)
        return parameter_value is False

    @staticmethod
    def has_category(speckle_object: Base) -> bool:
        """
        Checks if the speckle_object has a 'category' parameter.

        This method checks if the speckle_object has a 'category' parameter.
        If the 'category' parameter exists, it returns True; otherwise, it returns False.

        Args:
            speckle_object (Base): The Speckle object to check.

        Returns:
            bool: True if the object has the 'category' parameter, False otherwise.
        """
        return RevitRules.has_parameter(speckle_object, "category")

    @staticmethod
    def is_category(speckle_object: Base, category_input: str) -> bool:
        """
        Checks if the value of the 'category' property matches the given input.

        This method checks if the 'category' property of the speckle_object
        matches the given category_input. If they match, it returns True;
        otherwise, it returns False.

        Args:
            speckle_object (Base): The Speckle object to check.
            category_input (str): The category value to compare against.

        Returns:
            bool: True if the 'category' property matches the input, False otherwise.
        """
        category_value = RevitRules.get_parameter_value(speckle_object, "category")
        return category_value == category_input

    @staticmethod
    def get_category_value(speckle_object: Base) -> str:
        """
        Retrieves the value of the 'category' parameter from the speckle_object.

        This method retrieves the value of the 'category' parameter from the speckle_object.
        If the 'category' parameter exists and its value is not None, it returns the value.
        If the 'category' parameter does not exist or its value is None, it returns an empty string.

        Args:
            speckle_object (Base): The Speckle object to retrieve the 'category' parameter value from.

        Returns:
            str: The value of the 'category' parameter if it exists and is not None, or an empty string otherwise.
        """
        return RevitRules.get_parameter_value(speckle_object, "category")


def filter_objects_by_category(
    speckle_objects: List[Base], category_input: str
) -> Tuple[List[Base], List[Base]]:
    """
    Filters objects by category value and test.

    This function takes a list of Speckle objects, filters out the objects
    with a matching category value and satisfies the test, and returns
    both the matching and non-matching objects.

    Args:
        speckle_objects (List[Base]): The list of Speckle objects to filter.
        category_input (str): The category value to match against.

    Returns:
        Tuple[List[Base], List[Base]]: A tuple containing two lists:
                                        - The first list contains objects with matching category and test.
                                        - The second list contains objects without matching category or test.
    """
    matching_objects = []
    non_matching_objects = []

    for speckle_object in speckle_objects:
        if RevitRules.is_category(speckle_object, category_input):
            matching_objects.append(speckle_object)
        else:
            non_matching_objects.append(speckle_object)

    return matching_objects, non_matching_objects
