from .custom_class import CustomClass1  # noqa: F401
from .custom_class2 import CustomClass2, ModelTransformer  # noqa: F401

# ModelTransformed is imported only to verify it will be not recognized as transformer itself

# CustomClass1 lower case, and CustomClass2 upper case of Settings section header
FORMATTERS = ["CustomClass2", "CustomClass1"]
