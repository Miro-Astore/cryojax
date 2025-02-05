"""
Base class for a cryojax distribution.
"""

from abc import abstractmethod
from typing import Any

from jaxtyping import PRNGKeyArray
from equinox import Module, AbstractVar

from ...simulator import AbstractPipeline
from ...typing import Real_, RealImage, Image


class AbstractDistribution(Module, strict=True):
    """
    An image formation model equipped with a probabilistic model.
    """

    pipeline: AbstractVar[AbstractPipeline]

    @abstractmethod
    def log_probability(self, observed: Image) -> Real_:
        """
        Evaluate the log-probability.

        Parameters
        ----------
        observed :
            The observed data in real or fourier space.
        """
        raise NotImplementedError

    @abstractmethod
    def sample(self, key: PRNGKeyArray, **kwargs: Any) -> RealImage:
        """
        Sample from the distribution.

        Parameters
        ----------
        key :
            The RNG key or key(s). See ``ImagePipeline.sample`` for
            documentation.
        """
        raise NotImplementedError
