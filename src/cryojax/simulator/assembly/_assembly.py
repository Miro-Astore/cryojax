"""
Abstraction of a biological assembly. This assembles a structure
by computing an Ensemble of subunits, parameterized by
some geometry.
"""

from __future__ import annotations

__all__ = ["Assembly"]

from abc import abstractmethod
from typing import Optional, Any
from jaxtyping import Array, Float
from functools import cached_property

import jax.numpy as jnp
import equinox as eqx

from ..specimen import SpecimenBase, Specimen, Ensemble, Conformation
from ..pose import Pose, EulerPose, MatrixPose

_Positions = Float[Array, "N 3"]
"""Type hint for array where each element is a subunit coordinate."""

_Rotations = Float[Array, "N 3 3"]
"""Type hint for array where each element is a subunit rotation."""


class Assembly(eqx.Module):
    """
    Abstraction of a biological assembly.

    This class acts just like a ``Specimen``, however
    it creates an assembly from a subunit.

    To subclass an ``Assembly``,
        1) Overwrite the ``Assembly.n_subunits``
           property
        2) Overwrite the ``Assembly.positions``
           and ``Assembly.rotations`` properties.

    Attributes
    ----------
    subunit :
        The subunit. It is important to set the the initial pose
        of the initial subunit here. The initial pose is not in
        the lab frame, it is in the center of mass frame of the assembly.
    pose :
        The center of mass pose of the helix.
    conformation :
        The conformation of each `subunit`.
    """

    subunit: SpecimenBase
    pose: Pose
    conformation: Optional[Conformation] = None

    def __init__(
        self,
        subunit: Ensemble,
        *,
        pose: Optional[Pose] = None,
        conformation: Optional[Conformation] = None,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.subunit = subunit
        self.pose = pose or EulerPose()
        self.conformation = None if conformation is None else conformation

    def __check_init__(self):
        if self.conformation is not None and not isinstance(
            self.subunit, Ensemble
        ):
            raise AttributeError(
                "conformation cannot be set if the subunit is not an Ensemble."
            )

    @cached_property
    @abstractmethod
    def n_subunits(self) -> int:
        """The number of subunits in the assembly"""
        raise NotImplementedError

    @cached_property
    @abstractmethod
    def positions(self) -> _Positions:
        """The positions of each subunit."""
        raise NotImplementedError

    @cached_property
    @abstractmethod
    def rotations(self) -> _Rotations:
        """The relative rotations between subunits."""
        raise NotImplementedError

    @cached_property
    def poses(self) -> Pose:
        """
        Draw the poses of the subunits in the lab frame, measured
        from the rotation relative to the first subunit.
        """
        # Transform the subunit positions by pose of the helix
        transformed_positions = (
            self.pose.rotate(self.positions) + self.pose.offset
        )
        # Transform the subunit rotations by the pose of the helix
        transformed_rotations = jnp.einsum(
            "nij,jk->nik", self.rotations, self.pose.rotation.as_matrix()
        )
        return MatrixPose(
            offset_x=transformed_positions[:, 0],
            offset_y=transformed_positions[:, 1],
            offset_z=transformed_positions[:, 2],
            matrix=transformed_rotations,
        )

    @cached_property
    def subunits(self) -> Ensemble:
        """Draw a realization of all of the subunits in the lab frame."""
        # Compute a list of subunits, configured at the correct conformations
        if isinstance(self.subunit, Specimen):
            where = lambda s: s.pose
            return eqx.tree_at(where, self.subunit, self.poses)
        elif isinstance(self.subunit, Ensemble):
            where = lambda s: (s.conformation, s.pose)
            return eqx.tree_at(
                where, self.subunit, (self.conformation, self.poses)
            )
        else:
            raise AttributeError("The subunit must be of type SpecimenLike.")
