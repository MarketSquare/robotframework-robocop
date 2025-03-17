"""SonarQube own attributes used in their reporting and dashboards."""

from dataclasses import dataclass
from enum import Enum


class SonarQubeIssueType(Enum):
    BUG = "BUG"
    VULNERABILITY = "VULNERABILITY"
    CODE_SMELL = "CODE_SMELL"


class CleanCodeAttribute(Enum):
    # Consistency
    FORMATTED = "FORMATTED"  # The code presentation is systematic and regular
    CONVENTIONAL = "CONVENTIONAL"  # Faced with equally good options, the code adheres to a single choice across
    # all instances
    IDENTIFIABLE = "IDENTIFIABLE"  # The names follow a regular structure based on language conventions
    # Intentionality
    CLEAR = "CLEAR"  # The code is self-explanatory, transparently communicating its functionality
    LOGICAL = "LOGICAL"  # The code has well-formed and sound instructions that work together
    COMPLETE = "COMPLETE"  # The code constructs are comprehensive and used adequately and thoroughly
    EFFICIENT = "EFFICIENT"  # The code uses resources without needless waste
    # Adaptability
    FOCUSED = "FOCUSED"  # The code has a single, narrow, and specific scope
    DISTINCT = "DISTINCT"  # The code procedures and data are unique and distinctive, without undue duplication
    MODULAR = "MODULAR"  # The code has been organized and distributed to emphasize the separation between its parts
    TESTED = "TESTED"  # The code has automated checks that provide confidence in the functionality
    # Responsibility
    LAWFUL = "LAWFUL"  # The code respects licensing and copyright regulation
    TRUSTWORTHY = "TRUSTWORTHY"  # The code abstains from revealing or hard-coding private information
    RESPECTFUL = "RESPECTFUL"  # The code refrains from using discriminatory and offensive language


@dataclass
class SonarQubeAttributes:
    clean_code: CleanCodeAttribute
    issue_type: SonarQubeIssueType
