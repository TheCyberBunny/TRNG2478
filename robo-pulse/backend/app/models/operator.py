"""
Operator Model - Day 1 Phase B Challenge Answer Key
Not part of the original problem statement's expected entity list.
However, an operator model is implied by Mission.operator_id.
Follow the same pattern as the other models with a registry/find_by_id

"""

from typing import ClassVar

class Operator:
    registry: ClassVar[list["Operator"]] = []

    def __init__(self, operator_id: int, name: str, facility_id: int):
        self.id = operator_id
        self.name = name
        self.facility_id = facility_id
        Operator.registry.append(self)

    @classmethod
    def find_by_id(cls, operator_id: int) -> "Operator | None":
        for operator in cls.registry:
            if operator.id == operator_id:
                return operator
        return None

    def __repr__(self) -> str:
        return (f"Operator(id={self.id}, name={self.name!r}, "
                f"facility_id={self.facility_id})")